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


def twilio_inbound_handler(event, context):
    from twilio.request_validator import RequestValidator

    validator = RequestValidator(os.environ["TWILIO_AUTH_TOKEN"])
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    url = f"https://{headers.get('host', '')}{event.get('rawPath', '')}"
    params = {}
    raw_body = event.get("body") or ""
    if event.get("isBase64Encoded"):
        import base64

        raw_body = base64.b64decode(raw_body).decode()
    if raw_body:
        import urllib.parse

        params = dict(urllib.parse.parse_qsl(raw_body))
    if not validator.validate(url, params, headers.get("x-twilio-signature", "")):
        return {"statusCode": 403, "body": json.dumps({
            "error": "bad signature", "url": url,
            "param_keys": sorted(params.keys()),
            "ver": event.get("version", "?")})}
    to_number, from_number = params.get("To", ""), params.get("From", "")
    body = params.get("Body", "")
    number_a = os.environ.get("TWILIO_NUMBER_A", "")
    event_id = params.get("event_id", "")
    if not event_id:
        from supabase import create_client

        sb = create_client(os.environ["SUPABASE_URL"].rstrip("/"),
                           os.environ["SUPABASE_SERVICE_KEY"]).schema("porchlight")
        open_events = sb.table("hazard_events").select("id").eq("status", "open").execute().data
        event_id = open_events[-1]["id"] if open_events else ""
    if to_number == number_a:
        action, key = "inbound.coordinator", "coord"
    else:
        action, key = "inbound.resident", "resident"
    return {"statusCode": 200, "body": json.dumps(_runtime(
        {"action": action, "from": from_number, "to": to_number,
         "body": body, "event_id": event_id}, key))}


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
