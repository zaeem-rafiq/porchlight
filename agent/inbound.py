"""Inbound handling (P-03): routing, STOP/HELP, triage, retry ladder.

One ResidentAgent per resident (agents-as-tools, asyncio; session_id
f"{event_id}:{resident_id}") holds the roster row and history. The same
handle_inbound serves the Twilio webhook, the poll loop, and the console
/simulated-inbound path (shared secret checked by the caller, P-07).
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone

from agent.triage import triage_reply

RESEND_AFTER_MIN = 45
UNREACHABLE_AFTER_MIN = 90


class ResidentAgent:
    def __init__(self, event_id: str, resident: dict):
        self.session_id = f"{event_id}:{resident['id']}"
        self.resident = resident
        self.history: list[dict] = []

    def triage(self, body: str):
        result, used_model = triage_reply(body, self.resident)
        self.history.append({"in": body, "status": result.status,
                             "need": result.need, "model": used_model})
        return result, used_model


async def triage_many(agents: list[ResidentAgent], bodies: list[str]):
    return await asyncio.gather(*[
        asyncio.to_thread(a.triage, b) for a, b in zip(agents, bodies)
    ])


def _sb():
    from dotenv import load_dotenv
    from supabase import create_client

    load_dotenv()
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    return create_client(url, key).schema("porchlight")


def ladder_action(contact: dict, now_min: float, resend_after: float = RESEND_AFTER_MIN,
                  unreachable_after: float = UNREACHABLE_AFTER_MIN) -> str | None:
    """Pure retry-ladder step. Returns 'resend', 'flag_unreachable', or None."""
    if contact.get("status") not in ("sent", "resent"):
        return None
    age = now_min - contact.get("_sent_min", 0)
    attempts = contact.get("attempts", 1)
    if attempts == 1 and age >= resend_after:
        return "resend"
    if attempts >= 2 and age >= unreachable_after:
        return "flag_unreachable"
    return None


def handle_inbound(from_phone: str, to_number: str, body: str, event_id: str) -> dict:
    """Route one inbound SMS. Returns an outcome dict (never raises on user input)."""
    from agent.safety import parse_allowlist

    from dotenv import load_dotenv

    load_dotenv()
    allowlist = parse_allowlist(os.environ.get("PHONE_ALLOWLIST", ""))
    number_b = os.environ.get("TWILIO_NUMBER_B", "").strip()
    sb = _sb()
    now = datetime.now(timezone.utc).isoformat()
    text = body.strip()

    if from_phone not in allowlist:
        sb.table("audit_log").insert({
            "event_id": event_id, "actor": "inbound",
            "action": "dropped_not_allowlisted", "detail": f"to={to_number}"}).execute()
        return {"outcome": "dropped", "reason": "not_allowlisted"}
    if to_number != number_b:
        sb.table("audit_log").insert({
            "event_id": event_id, "actor": "inbound",
            "action": "dropped_wrong_channel", "detail": f"to={to_number}"}).execute()
        return {"outcome": "dropped", "reason": "wrong_channel"}

    residents = sb.table("residents").select("*").eq("phone", from_phone).execute().data
    if not residents:
        return {"outcome": "dropped", "reason": "unknown_resident"}
    resident = residents[0]

    upper = text.upper()
    if upper == "STOP":
        sb.table("residents").update({"opted_out": True}).eq("id", resident["id"]).execute()
        sb.table("contacts").update({"status": "opted_out"}).eq(
            "event_id", event_id).eq("resident_id", resident["id"]).execute()
        sb.table("audit_log").insert({
            "event_id": event_id, "actor": "inbound", "action": "opt_out",
            "detail": resident["name"]}).execute()
        return {"outcome": "opted_out", "resident": resident["name"]}
    if upper == "HELP":
        send_help(from_phone)
        return {"outcome": "help_sent", "resident": resident["name"]}

    from agent import coordinator as coord

    owner = os.environ.get("OWNER_PHONE", "").strip()
    if from_phone == owner:
        cmd = None
        if upper.startswith("COORD "):
            cmd = text[6:].strip()
        elif to_number != number_b:
            cmd = text
        elif text in ("1", "2", "3") and coord.pending_open(sb, event_id):
            mine = sb.table("contacts").select("status").eq(
                "event_id", event_id).eq("resident_id", resident["id"]).execute().data
            if mine and mine[0]["status"] not in ("sent", "pending", "resent"):
                cmd = text
        if cmd is not None:
            out = coord.handle_coordinator_reply(sb, event_id, cmd)
            out["resident"] = resident["name"]
            return out

    agent = ResidentAgent(event_id, resident)
    result, used_model = agent.triage(text)
    sb.table("contacts").update({
        "status": result.status, "last_inbound": now}).eq(
        "event_id", event_id).eq("resident_id", resident["id"]).execute()
    sb.table("audit_log").insert({
        "event_id": event_id, "actor": "inbound", "action": f"triage:{result.status}",
        "detail": f"{resident['name']} need={result.need} quote={result.quote[:80]}"}).execute()
    return {"outcome": "triaged", "resident": resident["name"],
            "status": result.status, "need": result.need,
            "quote": result.quote, "used_model": used_model}


def send_help(to_phone: str) -> None:
    owner = os.environ.get("OWNER_PHONE", "").strip()
    text = ("Porchlight Neighbors: reply 1 if OK, 2 for help. "
            "We check on you in extreme weather. Reply STOP to opt out.")
    if to_phone == owner:
        from twilio.rest import Client

        Client(os.environ.get("TWILIO_ACCOUNT_SID", ""),
               os.environ.get("TWILIO_AUTH_TOKEN", "")).messages.create(
            body=text, from_=os.environ.get("TWILIO_NUMBER_B", "").strip(), to=to_phone)
