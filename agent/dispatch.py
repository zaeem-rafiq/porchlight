"""Dispatcher (P-04): need -> resource/volunteer matching + dispatch rows.

For every needs_help/medical triage, match the need to a resource (nearest
open cooling center, or power/wellness guidance) and, for transport, to an
opted-in volunteer. Volunteer asks go out via Telegram (real only for the
owner; placeholders simulated). Y accepts the recorded request; calendar integration is not implemented.
"""

from __future__ import annotations

import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strands import tool

from agent.models import Dispatch


@tool
def match_resource(need: str, resident_name: str) -> str:
    """Match a triage need to a resource name or guidance text."""
    from agent.inbound import _sb

    sb = _sb()
    if need in ("cooling", "wellness_check"):
        centers = sb.table("resources").select("*").eq("kind", "cooling_center").execute().data
        if centers:
            c = centers[0]
            return f"{c['name']}, {c['address']} ({c['hours']})"
        return "nearest public cooling location; call coordinator for the address"
    if need == "power":
        return ("power guidance: check breaker, move medical devices to backup power, "
                "offer cooling-center transport")
    if need == "transport":
        return "volunteer transport (see volunteer match)"
    return "coordinator follow-up"


def propose_dispatch(resident: dict, triage, event_id: str) -> Dispatch:
    from strands import Agent
    from strands.models import BedrockModel

    agent = Agent(
        model=BedrockModel(model_id=os.environ.get("BEDROCK_MODEL_ID", ""),
                           region_name=os.environ.get("AWS_REGION", "") or None),
        tools=[match_resource],
        structured_output_model=Dispatch,
        system_prompt=(
            "You dispatch help for vulnerable neighbors. Match the need to a resource, "
            "keep the volunteer ask to one sentence with place and time, reply with the "
            "Dispatch structure only."
        ),
    )
    result = agent(
        f"Propose dispatch for {resident.get('name')} (need={triage.need}, "
        f"quote={triage.quote!r}): {resident.get('notes', '')}")
    dispatch: Dispatch = result.structured_output
    if not dispatch.resident_name:
        dispatch.resident_name = resident.get("name", "")
    return dispatch


def ask_volunteer(sb, dispatch: Dispatch, event_id: str, owner_phone: str) -> dict:
    from agent.outreach import send_one

    if not dispatch.resident_id:
        raise ValueError("dispatch requires a resident ID")
    existing = sb.table("dispatches").select("*").eq("event_id", event_id).eq(
        "resident_id", dispatch.resident_id).execute().data
    for row in existing:
        if row["status"] in ("sending", "proposed", "accepted"):
            return {"outcome": "already_pending", "dispatch_id": row["id"]}
    declined = {row["volunteer_id"] for row in existing if row["status"] == "declined"}
    vols = sb.table("volunteers").select("*").eq("opted_in", True).order("name").execute().data
    # The owner represents the real volunteer in this synthetic demonstration.
    vols.sort(key=lambda v: v["phone"] != owner_phone)
    active = sb.table("dispatches").select("volunteer_id,status").execute().data
    busy = {row["volunteer_id"] for row in active if row["status"] in ("sending", "proposed", "accepted")}
    destination = f" and arrange a visit to {dispatch.resource_name} (confirm opening hours first)" if dispatch.resource_name else ""
    request = f"Porchlight: can you check on {dispatch.resident_name}{destination}?"
    row = None
    for vol in vols:
        if vol["id"] in busy or vol["id"] in declined:
            continue
        request_id = str(uuid.uuid4())
        body = f"{request} Reply Y {request_id} or N {request_id}"
        try:
            rows = sb.table("dispatches").insert({
                "id": request_id, "event_id": event_id, "resident_id": dispatch.resident_id, "volunteer_id": vol["id"],
                "resource_id": dispatch.resource_id or None, "detail": body, "status": "sending",
            }).execute().data
            row = rows[0]
            break
        except Exception as exc:
            if getattr(exc, "code", None) != "23505":
                raise
            concurrent = sb.table("dispatches").select("*").eq("event_id", event_id).eq(
                "resident_id", dispatch.resident_id).execute().data
            for previous in concurrent:
                if previous["status"] in ("sending", "proposed", "accepted"):
                    return {"outcome": "already_pending", "dispatch_id": previous["id"]}
    if row is None:
        return {"outcome": "no_volunteer"}
    try:
        sid, channel = send_one(sb, vol["phone"], "telegram", body, owner_phone)
    except Exception:
        sb.table("dispatches").update({"status": "failed"}).eq("id", row["id"]).execute()
        raise
    status = "failed" if channel == "failed" else "proposed"
    sb.table("dispatches").update({"status": status}).eq("id", row["id"]).execute()
    sb.table("audit_log").insert({
        "event_id": event_id, "actor": "dispatcher", "action": f"volunteer_ask {channel}",
        "detail": f"{vol['name']} sid={sid} dispatch={row['id']}"}).execute()
    return {"outcome": "failed" if channel == "failed" else "asked", "dispatch_id": row["id"],
            "volunteer": vol["name"], "sid": sid, "channel": channel}


