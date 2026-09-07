"""Tiering (P-02): deterministic score + agent adjudication at boundaries.

`score_resident` is a pure function AND exposed as a Strands @tool.
Residents within `boundary_margin` of a tier cut are adjudicated by one
Agent(structured_output_model=TierPlan) call that must give a one-line
reason each; everyone else takes the deterministic tier.
"""

from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strands import tool

SCORES = {
    "lives_alone": 2,
    "no_ac_in_heat": 2,
    "powered_device_in_outage": 3,
    "powered_device_in_heat": 1,
    "age_85_plus": 2,
    "age_75_84": 1,
    "mobility_wheelchair": 2,
    "mobility_walker_or_limited": 1,
}
TIER1_MIN, TIER2_MIN, MARGIN = 5, 3, 1


@tool
def score_resident(resident: dict, hazard_type: str) -> int:
    """Score a resident's risk for a hazard type. Higher means more urgent."""
    s = 0
    if resident.get("lives_alone"):
        s += SCORES["lives_alone"]
    if hazard_type == "heat" and not resident.get("has_ac"):
        s += SCORES["no_ac_in_heat"]
    if resident.get("powered_medical_device"):
        s += SCORES["powered_device_in_outage"] if hazard_type == "outage" else SCORES["powered_device_in_heat"]
    age = str(resident.get("age_band", ""))
    if age == "85+":
        s += SCORES["age_85_plus"]
    elif age == "75-84":
        s += SCORES["age_75_84"]
    mob = str(resident.get("mobility", ""))
    if mob == "wheelchair":
        s += SCORES["mobility_wheelchair"]
    elif mob in ("walker", "limited"):
        s += SCORES["mobility_walker_or_limited"]
    return s


def deterministic_tier(score: int) -> int:
    if score >= TIER1_MIN:
        return 1
    if score >= TIER2_MIN:
        return 2
    return 3


def is_boundary(score: int) -> bool:
    return min(abs(score - TIER1_MIN), abs(score - TIER2_MIN)) <= MARGIN


def adjudicate(cases: list[dict], hazard_type: str, model_id: str, region: str) -> dict[str, dict]:
    from strands import Agent
    from strands.models import BedrockModel

    from agent.models import TierPlan

    agent = Agent(
        model=BedrockModel(model_id=model_id, region_name=region or None),
        tools=[score_resident],
        structured_output_model=TierPlan,
        system_prompt=(
            "You triage vulnerable neighbors for wellness check-ins. "
            "For each listed resident, confirm or adjust the deterministic tier "
            "(1 = check first, 3 = check last) and give a one-line reason. "
            "Reply with the TierPlan structure only."
        ),
    )
    payload = json.dumps([{"name": c["name"], "score": c["score"],
                           "deterministic_tier": c["tier"], "notes": c["notes"]}
                          for c in cases])
    result = agent(f"Adjudicate these boundary residents for a {hazard_type} hazard: {payload}")
    plan = result.structured_output
    out = {}
    for d in plan.decisions:
        out[d.resident_name] = {"tier": d.tier, "reason": d.reason, "score": next(
            (c["score"] for c in cases if c["name"] == d.resident_name), 0)}
    for c in cases:
        out.setdefault(c["name"], {"tier": c["tier"], "reason": "deterministic default (agent silent)",
                                   "score": c["score"]})
    return out


def main() -> int:
    from dotenv import load_dotenv
    from supabase import create_client

    load_dotenv()
    fixture = sys.argv[sys.argv.index("--fixture") + 1] if "--fixture" in sys.argv else "data/fixtures/alerts/heat.json"
    with open(fixture, encoding="utf-8") as fh:
        props = json.load(fh).get("properties", {})
    event = props.get("event", "")
    hazard_type = {"Extreme Heat Warning": "heat", "Excessive Heat Warning": "heat",
                   "Heat Advisory": "heat", "Power Outage": "outage"}.get(event, "heat")

    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    sb = create_client(url, key).schema("porchlight")
    residents = sb.table("residents").select("*").execute().data

    t0 = time.time()
    scored = []
    for r in residents:
        s = score_resident(r, hazard_type)
        scored.append({"name": r["name"], "score": s, "tier": deterministic_tier(s),
                       "notes": r.get("notes", "")})
    boundary = [c for c in scored if is_boundary(c["score"])]
    decided = adjudicate(
        boundary, hazard_type,
        os.environ.get("BEDROCK_MODEL_ID", ""), os.environ.get("AWS_REGION", ""))
    final = {}
    for c in scored:
        if c["name"] in decided:
            final[c["name"]] = decided[c["name"]]
        else:
            final[c["name"]] = {"tier": c["tier"], "reason": "deterministic (off-boundary)", "score": c["score"]}
    dt = time.time() - t0

    t1 = sum(1 for v in final.values() if v["tier"] == 1)
    t2 = sum(1 for v in final.values() if v["tier"] == 2)
    t3 = sum(1 for v in final.values() if v["tier"] == 3)
    missing_reasons = [n for n, v in final.items() if not v.get("reason")]
    oxy = [n for n, v in final.items()
           if "oxygen" in next((c["notes"] for c in scored if c["name"] == n), "").lower()]
    oxy_ok = all(final[n]["tier"] == 1 for n in oxy) if hazard_type == "outage" else True
    ok = (not missing_reasons) and oxy_ok and dt < 90
    print(f"tiering {len(residents)} residents -> tier1={t1} tier2={t2} tier3={t3}; "
          f"oxygen tier1 under outage={oxy_ok}; reasons present for every boundary case={not missing_reasons}; "
          f"wall time <90s={dt < 90} ({dt:.1f}s) = {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
