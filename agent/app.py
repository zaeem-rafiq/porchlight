"""Porchlight Runtime entrypoint (P-05): one BedrockAgentCoreApp and persisted workflow state.

Actions: hazard.detected, inbound.resident, inbound.coordinator,
inbound.volunteer, tick (retry + silence ladders), event.closed.
Callers pass
runtimeSessionId = "porchlight-" + event_id + suffix; Supabase stays the
source of truth and the DB-durable gate queue survives across invocations
(ADR-005). Secrets come from Secrets Manager porchlight/app in the cloud,
from .env locally. Nothing here sends outside PHONE_ALLOWLIST or dials 911.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

_config: dict[str, str] = {}


def get_config() -> dict[str, str]:
    global _config
    if _config:
        return _config
    secret_id = os.environ.get("PORCHLIGHT_SECRET_ID", "")
    if not secret_id and os.environ.get("AWS_EXECUTION_ENV"):
        secret_id = "porchlight/app"
    if secret_id:
        import boto3

        sm = boto3.client("secretsmanager")
        _config = json.loads(sm.get_secret_value(SecretId=secret_id)["SecretString"])
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
    get_config()
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
    sender = payload.get("from", "")
    if not sender or sender != cfg.get("OWNER_PHONE"):
        return {"outcome": "dropped", "reason": "not_coordinator"}
    body = payload["body"]
    if body.lower().startswith("/coord "):
        body = "COORD " + body[7:].strip()
    elif not body.upper().startswith("COORD "):
        body = "COORD " + body.strip()
    return handle_inbound(sender, "coordinator", body, payload["event_id"])


def on_inbound_volunteer(payload: dict) -> dict:
    from agent.dispatch import volunteer_reply

    return volunteer_reply(_sb(), payload["event_id"], payload.get("from", ""),
                           payload.get("body", ""), payload.get("dispatch_id", ""))


def on_dispatch_run(payload: dict) -> dict:
    from agent.coordinator import maybe_ping, pending_add, pending_open
    from agent.triage import triage_reply

    sb = _sb()
    event_id = payload["event_id"]
    rows = sb.table("residents").select("*").eq("id", payload["resident_id"]).execute().data
    if not rows or rows[0].get("opted_out"):
        return {"accepted": False, "error": "resident unavailable"}
    resident = rows[0]
    triage, _ = triage_reply(payload.get("body", ""), resident)
    if triage.status not in ("medical", "needs_help"):
        return {"accepted": False, "error": "no dispatch need"}
    pending_add(sb, event_id, "escalate_medical" if triage.status == "medical" else "dispatch_help",
                {"resident_id": resident["id"], "resident_name": resident["name"],
                 "need": triage.need, "quote": triage.quote})
    notification = maybe_ping(sb, event_id, "Assistance requested", force=True)
    return {"accepted": True, "held": True, "gate": "durable_coordinator_approval",
            "pending": len(pending_open(sb, event_id)), "notification": notification}


def on_tick(payload: dict) -> dict:
    from agent.coordinator import maybe_ping, pending_add, silence_check
    from agent.inbound import ladder_action, RESEND_AFTER_MIN, UNREACHABLE_AFTER_MIN
    from agent.outreach import send_one

    sb = _sb()
    event_id = payload["event_id"]
    now = datetime.now(timezone.utc)
    fired: list[str] = []
    contacts = sb.table("contacts").select("*").eq("event_id", event_id).execute().data
    for c in contacts:
        stamp = c.get("last_inbound") if c.get("status") == "medical" else c.get("last_outbound")
        if not stamp:
            continue
        try:
            sent_at = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            age_min = max(0.0, (now - sent_at).total_seconds() / 60)
        except (ValueError, TypeError):
            continue
        step = ladder_action({**c, "_sent_min": 0.0}, age_min,
                             unreachable_after=UNREACHABLE_AFTER_MIN - RESEND_AFTER_MIN)
        if step == "resend":
            residents = sb.table("residents").select("*").eq("id", c["resident_id"]).execute().data
            if not residents or residents[0].get("opted_out"):
                continue
            resident = residents[0]
            claimed = sb.table("contacts").update({"status": "retrying"}).eq("id", c["id"]).eq(
                "status", "sent").eq("attempts", 1).execute().data
            if not claimed:
                continue
            text = ("Porchlight: seguimos pendientes de ti. Responde 1 si estás bien, 2 si necesitas ayuda. STOP para salir."
                    if resident.get("language") == "es" else
                    "Porchlight: checking on you again. Reply 1 if OK, 2 for help. Reply STOP to opt out.")
            try:
                sid, channel = send_one(sb, resident["phone"], "telegram", text,
                                       os.environ.get("OWNER_PHONE", "").strip())
            except Exception:
                sb.table("contacts").update({"status": "retry_failed"}).eq("id", c["id"]).eq("status", "retrying").execute()
                raise
            change = {"status": "retry_failed"} if channel == "failed" else {
                "attempts": 2, "status": "resent", "last_outbound": now.isoformat()}
            sb.table("contacts").update(change).eq("id", c["id"]).eq("status", "retrying").execute()
            sb.table("audit_log").insert({"event_id": event_id, "actor": "retry",
                "action": f"resend {channel}", "detail": f"{resident['name']} sid={sid}"}).execute()
            fired.append(f"{'resend_failed' if channel == 'failed' else 'resend'}:{c['id']}")
        elif step == "flag_unreachable":
            changed = sb.table("contacts").update({"status": "unreachable"}).eq("id", c["id"]).eq(
                "status", "resent").execute().data
            if changed:
                resident = sb.table("residents").select("*").eq("id", c["resident_id"]).execute().data[0]
                pending_add(sb, event_id, "mark_unreachable_tier1", {
                    "resident_id": resident["id"], "resident_name": resident["name"]})
                fired.append(f"unreachable:{c['id']}")
        sil = silence_check(sb, event_id, c, age_min=age_min)
        if sil:
            fired.append(f"silence:{sil['resident']}:{sil['channel']}")
    maybe_ping(sb, event_id, "Check-in decisions pending")
    return {"accepted": True, "fired": fired}


def on_event_closed(payload: dict) -> dict:
    _sb().table("hazard_events").update({"status": "closed"}).eq(
        "id", payload["event_id"]).execute()
    return {"accepted": True, "event_id": payload["event_id"]}


if __name__ == "__main__":
    app.run()
