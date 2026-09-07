"""Dispatcher (P-04): need -> resource/volunteer matching + dispatch rows.

For every needs_help/medical triage, match the need to a resource (nearest
open cooling center, or power/wellness guidance) and, for transport, to an
opted-in volunteer. Volunteer asks go out from number B (real only for the
owner; placeholders simulated). On Y, a Calendar event is created (or the
step logs skipped when no token is configured).
"""

from __future__ import annotations

import os
import sys

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
    vols = sb.table("volunteers").select("*").eq("opted_in", True).execute().data
    if not vols:
        return {"outcome": "no_volunteer"}
    vol = vols[0]
    body = (f"Porchlight: can you take {dispatch.resident_name} to {dispatch.resource_name} "
            f"at 2pm? Reply Y or N")
    if vol["phone"] == owner_phone:
        from twilio.rest import Client

        sid = Client(os.environ.get("TWILIO_ACCOUNT_SID", ""),
                     os.environ.get("TWILIO_AUTH_TOKEN", "")).messages.create(
            body=body, from_=os.environ.get("TWILIO_NUMBER_B", "").strip(),
            to=vol["phone"]).sid
        channel = "twilio"
    else:
        sid, channel = f"SIM-VOL-{abs(hash(body)) % 10**8:08d}", "simulated"
    row = sb.table("dispatches").insert({
        "event_id": event_id, "volunteer_id": vol["id"],
        "resource_id": None, "detail": body, "status": "proposed",
    }).execute().data[0]
    sb.table("audit_log").insert({
        "event_id": event_id, "actor": "dispatcher", "action": f"volunteer_ask {channel}",
        "detail": f"{vol['name']} sid={sid}"}).execute()
    return {"outcome": "asked", "dispatch_id": row["id"], "volunteer": vol["name"],
            "sid": sid, "channel": channel}


def volunteer_yes(sb, dispatch_id: str, event_id: str) -> dict:
    from agent.coordinator import create_calendar_event

    sb.table("dispatches").update({"status": "accepted"}).eq("id", dispatch_id).execute()
    cal = create_calendar_event(f"Porchlight transport {dispatch_id}",
                                "Volunteer transport for wellness check-in.")
    sb.table("audit_log").insert({
        "event_id": event_id, "actor": "dispatcher", "action": "volunteer_accepted",
        "detail": f"{dispatch_id} calendar={cal}"}).execute()
    return {"outcome": "accepted", "dispatch_id": dispatch_id, "calendar": cal}
