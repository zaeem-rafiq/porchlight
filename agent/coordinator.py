"""Durable coordinator approval queue, authenticated choices, and silence ladder.

Production handlers explicitly queue decisions and await a coordinator menu reply.
The optional Strands hook below remains available to agents configured with it;
it is not invoked artificially by the production path. Medical cases notify
immediately; other queued work batches within a 15-minute window.
"""

from __future__ import annotations

import ast
import json
import os
import secrets
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strands import tool
from strands.hooks import HookProvider
from strands.hooks.events import AfterToolCallEvent, BeforeToolCallEvent

PING_WINDOW_MIN = 15
SILENCE_MIN = 20

# Durable gate queue lives in porchlight.gate_pending; approvals use conditional claims.
# The module-level list below is only a same-process convenience mirror.
pending: list[dict] = []


def pending_open(sb, event_id: str) -> list[dict]:
    q = sb.table("gate_pending").select("*").eq("event_id", event_id).eq("status", "open")
    if hasattr(q, "order"):
        q = q.order("created_at")
    return q.execute().data


def decision_input(decision: dict) -> dict:
    """Read new JSON records and legacy literal-dict queue records."""
    raw = decision.get("input", "{}")
    if isinstance(raw, dict):
        return raw
    try:
        value = json.loads(raw)
    except (ValueError, TypeError):
        try:
            value = ast.literal_eval(raw)
        except (ValueError, SyntaxError, TypeError):
            return {}
    return value if isinstance(value, dict) else {}


def pending_add(sb, event_id: str, tool_name: str, tool_input: dict) -> None:
    for item in pending_open(sb, event_id):
        previous = decision_input(item)
        if item["tool"] == tool_name and previous.get("resident_id", previous.get("resident_name")) == tool_input.get("resident_id", tool_input.get("resident_name")):
            return
    sb.table("gate_pending").insert({
        "event_id": event_id, "tool": tool_name,
        "input": json.dumps(tool_input or {}, ensure_ascii=False)}).execute()


def audit(sb, event_id: str, action: str, detail: str = "") -> None:
    sb.table("audit_log").insert({
        "event_id": event_id, "actor": "coordinator", "action": action,
        "detail": detail}).execute()


class CoordinatorGate(HookProvider):
    def __init__(self, sb, event_id: str):
        self.sb = sb
        self.event_id = event_id

    def register_hooks(self, registry, **kwargs) -> None:
        registry.add_callback(BeforeToolCallEvent, self.on_before_tool_call)
        registry.add_callback(AfterToolCallEvent, self.on_after_tool_call)

    def on_before_tool_call(self, event: BeforeToolCallEvent) -> None:
        if event.tool_name in ("escalate_medical", "mark_unreachable_tier1",
                               "dispatch_without_volunteer"):
            pending_add(self.sb, self.event_id, event.tool_name, dict(event.tool_input or {}))
            pending.append({"tool": event.tool_name, "input": dict(event.tool_input or {})})
            audit(self.sb, self.event_id, f"gate_hold:{event.tool_name}",
                  str(event.tool_input or {})[:200])
            event.interrupt("coordinator-decision")

    def on_after_tool_call(self, event: AfterToolCallEvent) -> None:
        audit(self.sb, self.event_id, f"tool:{event.tool_name}", "completed")


@tool
def escalate_medical(resident_name: str, quote: str) -> str:
    """Hold a medical case for the coordinator (gate intercepts before execution)."""
    return f"escalated {resident_name}: {quote}"


@tool
def mark_unreachable_tier1(resident_name: str) -> str:
    """Hold a tier-1 unreachable flag for the coordinator (gate intercepts)."""
    return f"flagged unreachable {resident_name}"


@tool
def dispatch_without_volunteer(resident_name: str, resource: str) -> str:
    """Hold a volunteer-less dispatch for the coordinator (gate intercepts)."""
    return f"dispatch without volunteer for {resident_name} to {resource}"


def open_decisions(sb, event_id: str) -> dict:
    contacts = sb.table("contacts").select("*, residents(name)").eq("event_id", event_id).execute().data
    counts: dict[str, int] = {}
    for c in contacts:
        counts[c.get("status", "?")] = counts.get(c.get("status", "?"), 0) + 1
    medical = [c for c in contacts if c.get("status") == "medical"]
    unreach = [c for c in contacts if c.get("status") == "unreachable"]
    return {"counts": counts, "medical": medical, "unreachable": unreach,
            "total": len(contacts)}


