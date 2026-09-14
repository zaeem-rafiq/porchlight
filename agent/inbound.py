"""Inbound handling (P-03): routing, STOP/HELP, triage, retry ladder.

One ResidentAgent per resident (agents-as-tools, asyncio; session_id
f"{event_id}:{resident_id}") holds the roster row and history. The same
handle_inbound serves the Telegram webhook, the poll loop, and the console
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


def _safe_audit(sb, event_id: str, actor: str, action: str, detail: str = "") -> None:
    try:
        sb.table("audit_log").insert({
            "event_id": event_id, "actor": actor,
            "action": action, "detail": detail}).execute()
    except Exception:
        pass


def handle_inbound(from_phone: str, to_number: str, body: str, event_id: str) -> dict:
    """Validate and route a reply; operational failures surface to the caller."""
    from agent.safety import parse_allowlist

    from dotenv import load_dotenv

    load_dotenv()
    allowlist = parse_allowlist(os.environ.get("PHONE_ALLOWLIST", ""))
    bot_user = os.environ.get("TELEGRAM_BOT_USERNAME", "").lower().lstrip("@")
    number_b = os.environ.get("TWILIO_NUMBER_B", "").strip().lower()
    valid_channels = {
        "telegram", "bot", "simulated", "sim", "console", "coordinator", "coord", "",
    }
    if bot_user:
        valid_channels.add(bot_user)
        valid_channels.add("@" + bot_user)
    if number_b:
        valid_channels.add(number_b)

    if not all(isinstance(value, str) for value in (from_phone, to_number, body, event_id)):
        return {"outcome": "dropped", "reason": "invalid_payload"}
    now = datetime.now(timezone.utc).isoformat()
    text = body.strip()

    if from_phone not in allowlist:
        return {"outcome": "dropped", "reason": "not_allowlisted"}
    if to_number and to_number.strip().lower() not in valid_channels:
        return {"outcome": "dropped", "reason": "wrong_channel"}

    sb = _sb()
    upper = text.upper()
    owner = os.environ.get("OWNER_PHONE", "").strip()
    from agent import coordinator as coord

    explicit_coord = upper.startswith(("COORD ", "/COORD ")) or to_number.strip().lower() in ("coordinator", "coord")
    if explicit_coord:
        if from_phone != owner:
            return {"outcome": "dropped", "reason": "not_coordinator"}
        cmd = text.split(" ", 1)[1].strip() if " " in text else text
        return coord.handle_coordinator_reply(sb, event_id, cmd)
    if upper.split()[:1] in (["Y"], ["N"]):
        from agent.dispatch import volunteer_reply
        return volunteer_reply(sb, event_id, from_phone, text)

    residents = sb.table("residents").select("*").eq("phone", from_phone).execute().data
    if not residents:
        return {"outcome": "dropped", "reason": "unknown_resident"}
    resident = residents[0]
    if upper == "STOP":
        sb.table("residents").update({"opted_out": True}).eq("id", resident["id"]).execute()
        sb.table("contacts").update({"status": "opted_out"}).eq(
            "event_id", event_id).eq("resident_id", resident["id"]).execute()
        _safe_audit(sb, event_id, "inbound", "opt_out", resident["name"])
        return {"outcome": "opted_out", "resident": resident["name"]}
    if upper == "HELP":
        send_help(from_phone)
        return {"outcome": "help_sent", "resident": resident["name"]}
    if upper in ("START", "UNSTOP", "YES"):
        sb.table("residents").update({"opted_out": False}).eq("id", resident["id"]).execute()
        _safe_audit(sb, event_id, "inbound", "opt_in", resident["name"])
        return {"outcome": "opted_in", "resident": resident["name"]}
    if resident.get("opted_out"):
        return {"outcome": "dropped", "reason": "opted_out"}

    agent = ResidentAgent(event_id, resident)
    result, used_model = agent.triage(text)
    sb.table("contacts").update({
        "status": result.status, "last_inbound": now}).eq(
        "event_id", event_id).eq("resident_id", resident["id"]).execute()
    _safe_audit(sb, event_id, "inbound", f"triage:{result.status}",
                f"{resident['name']} need={result.need} quote={result.quote[:80]}")

    notification = None
    if result.status in ("medical", "needs_help", "unclear"):
        coord.pending_add(sb, event_id, "escalate_medical" if result.status == "medical" else "dispatch_help",
                          {"resident_id": resident["id"], "resident_name": resident["name"],
                           "need": result.need, "quote": result.quote})
        ev_rows = sb.table("hazard_events").select("headline").eq("id", event_id).execute().data
        headline = ev_rows[0]["headline"] if ev_rows else "Extreme Weather"
        notification = coord.maybe_ping(sb, event_id, headline, force=result.status == "medical")

    return {"outcome": "triaged", "resident": resident["name"],
            "status": result.status, "need": result.need,
            "quote": result.quote, "used_model": used_model, "coordinator_alert": notification}


def send_help(to_phone: str) -> None:
    from agent.outreach import send_one

    owner = os.environ.get("OWNER_PHONE", "").strip()
    text = ("Porchlight Neighbors: reply 1 if OK, 2 for help. "
            "We check on you in extreme weather. Reply STOP to opt out.")
    _, channel = send_one(None, to_phone, "telegram", text, owner)
    if channel == "failed":
        raise RuntimeError("help message was not delivered")
