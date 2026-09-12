"""Coordinator gate (P-04): one consolidated ping, silence ladder, audit.

Gate tools (escalate_medical, mark_unreachable_tier1, dispatch_without_volunteer)
are Strands @tools whose BeforeToolCallEvent hook records the decision and
interrupts with "coordinator-decision" instead of executing. The coordinator
gets ONE ping per 15-minute window (via Telegram with [Coordinator] prefix
per ADR-003 and ADR-004) and replies 1/2/3
(optionally COORD-prefixed). Bare digits route here only when a ping is
pending and the owner's resident contact is already triaged.

Silence ladder: medical flag unanswered 20 min -> text the emergency contact
("please check on them; if you can't reach them, call 911"). The agent never
calls 911: no such tool exists anywhere in this codebase.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strands import tool
from strands.hooks import HookProvider
from strands.hooks.events import AfterToolCallEvent, BeforeToolCallEvent

PING_WINDOW_MIN = 15
SILENCE_MIN = 20

# Durable gate queue lives in porchlight.gate_pending (multi-process safe).
# The module-level list below is only a same-process convenience mirror.
pending: list[dict] = []


def pending_open(sb, event_id: str) -> list[dict]:
    q = sb.table("gate_pending").select("*").eq("event_id", event_id).eq("status", "open")
    if hasattr(q, "order"):
        q = q.order("created_at")
    return q.execute().data


def pending_add(sb, event_id: str, tool_name: str, tool_input: dict) -> None:
    sb.table("gate_pending").insert({
        "event_id": event_id, "tool": tool_name,
        "input": str(tool_input or {})[:500]}).execute()


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


def compose_ping(sb, event_id: str, hazard_headline: str) -> str:
    d = open_decisions(sb, event_id)
    ok = d["counts"].get("ok", 0)
    lines = [f"[Coordinator] Porchlight - {hazard_headline}: {ok} OK out of {d['total']} checked."]
    options: list[str] = []
    for i, m in enumerate(d["medical"][:3], start=1):
        name = (m.get("residents") or {}).get("name", "?")
        lines.append(f"Medical-sounding ({name}).")
        options.append(f"{i} send volunteer to {name.split()[-1]}")
    for m in d["unreachable"][:2]:
        name = (m.get("residents") or {}).get("name", "?")
        lines.append(f"Unreachable after 2 tries ({name}).")
        options.append(f"{len(options) + 1} call {name.split()[-1]} contact")
    options.append(f"{len(options) + 1} I'll handle it")
    lines.append("Reply " + " / ".join(options))
    return " ".join(lines)


def send_ping(sb, event_id: str, text: str) -> dict:
    owner = os.environ.get("OWNER_PHONE", "").strip()
    from agent.telegram import owner_chat_id, send_message

    chat = owner_chat_id()
    try:
        mid = send_message(chat, text) if chat else 0
    except Exception as exc:
        sys.stderr.write(f"telegram_send_error in send_ping: {exc}\n")
        mid = 0
    audit(sb, event_id, "coordinator_ping", f"mid={mid}")
    return {"channel": "telegram", "mid": mid}


def maybe_ping(sb, event_id: str, hazard_headline: str, now_min: float) -> dict | None:
    from datetime import datetime

    queue = pending_open(sb, event_id)
    if not queue:
        return None
    pings = sb.table("audit_log").select("created_at").eq("event_id", event_id).eq(
        "action", "coordinator_ping").order("created_at", desc=True).execute().data
    if pings:
        last = datetime.fromisoformat(pings[0]["created_at"])
        age_min = (datetime.now(timezone.utc) - last).total_seconds() / 60
        if age_min < PING_WINDOW_MIN:
            return {"outcome": "batched", "pending": len(queue)}
    text = compose_ping(sb, event_id, hazard_headline)
    out = send_ping(sb, event_id, text)
    return {"outcome": "pinged", "pending": len(queue), **out}


def handle_coordinator_reply(sb, event_id: str, digit: str) -> dict:
    queue = pending_open(sb, event_id)
    idx = {"1": 0, "2": 1, "3": 2}.get(digit.strip(), -1)
    if idx < 0 or idx >= len(queue):
        return {"outcome": "ignored", "reason": "no such option"}
    decision = queue[idx]
    sb.table("gate_pending").update({"status": "approved"}).eq("id", decision["id"]).execute()
    pending.clear()
    audit(sb, event_id, f"coordinator_approved:{decision['tool']}", str(decision["input"])[:200])
    return {"outcome": "approved",
            "decision": {"tool": decision["tool"], "input": decision["input"]}}


def silence_check(sb, event_id: str, contact: dict, age_min: float,
                  limit_min: float = SILENCE_MIN) -> dict | None:
    """Medical flag unanswered past the limit -> text emergency contact. Never 911."""
    if contact.get("status") != "medical" or age_min < limit_min:
        return None
    resident = sb.table("residents").select("*").eq("id", contact["resident_id"]).execute().data[0]
    ec = resident["emergency_contact"]
    owner = os.environ.get("OWNER_PHONE", "").strip()
    body = (f"Porchlight: please check on {resident['name']} ({resident.get('notes', '')[:60]}); "
            f"if you can't reach them, call 911.")
    if ec == owner:
        from agent.telegram import owner_chat_id, send_message

        chat = owner_chat_id()
        try:
            mid = send_message(chat, body) if chat else 0
        except Exception as exc:
            sys.stderr.write(f"telegram_send_error in silence_check: {exc}\n")
            mid = 0
        sid, channel = f"TG-{mid}", "telegram"
    else:
        sid, channel = f"SIM-EC-{abs(hash((ec, body))) % 10**8:08d}", "simulated"
    sb.table("escalations").insert({
        "event_id": event_id, "resident_id": resident["id"],
        "reason": "medical silence past ladder", "status": "open"}).execute()
    audit(sb, event_id, f"silence_ladder {channel}", f"{resident['name']} sid={sid}")
    return {"channel": channel, "sid": sid, "resident": resident["name"]}


def create_calendar_event(title: str, description: str) -> str:
    if not os.environ.get("GOOGLE_CALENDAR_REFRESH_TOKEN", ""):
        return "calendar=skipped (no token)"
    return "calendar=skipped (token present, P-07 wires the API)"
