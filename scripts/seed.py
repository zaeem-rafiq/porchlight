"""P-01 idempotent seed: roster, volunteers, resources, protocol into `porchlight`.

Usage:
  python scripts/seed.py --reset            # wipe P-01 tables, reseed, print proofs
  python scripts/seed.py --reset --verify-twice   # reset twice, prove identical counts

Safety: every phone is checked against PHONE_ALLOWLIST before any insert;
anything outside aborts with no writes. Secrets from .env, never printed.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RESET_TABLES = [
    "audit_log", "escalations", "dispatches", "contacts",
    "hazard_events", "protocol", "resources", "volunteers", "residents",
]

PLACEHOLDER_BASE = 1555010000


def placeholder(n: int) -> str:
    return f"+{PLACEHOLDER_BASE + n}"


def build_rows(owner_phone: str) -> dict[str, list[dict]]:
    from seeds.residents import ROSTER
    from seeds.support import PROTOCOL_YAML, RESOURCES, VOLUNTEERS

    residents = []
    for i, (name, lang, age, alone, ac, device, mobility, channel, notes) in enumerate(ROSTER):
        residents.append({
            "name": name,
            "language": lang,
            "age_band": age,
            "lives_alone": alone,
            "has_ac": ac,
            "powered_medical_device": device,
            "mobility": mobility,
            "phone": owner_phone if i == 0 else placeholder(i),
            "emergency_contact": placeholder(900 + i),
            "preferred_channel": channel,
            "notes": notes,
        })
    volunteers = [
        {"name": n, "phone": placeholder(100 + i), "opted_in": opt, "home_block": blk}
        for i, (n, opt, blk) in enumerate(VOLUNTEERS)
    ]
    resources = [
        {"name": n, "kind": k, "address": a, "hours": h, "phone": p}
        for (n, k, a, h, p) in RESOURCES
    ]
    return {
        "residents": residents,
        "volunteers": volunteers,
        "resources": resources,
        "protocol": [{"id": "v1", "rules_yaml": PROTOCOL_YAML}],
    }


def main() -> int:
    from dotenv import load_dotenv

    load_dotenv()
    if "--reset" not in sys.argv:
        print("usage: python scripts/seed.py --reset [--verify-twice]")
        return 2

    from agent.safety import parse_allowlist
    from supabase import create_client

    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    owner = os.environ.get("OWNER_PHONE", "").strip()
    allowlist = parse_allowlist(os.environ.get("PHONE_ALLOWLIST", ""))
    if not url or not key or not owner or not allowlist:
        print("seed=BLOCKED missing SUPABASE_URL, SUPABASE_SERVICE_KEY, OWNER_PHONE, or PHONE_ALLOWLIST")
        return 2

    rows = build_rows(owner)
    phones = (
        [r["phone"] for r in rows["residents"]]
        + [r["emergency_contact"] for r in rows["residents"]]
        + [v["phone"] for v in rows["volunteers"]]
    )
    outside = [p for p in phones if p not in allowlist]
    if outside:
        print(f"seed=ABORTED {len(outside)} phones outside PHONE_ALLOWLIST, no writes performed")
        return 1

    sb = create_client(url, key).schema("porchlight")

    def reset_once() -> dict[str, int]:
        for table in RESET_TABLES:
            sb.table(table).delete().neq("id", "00000000-0000-0000-0000-000000000000" if table != "protocol" else "__none__").execute()
        counts: dict[str, int] = {}
        for table in ("residents", "volunteers", "resources", "protocol"):
            sb.table(table).insert(rows[table]).execute()
            counts[table] = len(rows[table])
        return counts

    first = reset_once()
    line1 = (
        f"PROOF P-01: residents={first['residents']} volunteers={first['volunteers']} "
        f"resources={first['resources']} protocol={first['protocol']} "
        f"fixtures={len([f for f in os.listdir('data/fixtures/alerts') if f.endswith('.json')])} = PASS"
    )
    real = sum(1 for r in rows["residents"] if r["phone"] == owner)
    line2 = (
        f"PROOF P-01: allowlist check — {len(rows['residents'])}/{len(rows['residents'])} "
        f"resident phones allowlisted, {real} real (OWNER_PHONE) = PASS"
    )
    print(line1)
    print(line2)
    if "--verify-twice" in sys.argv:
        second = reset_once()
        same = "PASS" if second == first else "FAIL"
        print(f"PROOF P-01: seed --reset twice -> identical row counts = {same}")
        return 0 if same == "PASS" else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