def compose_ping(sb, event_id: str, hazard_headline: str, queue=None) -> str:
    queue = pending_open(sb, event_id) if queue is None else queue
    d = open_decisions(sb, event_id)
    lines = [f"[Coordinator] Porchlight - {hazard_headline}: {d['counts'].get('ok', 0)} OK out of {d['total']} checked."]
    options = []
    for i, decision in enumerate(queue[:3], 1):
        data = decision_input(decision)
        name = data.get("resident_name", "resident")
        action = "contact emergency contact for" if decision["tool"] == "mark_unreachable_tier1" else "ask volunteer to check on"
        options.append(f"{i} {action} {name}")
    options.append(f"{len(queue[:3]) + 1} I'll handle these cases")
    lines.append("Reply COORD " + " / COORD ".join(options))
    return " ".join(lines)


def send_ping(sb, event_id: str, text: str, decision_ids=None) -> dict:
    from agent.outreach import send_one

    owner = os.environ.get("OWNER_PHONE", "").strip()
    menu_token = secrets.token_hex(4)
    text = text.replace("COORD ", f"COORD {menu_token} ")
    text = text.replace("[Coordinator] ", f"[Coordinator] Menu code {menu_token}. ", 1)
    sid, channel = send_one(sb, owner, "telegram", text, owner)
    if channel == "failed":
        audit(sb, event_id, "coordinator_ping_failed")
        return {"channel": channel, "mid": 0}
    ids = decision_ids if decision_ids is not None else [x["id"] for x in pending_open(sb, event_id)[:3]]
    audit(sb, event_id, "coordinator_ping", json.dumps({"sid": sid, "decision_ids": ids, "menu_token": menu_token, "text": text}))
    return {"channel": channel, "mid": sid, "menu_token": menu_token}


def maybe_ping(sb, event_id: str, hazard_headline: str, now_min: float = 0, force=False) -> dict | None:
    queue = pending_open(sb, event_id)
    if not queue:
        return None
    pings = sb.table("audit_log").select("created_at").eq("event_id", event_id).eq(
        "action", "coordinator_ping").order("created_at", desc=True).execute().data
    if pings and not force:
        last = datetime.fromisoformat(pings[0]["created_at"].replace("Z", "+00:00"))
        if (datetime.now(timezone.utc) - last).total_seconds() / 60 < PING_WINDOW_MIN:
            return {"outcome": "batched", "pending": len(queue)}
    out = send_ping(sb, event_id, compose_ping(sb, event_id, hazard_headline, queue),
                    [x["id"] for x in queue[:3]])
    return {"outcome": "failed" if out["channel"] == "failed" else "pinged", "pending": len(queue), **out}


