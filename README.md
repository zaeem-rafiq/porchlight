# Porchlight

Extreme-weather wellness check-in agent for neighborhood "check on" rosters — Strands + AgentCore, Good Neighbor track.

In a heat wave the people who die are older, alone, and on somebody's list. Porchlight works the list: when an NWS warning drops it texts every vulnerable neighbor, reads what they say back, sends help where it's needed, and calls the coordinator only for the decisions a human has to make.

Second submission; Rebuttal wins every conflict. Freeze Fri 9/11, submit Sun 9/13.

## Status

P-00 pre-flight + bootstrap in progress (HAC-24). See `docs/proofs/P-00.md` for the proof line once it passes.

## Quick start

1. Copy `.env.example` to `.env` and fill every value (see HAC-24 pre-conditions).
2. Create and activate a Python 3.12 venv, then install `requirements.txt`.
3. Run `python scripts/preflight.py` — it exits 0 only when every check passes.

## Safety

`ROSTER_MODE=synthetic` asserts every phone number is in `PHONE_ALLOWLIST`; any other number aborts before any send. Never text or call outside the allowlist. Never call 911 — the escalation ladder ends at the emergency contact with "call 911" guidance. First contact carries "Reply STOP to opt out"; STOP and HELP are honored everywhere. NWS outreach fires only for `DEMO_ZONE` fixtures unless `LIVE_ZONE` is set — it never is during the hackathon.

## Evals

| Run | Status | Need | Quote | Judge |
|---|---|---|---|---|
| 2026-09-07 run 7 | 27/30 | 26/30 | 30/30 | 29/30 |

Triage evals (`evals/replies/cases.json`, 30 adversarial replies) clear every threshold (27/26/30/27). Full history in `evals/results/`; failure modes in `docs/evals.md`.
