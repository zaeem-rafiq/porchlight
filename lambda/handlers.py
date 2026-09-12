"""Lambda shims (P-05): thin HTTP/schedule adapters over the Runtime + Supabase."""

import json
import os


def _runtime(action_payload, session_suffix):
    import boto3

    event_id = action_payload.get("event_id") or "00000000-0000-0000-0000-000000000000"
    client = boto3.client("bedrock-agentcore", region_name=os.environ.get("AWS_REGION"))
    resp = client.invoke_agent_runtime(
        agentRuntimeArn=os.environ["RUNTIME_ARN"],
        runtimeSessionId=f"porchlight-{event_id}-{session_suffix}-sess",
        payload=json.dumps(action_payload).encode(),
        contentType="application/json",
        accept="application/json",
    )
    body = resp.get("response", b"")
    if hasattr(body, "read"):
        body = body.read()
    return json.loads(body or b"{}")


def nws_poll_handler(event, context):
    import urllib.request

    zone = os.environ["DEMO_ZONE"]
    req = urllib.request.Request(
        f"https://api.weather.gov/alerts/active?zone={zone}",
        headers={"User-Agent": "porchlight-nws-poll"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        payload = json.load(resp)
    feats = payload.get("features", [])
    if not feats:
        return {"ok": True, "alerts": 0}
    return _runtime({"action": "hazard.detected", "alert": feats[0],
                     "source": f"nws:{feats[0].get('id', '')}",
                     "observed_only": not os.environ.get("LIVE_ZONE")}, "poll")


def telegram_inbound_handler(event, context):
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    raw_body = event.get("body") or ""
    if event.get("isBase64Encoded"):
        import base64

        raw_body = base64.b64decode(raw_body).decode()
    console_key = os.environ.get("CONSOLE_KEY", "")
    key_header = headers.get("x-console-key", "")
    if console_key:
        if key_header == console_key:
            try:
                incoming = json.loads(raw_body or "{}")
            except Exception as exc:
                return {"statusCode": 400, "body": json.dumps({"error": f"bad json: {exc}"})}
            if not isinstance(incoming, dict):
                return {"statusCode": 400, "body": json.dumps({"error": "payload must be a JSON object"})}
            op = incoming.get("op", "inbound")
            if op == "inject":
                return {"statusCode": 200, "body": json.dumps(_runtime(
                    {"action": "hazard.detected", "alert": incoming.get("alert", {}),
                     "source": f"drill:{incoming.get('fixture', 'console')}",
                     "observed_only": False}, "console"))}
            if op == "volunteer":
                return {"statusCode": 200, "body": json.dumps(_runtime(
                    {"action": "inbound.volunteer", "dispatch_id": incoming.get("dispatch_id", ""),
                     "body": incoming.get("text", ""),
                     "event_id": incoming.get("event_id", "")}, "console"))}
            if op == "coordinator":
                return {"statusCode": 200, "body": json.dumps(_runtime(
                    {"action": "inbound.coordinator", "body": incoming.get("text", ""),
                     "event_id": incoming.get("event_id", "")}, "console"))}
            return {"statusCode": 200, "body": json.dumps(_runtime(
                {"action": "inbound.resident", "from": incoming.get("from", ""),
                 "to": incoming.get("to") or "telegram", "body": incoming.get("text", ""),
                 "event_id": incoming.get("event_id", "")}, "console"))}
        else:
            try:
                chk = json.loads(raw_body or "{}")
            except Exception:
                chk = {}
            if key_header or (isinstance(chk, dict) and "op" in chk):
                return {"statusCode": 403, "body": json.dumps({"error": "invalid console key"})}

    secret_token = os.environ.get("TELEGRAM_SECRET_TOKEN", "").strip()
    if secret_token:
        if headers.get("x-telegram-bot-api-secret-token", "") != secret_token:
            return {"statusCode": 403, "body": json.dumps({"error": "bad secret token"})}

    try:
        incoming = json.loads(raw_body or "{}")
    except Exception as exc:
        return {"statusCode": 400, "body": json.dumps({"error": f"bad json: {exc}"})}

    if not isinstance(incoming, dict):
        return {"statusCode": 400, "body": json.dumps({"error": "payload must be a JSON object"})}

    msg = incoming.get("message") or incoming.get("edited_message") or {}
    if not isinstance(msg, dict):
        return {"statusCode": 200, "body": json.dumps({"ok": True, "ignored": "no_text"})}

    text = (msg.get("text") or "").strip()
    chat_id = str((msg.get("chat") or {}).get("id", "")).strip() if isinstance(msg.get("chat"), dict) else ""
    from_id = str((msg.get("from") or {}).get("id", "")).strip() if isinstance(msg.get("from"), dict) else ""

    if not text:
        return {"statusCode": 200, "body": json.dumps({"ok": True, "ignored": "no_text"})}

    owner_chat = os.environ.get("TELEGRAM_OWNER_CHAT_ID", "").strip()
    owner_phone = os.environ.get("OWNER_PHONE", "").strip()

    if (owner_chat and chat_id == owner_chat) or (owner_chat and from_id == owner_chat):
        from_number = owner_phone
    else:
        from_number = chat_id

    event_id = incoming.get("event_id", "")
    if not event_id:
        from supabase import create_client

        sb = create_client(os.environ["SUPABASE_URL"].rstrip("/"),
                           os.environ["SUPABASE_SERVICE_KEY"]).schema("porchlight")
        open_events = sb.table("hazard_events").select("id").eq("status", "open").execute().data
        event_id = open_events[-1]["id"] if open_events else ""

    upper = text.upper()
    if upper.startswith("COORD ") or upper.startswith("/COORD "):
        action, key = "inbound.coordinator", "coord"
        body = text.split(" ", 1)[1].strip() if " " in text else text
    else:
        action, key = "inbound.resident", "resident"
        body = text

    return {"statusCode": 200, "body": json.dumps(_runtime(
        {"action": action, "from": from_number, "to": "telegram",
         "body": body, "event_id": event_id}, key))}


twilio_inbound_handler = telegram_inbound_handler


def tick_handler(event, context):
    from supabase import create_client

    sb = create_client(os.environ["SUPABASE_URL"].rstrip("/"),
                       os.environ["SUPABASE_SERVICE_KEY"]).schema("porchlight")
    open_events = sb.table("hazard_events").select("id").eq("status", "open").execute().data
    if not open_events:
        return {"ok": True, "events": 0}
    out = []
    for e in open_events:
        out.append(_runtime({"action": "tick", "event_id": e["id"],
                             "age_min": 10**9, "silence_min": 20.0}, "tick"))
    return {"ok": True, "events": len(open_events), "fired": out}