def handle_coordinator_reply(sb, event_id: str, digit: str) -> dict:
    from agent.dispatch import ask_volunteer
    from agent.models import Dispatch

    pings = sb.table("audit_log").select("detail").eq("event_id", event_id).eq(
        "action", "coordinator_ping").order("created_at", desc=True).limit(1).execute().data
    try:
        menu = json.loads(pings[0]["detail"])
        token, number = digit.strip().split()
        if not menu.get("menu_token") or not secrets.compare_digest(token, menu["menu_token"]):
            return {"outcome": "ignored", "reason": "stale or missing menu code"}
        ids = menu["decision_ids"]
        idx = int(number) - 1
    except (ValueError, TypeError, KeyError, IndexError):
        return {"outcome": "ignored", "reason": "reply with the current menu code and number"}
    if idx < 0 or idx > len(ids):
        return {"outcome": "ignored", "reason": "no such option"}
    if idx == len(ids):
        for decision_id in ids:
            sb.table("gate_pending").update({"status": "human_handling"}).eq(
                "event_id", event_id).eq("id", decision_id).eq("status", "open").execute()
        audit(sb, event_id, "coordinator_handling", json.dumps(ids))
        return {"outcome": "human_handling"}
    rows = sb.table("gate_pending").update({"status": "processing"}).eq(
        "id", ids[idx]).eq("event_id", event_id).eq("status", "open").execute().data
    if not rows:
        return {"outcome": "ignored", "reason": "decision already handled"}
    decision = rows[0]
    data = decision_input(decision)
    try:
        residents = sb.table("residents").select("*").eq("id", data.get("resident_id", "")).execute().data
        if not residents:
            raise ValueError("decision has no valid resident")
        resident = residents[0]
        if resident.get("opted_out"):
            raise ValueError("resident opted out")
        if decision["tool"] == "mark_unreachable_tier1":
            from agent.outreach import send_one
            owner = os.environ.get("OWNER_PHONE", "").strip()
            sid, channel = send_one(sb, resident["emergency_contact"], "telegram",
                f"Porchlight: please check on {resident['name']}; we could not reach them after two check-ins.", owner)
            result = {"outcome": "contacted" if channel != "failed" else "failed", "channel": channel, "sid": sid}
        else:
            resources = sb.table("resources").select("*").eq("kind", "cooling_center").order("name").execute().data
            resource = resources[0] if resources and data.get("need") in ("cooling", "transport") else {}
            plan = Dispatch(resident_id=resident["id"], resident_name=resident["name"],
                            resource_id=resource.get("id", ""), resource_name=resource.get("name", ""))
            result = ask_volunteer(sb, plan, event_id, os.environ.get("OWNER_PHONE", "").strip())
        if result["outcome"] not in ("asked", "contacted", "already_pending"):
            sb.table("gate_pending").update({"status": "open"}).eq("id", decision["id"]).execute()
            if result["outcome"] == "no_volunteer":
                result["coordinator_alert"] = maybe_ping(sb, event_id,
                    "No available volunteer; please handle this case", force=True)
            return {"outcome": "needs_coordinator", "reason": result["outcome"], "dispatch": result}
    except Exception:
        sb.table("gate_pending").update({"status": "open"}).eq("id", decision["id"]).execute()
        raise
    sb.table("gate_pending").update({"status": "approved"}).eq("id", decision["id"]).execute()
    pending.clear()
    audit(sb, event_id, f"coordinator_approved:{decision['tool']}", json.dumps(data))
    return {"outcome": "approved", "decision": {"tool": decision["tool"], "input": data}, "dispatch": result}


def silence_check(sb, event_id: str, contact: dict, age_min: float,
                  limit_min: float = SILENCE_MIN) -> dict | None:
    """Escalate once after actual unanswered medical age; never call 911."""
    from agent.outreach import send_one

    if contact.get("status") != "medical" or age_min < limit_min:
        return None
    gates = sb.table("gate_pending").select("*").eq("event_id", event_id).execute().data
    if any(decision_input(g).get("resident_id") == contact["resident_id"] and
           g["status"] == "human_handling" for g in gates):
        return None
    accepted = sb.table("dispatches").select("id").eq("event_id", event_id).eq(
        "resident_id", contact["resident_id"]).eq("status", "accepted").execute().data
    if accepted:
        return None
    reason = "medical silence past ladder"
    prior = sb.table("escalations").select("id").eq("event_id", event_id).eq(
        "resident_id", contact["resident_id"]).eq("reason", reason).execute().data
    if prior:
        return None
    resident = sb.table("residents").select("*").eq("id", contact["resident_id"]).execute().data[0]
    if resident.get("opted_out"):
        return None
    # The unique event/resident/reason index makes this reservation atomic across workers.
    try:
        rows = sb.table("escalations").insert({"event_id": event_id, "resident_id": resident["id"],
            "reason": reason, "status": "sending"}).execute().data
    except Exception as exc:
        if getattr(exc, "code", None) == "23505":
            return None
        raise
    escalation_id = rows[0]["id"]
    body = (f"Porchlight: please check on {resident['name']}; "
            "if you can't reach them, call 911.")
    try:
        sid, channel = send_one(sb, resident["emergency_contact"], "telegram", body,
                               os.environ.get("OWNER_PHONE", "").strip())
    except Exception:
        sb.table("escalations").update({"status": "failed"}).eq("id", escalation_id).execute()
        raise
    sb.table("escalations").update({"status": "failed" if channel == "failed" else "open"}).eq(
        "id", escalation_id).execute()
    audit(sb, event_id, f"silence_ladder {channel}", f"{resident['name']} sid={sid}")
    return {"channel": channel, "sid": sid, "resident": resident["name"]}


def create_calendar_event(title: str, description: str) -> str:
    return "calendar=skipped (not implemented)"
