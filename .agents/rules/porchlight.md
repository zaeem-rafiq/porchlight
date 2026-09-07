---
trigger: always_on
---

# Porchlight — global rules (every issue inherits these)

Source of truth: Linear project "Porchlight" (team Hackathon). Second submission; Rebuttal wins every conflict. Freeze Fri 9/11, submit Sun 9/13.

In a heat wave the people who die are older, alone, and on somebody's list. Porchlight works the list: when an NWS warning drops it texts every vulnerable neighbor, reads what they say back, sends help where it's needed, and calls the coordinator only for the decisions a human has to make. Audience: block associations, senior centers, congregations, mutual-aid groups with a "check on" roster run by one volunteer coordinator.

Substantially different from Rebuttal by design: external alert trigger (`api.weather.gov`), one conversation agent per resident running in parallel, a long-running Runtime session that lasts a hazard day, a group audience with a coordinator on top, and a liability-grade record of who was contacted when. Reuses the patterns (Lambda webhook → Runtime, Twilio two-way gate, Memory, console, evals) — not the code.

Schedule: build Mon 9/7 – Thu 9/10 in the gaps around Rebuttal's Harden queue, freeze Fri 9/11 EOD, video Sat 9/12 after Rebuttal submits, posts + Devpost Sun 9/13. Cut order if it slips: voice calls → Spanish copy → volunteer dispatch (fall back to cooling-center info only) → console polish. Never cut the real-phone rehearsal, the triage evals' first run, or the three posts.

## Global rules

- Repo `porchlight/` (MIT). Python 3.12 venv. Packages: `strands-agents`, `strands-agents-tools`, `bedrock-agentcore`, `bedrock-agentcore-starter-toolkit`, `supabase`, `twilio`, `boto3`, `pydantic`, `pyyaml`, `pytest`, `python-dotenv`, `httpx`, `google-api-python-client`. Copy Rebuttal's `.agents/rules` and helper scripts where useful; do not lift Rebuttal's agent code wholesale.
- People-safety guard: `ROSTER_MODE=synthetic` asserts every phone number in `residents`, `volunteers` and `emergency_contacts` is in `PHONE_ALLOWLIST` (owner numbers + the project's Twilio numbers); any other number aborts before any send. Never text or call outside the allowlist. Never call 911 or any emergency service — the escalation ladder ends at the emergency contact with "call 911" guidance. First contact to any number carries "Reply STOP to opt out"; STOP and HELP are honored everywhere.
- The NWS poller reads real alerts, but outreach fires only for `DEMO_ZONE` fixtures unless `LIVE_ZONE` is set explicitly — it never is during the hackathon.
- Two Twilio numbers = two channels: number A is the coordinator channel, number B is the resident/volunteer channel. Inbound routing is by the To number, so one real phone can play both a resident and the coordinator.
- Secrets only from `.env` locally / AWS Secrets Manager in the cloud; never print a secret value.
- Proof lines `PROOF P-xx: <check> = PASS|FAIL` go to the transcript AND `docs/proofs/P-xx.md`. Done means every proof is PASS.
- Failure handoff: after 2 failed attempts at the same step or 30 min without a passing proof, write `docs/blockers/P-xx.md` (tried, exact error, hypothesis, smallest next step), print `BLOCKED P-xx`, stop. Turn bound is a hard stop.
- Protected paths (all issues): `LICENSE`, `.env*`, `docs/proofs/**`, `docs/blockers/**`, `docs/decisions/**` (append-only), plus the per-issue list; `data/fixtures/**` after P-01; `agent/models.py` after P-02 (changes need an ADR).
- Verify Strands and AgentCore APIs against the installed package docs before using them. Ask before anything that costs more than cents or creates a cloud resource not on the pre-approved list.

## Pre-approved cloud resources (region = AWS_REGION in .env; tag project=porchlight)

One AgentCore Runtime with its IAM execution role and ECR image; one AgentCore Memory; up to 3 Lambda functions with Function URLs and IAM roles; two EventBridge Scheduler schedules (nws_poll, tick); Secrets Manager secrets under porchlight/*; CloudWatch log groups; one S3 bucket only if the P-05 session-manager fallback fires; one additional Twilio phone number. Anything else: ask first.
