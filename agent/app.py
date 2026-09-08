"""Porchlight Runtime entrypoint (P-05): one BedrockAgentCoreApp, six actions.

Actions: hazard.detected, inbound.resident, inbound.coordinator,
inbound.volunteer, tick (retry + silence ladders), event.closed.
The hazard session is long-running: callers pass
runtimeSessionId = "porchlight-" + event_id + suffix; Supabase stays the
source of truth and the DB-durable gate queue survives across invocations
(ADR-005). Secrets come from Secrets Manager porchlight/app in the cloud,
from .env locally. Nothing here sends outside PHONE_ALLOWLIST or dials 911.
"""

from __future__ import annotations

import json
import os

from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

_config: dict[str, str] = {}


def get_config() -> dict[str, str]:
    global _config
    if _config:
        return _config
    if os.environ.get("AWS_EXECUTION_ENV"):
        import boto3

        sm = boto3.client("secretsmanager")
        _config = json.loads(sm.get_secret_value(SecretId="porchlight/app")["SecretString"])
        for key, value in _config.items():
            os.environ.setdefault(key, value)
    else:
        from dotenv import load_dotenv

        load_dotenv()
        _config = dict(os.environ)
    return _config


def _sb():
    from supabase import create_client

    cfg = get_config()
    return create_client(cfg["SUPABASE_URL"].rstrip("/"), cfg["SUPABASE_SERVICE_KEY"]).schema("porchlight")


@app.entrypoint
def porchlight(payload: dict) -> dict:
    action = (payload or {}).get("action", "")
    handlers = {
        "hazard.detected": on_hazard_detected,
        "inbound.resident": on_inbound_resident,
        "inbound.coordinator": on_inbound_coordinator,
        "inbound.volunteer": on_inbound_volunteer,
        "dispatch.run": on_dispatch_run,
        "tick": on_tick,
        "event.closed": on_event_closed,
    }
    if action not in handlers:
        return {"accepted": False, "error": f"unknown action {action}"}
    return handlers[action](payload)


def on_hazard_detected(payload: dict) -> dict:
    import agent.poller as poller
    from agent.outreach import send_wave
    from agent.tiering import deterministic_tier, score_resident

    poller.load_protocol()
    feature = payload.get("alert") or {}
    item = poller.normalize(feature, payload.get("source", "drill:runtime"))
    if item is None:
        return {"accepted": False, "error": "unrecognized event type"}
    created, _ = poller.store([item], observed_only=bool(payload.get("observed_only", False)))
    sb = _sb()
    rows = sb.table("hazard_events").select("id").eq("nws_id", item["nws_id"]).execute().data
    event_id = rows[0]["id"] if rows else None
    if not event_id or payload.get("observed_only"):
        return {"accepted": True, "event_id": event_id, "wave": "skipped_observed_only"}
    residents = sb.table("residents").select("*").execute().data
    tier_map = {r["id"]: deterministic_tier(score_resident(r, item["row"].type)) for r in residents}
    result = send_wave(event_id, tier_map)
    print(f"wave sent n={result['sent']}", flush=True)
    return {"accepted": True, "event_id": event_id, "wave": result}


def on_inbound_resident(payload: dict) -> dict:
    from agent.inbound import handle_inbound

    return handle_inbound(payload["from"], payload["to"], payload["body"], payload["event_id"])


def on_inbound_coordinator(payload: dict) -> dict:
    from agent.inbound import handle_inbound

    cfg = get_config()
    body = payload["body"]
    if not body.upper().startswith("COORD ") and body.strip() in ("1", "2", "3"):
        body = "COORD " + body.strip()
    return handle_inbound(cfg["OWNER_PHONE"], cfg["TWILIO_NUMBER_B"], body, payload["event_id"])


def on_inbound_volunteer(payload: dict) -> dict:
    from agent.dispatch import volunteer_yes

    if payload.get("body", "").strip().upper() != "Y":
        return {"outcome": "declined"}
    return volunteer_yes(_sb(), payload["dispatch_id"], payload["event_id"])


def on_dispatch_run(payload: dict) -> dict:
    from agent.coordinator import CoordinatorGate, pending_open
    from agent.dispatch import propose_dispatch
    from agent.triage import triage_reply

    sb = _sb()
    event_id = payload["event_id"]
    resident = sb.table("residents").select("*").eq(
        "id", payload["resident_id"]).execute().data[0]
    triage, _ = triage_reply(payload.get("body", ""), resident)
    dispatch = propose_dispatch(resident, triage, event_id)

    class _GateEvent:
        tool_name = "escalate_medical"
        tool_input = {"resident_name": resident["name"]}

        def interrupt(self, token):
            self.token = token

    ev = _GateEvent()
    CoordinatorGate(sb, event_id).on_before_tool_call(ev)
    return {"accepted": True, "held": ev.token == "coordinator-decision",
            "pending": len(pending_open(sb, event_id)),
            "dispatch": dispatch.model_dump()}


def on_tick(payload: dict) -> dict:
    from agent.coordinator import silence_check
    from agent.inbound import ladder_action

    sb = _sb()
    event_id = payload["event_id"]
    fired: list[str] = []
    contacts = sb.table("contacts").select("*").eq("event_id", event_id).execute().data
    for c in contacts:
        step = ladder_action({**c, "_sent_min": 0.0}, payload.get("age_min", 10**9))
        if step == "resend":
            sb.table("contacts").update({"attempts": c["attempts"] + 1, "status": "resent"}).eq(
                "id", c["id"]).execute()
            fired.append(f"resend:{c['id'][:8]}")
        elif step == "flag_unreachable":
            sb.table("contacts").update({"status": "unreachable"}).eq("id", c["id"]).execute()
            fired.append(f"unreachable:{c['id'][:8]}")
        sil = silence_check(sb, event_id, c, age_min=payload.get("age_min", 10**9),
                            limit_min=payload.get("silence_min", 20.0))
        if sil:
            fired.append(f"silence:{sil['resident']}")
    return {"accepted": True, "fired": fired}


def on_event_closed(payload: dict) -> dict:
    _sb().table("hazard_events").update({"status": "closed"}).eq(
        "id", payload["event_id"]).execute()
    return {"accepted": True, "event_id": payload["event_id"]}


if __name__ == "__main__":
    app.run()
