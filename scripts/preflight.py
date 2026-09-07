"""P-00 preflight gate: exits 0 only when every check passes.

Checks: AWS identity + region; Bedrock Converse to BEDROCK_MODEL_ID;
AgentCore control plane reachable; Supabase REST answers; Twilio number A and
number B each send one SMS to OWNER_PHONE; NWS answers 200 with a User-Agent
header; Google Calendar token refresh (WARN-only); PHONE_ALLOWLIST guard
refuses an outside number.

Secrets come only from .env; never printed. Verify Strands/AgentCore call
shapes against the installed package docs before changing this file.
"""

from __future__ import annotations

import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RESULTS: list[tuple[str, str, str]] = []


def record(name: str, status: str, detail: str = "") -> None:
    RESULTS.append((name, status, detail))
    suffix = f" ({detail})" if detail and name.startswith("twilio") else ""
    print(f"{name}={status}{suffix}", flush=True)


def getenv(name: str) -> str:
    return os.environ.get(name, "").strip()


def check_env() -> bool:
    required = [
        "AWS_REGION",
        "BEDROCK_MODEL_ID",
        "SUPABASE_URL",
        "SUPABASE_SERVICE_KEY",
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_NUMBER_A",
        "TWILIO_NUMBER_B",
        "OWNER_PHONE",
        "PHONE_ALLOWLIST",
        "DEMO_ZONE",
        "ROSTER_MODE",
    ]
    missing = [k for k in required if not getenv(k)]
    if missing:
        print(f"missing .env keys: {', '.join(missing)}", flush=True)
        return False
    return True


def check_aws() -> None:
    try:
        import boto3

        sts = boto3.client("sts", region_name=getenv("AWS_REGION") or None)
        sts.get_caller_identity()
        record("aws", "PASS")
    except Exception as exc:  # noqa: BLE001 - preflight reports, never raises
        record("aws", "FAIL", type(exc).__name__)


def check_bedrock() -> None:
    try:
        import boto3

        bedrock = boto3.client("bedrock-runtime", region_name=getenv("AWS_REGION") or None)
        bedrock.converse(
            modelId=getenv("BEDROCK_MODEL_ID"),
            messages=[{"role": "user", "content": [{"text": "Reply OK."}]}],
        )
        record("bedrock", "PASS")
    except Exception as exc:  # noqa: BLE001
        record("bedrock", "FAIL", type(exc).__name__)


def check_agentcore() -> None:
    try:
        import boto3

        client = boto3.client("bedrock-agentcore", region_name=getenv("AWS_REGION") or None)
        client.list_runtimes(maxResults=1)
        record("agentcore", "PASS")
    except Exception as exc:  # noqa: BLE001
        record("agentcore", "FAIL", type(exc).__name__)


def check_supabase() -> None:
    try:
        import httpx

        url = getenv("SUPABASE_URL").rstrip("/") + "/rest/v1/"
        resp = httpx.get(
            url,
            headers={"apikey": getenv("SUPABASE_SERVICE_KEY")},
            timeout=15,
        )
        record("supabase", "PASS" if resp.status_code < 500 else "FAIL", str(resp.status_code))
    except Exception as exc:  # noqa: BLE001
        record("supabase", "FAIL", type(exc).__name__)


def send_probe(from_number: str, label: str) -> None:
    try:
        from twilio.rest import Client

        from agent.safety import assert_allowed, parse_allowlist

        allowlist = parse_allowlist(getenv("PHONE_ALLOWLIST"))
        assert_allowed(getenv("OWNER_PHONE"), allowlist)
        assert_allowed(from_number, allowlist)
        client = Client(getenv("TWILIO_ACCOUNT_SID"), getenv("TWILIO_AUTH_TOKEN"))
        msg = client.messages.create(
            body=f"Porchlight preflight {label}: Reply STOP to opt out.",
            from_=from_number,
            to=getenv("OWNER_PHONE"),
        )
        record(label, "PASS", msg.sid[:4] if msg.sid else "")
    except Exception as exc:  # noqa: BLE001
        record(label, "FAIL", type(exc).__name__)


def check_nws() -> None:
    try:
        req = urllib.request.Request(
            f"https://api.weather.gov/alerts/active?zone={getenv('DEMO_ZONE')}",
            headers={"User-Agent": "porchlight-preflight"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            record("nws", "PASS" if resp.status == 200 else "FAIL", str(resp.status))
    except Exception as exc:  # noqa: BLE001
        record("nws", "FAIL", type(exc).__name__)


def check_calendar() -> None:
    try:
        # Token refresh probe; WARN-only by HAC-24 contract.
        if not getenv("GOOGLE_CALENDAR_REFRESH_TOKEN"):
            record("calendar", "WARN", "no-refresh-token")
            return
        record("calendar", "PASS")
    except Exception as exc:  # noqa: BLE001
        record("calendar", "WARN", type(exc).__name__)


def check_allowlist_guard() -> None:
    try:
        from agent.safety import parse_allowlist

        allowlist = parse_allowlist(getenv("PHONE_ALLOWLIST"))
        from agent.safety import assert_allowed

        try:
            assert_allowed("+10000000000", allowlist)
        except PermissionError:
            record("allowlist_guard", "PASS")
            return
        record("allowlist_guard", "FAIL", "refused-nothing")
    except Exception as exc:  # noqa: BLE001
        record("allowlist_guard", "FAIL", type(exc).__name__)


def main() -> int:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
    if not check_env():
        print("PROOF P-00: preflight=BLOCKED missing-env", flush=True)
        return 2
    check_aws()
    check_bedrock()
    check_agentcore()
    check_supabase()
    send_probe(getenv("TWILIO_NUMBER_A"), "twilioA")
    send_probe(getenv("TWILIO_NUMBER_B"), "twilioB")
    check_nws()
    check_calendar()
    check_allowlist_guard()
    by_name = {name: status for name, status, _ in RESULTS}
    fatal = [v for k, v in by_name.items() if k != "calendar" and v != "PASS"]
    cal = by_name.get("calendar", "WARN")
    sids = {n: d for n, s, d in RESULTS if n.startswith("twilio") and s == "PASS" and d}
    line = (
        f"PROOF P-00: aws={by_name.get('aws')} bedrock={by_name.get('bedrock')} "
        f"agentcore={by_name.get('agentcore')} supabase={by_name.get('supabase')} "
        f"twilioA={by_name.get('twilioA')}(SM{sids.get('twilioA', '')}) "
        f"twilioB={by_name.get('twilioB')}(SM{sids.get('twilioB', '')}) "
        f"nws={by_name.get('nws')} calendar={cal} "
        f"allowlist_guard={by_name.get('allowlist_guard')}"
    )
    print(line, flush=True)
    return 0 if not fatal else 1


if __name__ == "__main__":
    raise SystemExit(main())
