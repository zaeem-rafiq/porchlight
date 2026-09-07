"""Send the outreach wave for an event (P-03; reused by P-08 rehearsal).

Usage: python scripts/wave.py [--inject data/fixtures/alerts/heat.json] [--event-id UUID]
Computes deterministic tiers, sends tier-1 then tier-2 then tier-3, prints counts.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main() -> int:
    from dotenv import load_dotenv
    from supabase import create_client

    load_dotenv()
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    sb = create_client(url, key).schema("porchlight")

    if "--event-id" in sys.argv:
        event_id = sys.argv[sys.argv.index("--event-id") + 1]
    else:
        from agent.poller import load_protocol, normalize, store

        load_protocol()
        path = (sys.argv[sys.argv.index("--inject") + 1] if "--inject" in sys.argv
                else "data/fixtures/alerts/heat.json")
        import json

        with open(path, encoding="utf-8") as fh:
            feature = json.load(fh)
        item = normalize(feature, f"drill:{os.path.basename(path)}")
        assert item is not None
        rows = sb.table("hazard_events").select("id").eq("nws_id", item["nws_id"]).execute().data
        if rows:
            event_id = rows[0]["id"]
            print(f"event reused={event_id}")
        else:
            created, _ = store([item], observed_only=False)
            event_id = sb.table("hazard_events").select("id").eq(
                "nws_id", item["nws_id"]).execute().data[0]["id"]
            print(f"event created={event_id}")

    from agent.tiering import deterministic_tier, score_resident

    residents = sb.table("residents").select("*").execute().data
    tier_map = {r["id"]: deterministic_tier(score_resident(r, "heat")) for r in residents}

    from agent.outreach import send_wave

    result = send_wave(event_id, tier_map)
    sent_rows = sb.table("contacts").select("id").eq("event_id", event_id).execute().data
    print(f"wave event={event_id} sent={result['sent']} real={result['real']} "
          f"simulated={result['simulated']} contact_rows={len(sent_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