def volunteer_reply(sb, event_id: str, from_phone: str, body: str, dispatch_id: str = "") -> dict:
    from agent.safety import is_allowed, parse_allowlist

    if not is_allowed(from_phone, parse_allowlist(os.environ.get("PHONE_ALLOWLIST", ""))):
        return {"outcome": "dropped", "reason": "not_allowlisted"}
    volunteers = sb.table("volunteers").select("*").eq("phone", from_phone).eq("opted_in", True).execute().data
    if not volunteers:
        return {"outcome": "dropped", "reason": "unknown_volunteer"}
    parts = body.strip().split()
    if len(parts) == 2:
        if dispatch_id and dispatch_id != parts[1]:
            return {"outcome": "ignored", "reason": "request ID does not match reply"}
        reply, dispatch_id = parts[0].upper(), parts[1]
    elif len(parts) == 1 and dispatch_id:
        reply = parts[0].upper()
    else:
        return {"outcome": "ignored", "reason": "reply Y or N with the reviewed request ID"}
    if reply not in ("Y", "N"):
        return {"outcome": "ignored", "reason": "reply Y or N with the reviewed request ID"}
    query = sb.table("dispatches").select("*").eq("event_id", event_id).eq(
        "volunteer_id", volunteers[0]["id"]).eq("status", "proposed")
    query = query.eq("id", dispatch_id)
    rows = query.execute().data
    if len(rows) != 1:
        return {"outcome": "ignored", "reason": "no single pending dispatch"}
    if reply == "Y":
        return volunteer_yes(sb, rows[0]["id"], event_id)
    changed = sb.table("dispatches").update({"status": "declined"}).eq("event_id", event_id).eq(
        "id", rows[0]["id"]).eq("status", "proposed").execute().data
    if not changed:
        return {"outcome": "ignored", "reason": "dispatch already handled"}
    sb.table("audit_log").insert({"event_id": event_id, "actor": "dispatcher",
        "action": "volunteer_declined", "detail": rows[0]["id"]}).execute()
    from agent.coordinator import decision_input, maybe_ping, pending_add

    resident_id = rows[0]["resident_id"]
    gates = sb.table("gate_pending").select("*").eq("event_id", event_id).eq("status", "approved").execute().data
    reopened = False
    for gate in gates:
        if decision_input(gate).get("resident_id") == resident_id:
            changed = sb.table("gate_pending").update({"status": "open"}).eq("id", gate["id"]).eq(
                "status", "approved").execute().data
            reopened = reopened or bool(changed)
    if not reopened:
        residents = sb.table("residents").select("*").eq("id", resident_id).execute().data
        if residents:
            pending_add(sb, event_id, "dispatch_help", {"resident_id": resident_id,
                "resident_name": residents[0]["name"], "need": "wellness_check"})
    notification = maybe_ping(sb, event_id, "Volunteer declined; coordinator action needed", force=True)
    return {"outcome": "declined", "dispatch_id": rows[0]["id"], "coordinator_alert": notification}


def volunteer_yes(sb, dispatch_id: str, event_id: str) -> dict:
    rows = sb.table("dispatches").update({"status": "accepted"}).eq(
        "id", dispatch_id).eq("event_id", event_id).eq("status", "proposed").execute().data
    if not rows:
        return {"outcome": "ignored", "reason": "dispatch is not pending for this event"}
    sb.table("audit_log").insert({
        "event_id": event_id, "actor": "dispatcher", "action": "volunteer_accepted",
        "detail": dispatch_id}).execute()
    return {"outcome": "accepted", "dispatch_id": dispatch_id, "calendar": "skipped (not implemented)"}
