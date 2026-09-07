"""NWS alert poller (P-02): fetch, normalize, dedupe, store.

Real alerts are observed_only unless LIVE_ZONE is set (never in hackathon).
--inject <fixture.json> runs the same normalize+store path for demos.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

NWS_URL = "https://api.weather.gov/alerts/active?zone={zone}"

EVENT_TYPES: dict[str, str] = {}


def load_protocol() -> dict:
    import yaml

    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "protocol.yaml"), encoding="utf-8") as fh:
        proto = yaml.safe_load(fh)
    EVENT_TYPES.update(proto.get("type_map", {}))
    return proto


def fetch_live(zone: str) -> tuple[int, list[dict]]:
    req = urllib.request.Request(
        NWS_URL.format(zone=zone), headers={"User-Agent": "porchlight-poller"}
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        status, payload = resp.status, json.load(resp)
    features = payload.get("features", []) if isinstance(payload, dict) else []
    return status, features


def normalize(feature: dict, source: str) -> dict | None:
    from agent.models import HazardEvent

    props = feature.get("properties", {})
    event = props.get("event", "")
    kind = EVENT_TYPES.get(event)
    if kind is None:
        return None
    alert_id = feature.get("id", "")
    hazard = HazardEvent(
        type=kind,
        severity=str(props.get("severity", "")),
        onset=props.get("onset"),
        expires=props.get("expires") or props.get("ends"),
        headline=str(props.get("headline", event)),
        source=source,
        zone=str(props.get("areaDesc", "")),
    )
    return {"row": hazard, "nws_id": alert_id or None}


def store(items: list[dict], observed_only: bool) -> tuple[int, int]:
    from dotenv import load_dotenv
    from supabase import create_client

    load_dotenv()
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    sb = create_client(url, key).schema("porchlight")
    created, dupes = 0, 0
    for item in items:
        row = item["row"]
        data = row.model_dump()
        data["nws_id"] = item["nws_id"]
        data["status"] = "observed_only" if observed_only else "open"
        if item["nws_id"]:
            existing = (
                sb.table("hazard_events").select("id").eq("nws_id", item["nws_id"]).execute()
            )
            if existing.data:
                dupes += 1
                continue
        sb.table("hazard_events").insert(data).execute()
        created += 1
    return created, dupes


def main() -> int:
    load_protocol()
    if "--inject" in sys.argv:
        path = sys.argv[sys.argv.index("--inject") + 1]
        with open(path, encoding="utf-8") as fh:
            feature = json.load(fh)
        item = normalize(feature, f"drill:{os.path.basename(path)}")
        if item is None:
            print("inject=FAIL unrecognized event type")
            return 1
        created, dupes = store([item], observed_only=False)
        print(f"inject created={created} dupes={dupes}")
        return 0
    from dotenv import load_dotenv

    load_dotenv()
    zone = os.environ.get("DEMO_ZONE", "")
    status, features = fetch_live(zone)
    load_protocol()
    parsed = [normalize(f, f"nws:{f.get('id', '')}") for f in features]
    parsed = [p for p in parsed if p is not None]
    print(f"live poll {zone} -> HTTP {status}, {len(parsed)} alerts parsed")
    if parsed:
        live_zone = os.environ.get("LIVE_ZONE", "")
        created, dupes = store(parsed, observed_only=not live_zone)
        print(f"stored created={created} dupes={dupes} (observed_only={not live_zone})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
