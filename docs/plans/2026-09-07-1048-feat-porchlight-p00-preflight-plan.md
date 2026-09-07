---
title: Porchlight P-00 Pre-flight Bootstrap - Plan
type: feat
date: 2026-09-07
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
product_contract_source: ce-plan-bootstrap
execution: code
---

## Goal Capsule

- **Objective:** An empty folder becomes a runnable Porchlight repo whose preflight proves AWS, Bedrock, AgentCore, Supabase, both Twilio channels, NWS, and the allowlist guard before any resident is ever contacted.
- **Means:** Bootstrap repo skeleton plus `scripts/preflight.py` exit-0 gate (KTD2).
- **Authority:** Linear project Porchlight description (global rules) > HAC-24 issue > this plan.
- **Stop conditions:** STOP and ask for `.env` values one at a time when pre-conditions are unmet; BLOCKED with `docs/blockers/P-00.md` after 2 failed attempts or 30 min without passing proof; never send outside `PHONE_ALLOWLIST`; never call 911.
- **Execution profile:** code, Lightweight reclassified to Standard (touches external contract surfaces: env vars, Twilio, NWS).
- **Tail ownership:** `ce-work` owns goal-mode engine choice; returns to LFG.

---

## Product Contract

### Summary

Bootstrap `porchlight/` (MIT, gitignore, venv, packages, `.agents/rules/porchlight.md`, `docs/{proofs,blockers,decisions,media}`) and land a `scripts/preflight.py` that exits 0 only when every external dependency answers and the allowlist guard refuses an outside number.
First commit is pushed. Proof line goes to transcript and `docs/proofs/P-00.md`.

### Problem Frame

Porchlight sends real SMS during the hackathon rehearsal from day one.
Without a pre-flight gate, a missing credential, a wrong Supabase schema, or a single-channel Twilio setup is discovered only when a resident wave fails.
P-00 makes those failures cheap and local, and writes the global safety rules into the repo so every later P-01 through P-08 task inherits them.

### Requirements

**Bootstrap**

- R1. Repo skeleton exists with MIT license, Python 3.12 venv, pinned packages, gitignore, `.env.example`, and `docs/{proofs,blockers,decisions,media}`.
- R2. `.agents/rules/porchlight.md` carries the Linear project global rules verbatim with frontmatter `trigger: always_on`.
- R3. First commit is pushed to the configured remote when a remote exists; local-only commit when no remote is configured.

**Preflight gate**

- R4. `scripts/preflight.py` exits 0 only when all checks pass: AWS identity plus region, Bedrock Converse to `BEDROCK_MODEL_ID`, AgentCore control plane reachable, Supabase REST answers, Twilio number A and number B each send one SMS to `OWNER_PHONE`, NWS `api.weather.gov/alerts/active?zone=<DEMO_ZONE>` answers 200 with `User-Agent` header, Google Calendar token refreshes (WARN-only does not fail the gate).
- R5. `PHONE_ALLOWLIST` guard refuses any number outside the allowlist before any send, per global rules.
- R6. Secrets come only from `.env` locally, never printed; `.env.example` lists every key HAC-24 pre-conditions name without values.
- R7. Proof line `PROOF P-00: aws=PASS bedrock=PASS agentcore=PASS supabase=PASS twilioA=PASS(SM…) twilioB=PASS(SM…) nws=PASS calendar=PASS|WARN allowlist_guard=PASS` is printed and appended to `docs/proofs/P-00.md`; owner phone shows two texts, one per Twilio number.

### Key Decisions

- **Queue scope is HAC-24 through HAC-32 in blocked-by order; HAC-33, HAC-34, HAC-35 are excluded** (session-settled: user-directed — chosen over running the full queue: those three are the user's own). Governs R1, R3.
- **Rebuttal is a pattern reference only; copy `.agents/rules` and helper scripts where useful, never agent code** (session-settled: user-directed — chosen over lifting Rebuttal agent code wholesale: Porchlight is a substantially different second submission). Governs R2.
- **Synthetic roster with allowlist enforcement and observed-only NWS unless `LIVE_ZONE` is set, which never happens during the hackathon** (session-settled: user-directed — chosen over live outreach: people-safety guard). Governs R4, R5, R7.

### Scope Boundaries

- In scope: HAC-24 P-00 only. Repo skeleton, rules file, env example, preflight script, first commit, P-00 proof.
- Out of scope: Supabase schema and seeding (HAC-25), poller and tiering (HAC-26), outreach wave (HAC-27), dispatcher (HAC-28), Runtime and Memory (HAC-29), evals (HAC-30), console (HAC-31), rehearsal and freeze (HAC-32), video, posts, Devpost (HAC-33 through HAC-35).

### Deferred to Follow-Up Work

- HAC-25 through HAC-32 execute in order after this plan lands, each with its own plan artifact.
- Voice-call extra in HAC-32 only when core proofs pass with time to spare.

### Dependencies

- Second Twilio number purchased (pre-approved, about $1/month) before Twilio B check can pass.
- `.env` filled by the user: AWS, `BEDROCK_MODEL_ID`, Supabase (new project or `porchlight` schema, never Rebuttal tables), `TWILIO_*`, `TWILIO_NUMBER_A`, `TWILIO_NUMBER_B`, `OWNER_PHONE`, `PHONE_ALLOWLIST`, `DEMO_ZONE`, `ROSTER_MODE=synthetic`.

### Open Questions

- None blocking. `.env` values are a pre-condition to be collected at execution, not a planning unknown.

### Sources

- Linear project Porchlight description (global rules, schedule, cut order).
- Linear issue HAC-24 description (end-state, proof, turn bound, pre-conditions).
- Linear issues HAC-25 through HAC-32 titles for sequencing; HAC-33 through HAC-35 explicitly excluded.

---

## Planning Contract

### Key Technical Decisions

- KTD1. Bootstrap by hand-authored skeleton, no starter-kit magic (session-settled: user-directed — chosen over Rebuttal code lift: keeps Porchlight identity separate). The skeleton is MIT, `.gitignore`, `.env.example`, venv, `requirements.txt` with `strands-agents`, `strands-agents-tools`, `bedrock-agentcore`, `bedrock-agentcore-starter-toolkit`, `supabase`, `twilio`, `boto3`, `pydantic`, `pyyaml`, `pytest`, `python-dotenv`, `httpx`, `google-api-python-client`, plus `.agents/rules/porchlight.md` and `docs/` skeleton.
- KTD2. Single `scripts/preflight.py` with per-check functions and exit-0 aggregation. Each external (AWS STS, Bedrock Converse, AgentCore control plane, Supabase REST, Twilio A and B, NWS with `User-Agent`, Calendar refresh) is one function returning PASS, FAIL, or WARN; only Calendar WARN is non-fatal. Directional guidance only; implementation resolves SDK call shapes against installed package docs.
- KTD3. Allowlist guard lives in its own importable module so P-01 through P-08 reuse the same gate. `ROSTER_MODE=synthetic` asserts every phone in `residents`, `volunteers`, and `emergency_contacts` is in `PHONE_ALLOWLIST`; any other number aborts before any send. Unit test proves refuse-outside and permit-inside without sending.
- KTD4. Verify Strands and AgentCore APIs against installed package docs before use. No cloud resource beyond one Bedrock call is created by this plan.

### Assumptions

- Working directory `C:\Users\zaeem\Documents\Porchlight` becomes repo root `porchlight/`; `<root>` resolves to `docs` (no `.compound-engineering/config.yaml` present).
- Python 3.12 is available; `python -m venv .venv` succeeds.
- No remote is configured yet; first-commit push follows the no-remote substitution (local-only commit, remote added later).
- `.env` collection happens in `ce-work` via STOP-and-wait; planning does not block on it.

### Sequencing

- U1 then U2 then U3. U2 needs U1 skeleton paths; U3 needs U2 proof artifacts.

---

## Implementation Units

### U1. Repo skeleton plus Porchlight rules

- **Goal:** Empty folder becomes a committable repo with safety rules inherited by every later task.
- **Requirements:** R1, R2.
- **Dependencies:** None.
- **Files:** `LICENSE`, `.gitignore`, `.env.example`, `requirements.txt`, `README.md`, `.agents/rules/porchlight.md`, `docs/proofs/.keep`, `docs/blockers/.keep`, `docs/decisions/.keep`, `docs/media/.keep`.
- **Approach:** Hand-author minimal files. Copy Linear project global rules into `.agents/rules/porchlight.md` with `trigger: always_on` frontmatter. List every HAC-24 key in `.env.example` with empty values. Note Rebuttal `.agents/rules` and helper-script patterns as followable references without copying agent code, per R2.
- **Patterns to follow:** Rebuttal `.agents/rules` shape where useful; otherwise plain minimal Python repo layout.
- **Test scenarios:**
  - Skeleton lists all required paths and each file renders without template leftovers.
  - Rules file contains allowlist guard, 911 prohibition, STOP handling, `DEMO_ZONE` observed-only clause, proof-line contract, blocker contract, and protected paths.
  - `.env.example` names AWS, `BEDROCK_MODEL_ID`, Supabase, `TWILIO_*`, both Twilio numbers, `OWNER_PHONE`, `PHONE_ALLOWLIST`, `DEMO_ZONE`, `ROSTER_MODE` with no secret values.
- **Verification:** Directory listing matches the file list; rules file opens and reads as the project source of truth.

### U2. Preflight gate plus allowlist guard

- **Goal:** One command proves every external dependency and the safety gate.
- **Requirements:** R4, R5, R6.
- **Dependencies:** U1.
- **Files:** `scripts/preflight.py`, `agent/safety.py`, `tests/test_safety.py`.
- **Approach:** Build per-check functions aggregating to exit 0. Calendar WARN does not fail. Guard is importable and called before any Twilio send. Secrets read from `.env` via `python-dotenv`; no secret is printed. SDK shapes verified against installed package docs at implementation time.
- **Execution note:** This is mostly config plus smoke verification; prefer install and runtime smoke proof over unit coverage, except the guard which gets a unit test.
- **Patterns to follow:** Small check-function layout; deferred detail stays in implementation.
- **Test scenarios:**
  - Guard refuses a number outside `PHONE_ALLOWLIST` and permits an inside number without sending.
  - Missing `.env` key produces a named FAIL identifying the key, not a traceback.
  - NWS request carries `User-Agent` and treats non-200 as FAIL.
  - Twilio A and Twilio B each address `OWNER_PHONE`; proof SIDs are captured for the proof line.
  - Calendar refresh failure surfaces as WARN while exit code stays 0 when all else passes.
- **Verification:** `scripts/preflight.py` exits 0 in a filled environment and non-zero with a named failure when a dependency is broken.

### U3. First commit plus proof capture

- **Goal:** Work is durable and Done means every proof is PASS.
- **Requirements:** R3, R7.
- **Dependencies:** U1, U2.
- **Files:** `docs/proofs/P-00.md`, git history.
- **Approach:** Run preflight, append the single PROOF line to `docs/proofs/P-00.md`, commit as `P-00: <title>`, push when a remote exists. Confirm owner phone shows two texts, one per Twilio number.
- **Test scenarios:**
  - Test expectation: none -- commit and proof-capture step with no behavioral change.
- **Verification:** Proof line exists in transcript and in `docs/proofs/P-00.md`; git log shows the commit; push succeeds or reports no-remote local-only.

---

## Verification Contract

| Check | Command or signal | Applies to |
|---|---|---|
| Guard unit test | `pytest tests/test_safety.py` | U2 |
| Preflight gate | `python scripts/preflight.py` exits 0 | U2, U3 |
| Proof line | Transcript plus `docs/proofs/P-00.md` contains `PROOF P-00:` with all PASS and Calendar PASS or WARN | U3 |
| Human confirm | Owner phone shows two texts, one from each Twilio number | U3 |

Quality gates: no secret values in output or files; no send outside `PHONE_ALLOWLIST`; no cloud resource beyond one Bedrock call; turn bound 0.5h / 20 turns is a hard stop.

---

## Definition of Done

- Skeleton, rules file, env example, preflight script, guard, and guard test exist at the paths above.
- Preflight exits 0; proof line is PASS across the board with Calendar PASS or WARN.
- Proof line is in the transcript and in `docs/proofs/P-00.md`; owner phone confirms both Twilio channels.
- First commit exists and is pushed when a remote is configured.
- No Done is marked unless every proof is PASS; failures follow the blocker contract (`docs/blockers/P-00.md`, `BLOCKED P-00`, stop).

---

## Appendix

- LFG run context: HAC-24 first in the HAC-24 through HAC-32 blocked-by chain. HAC-33, HAC-34, HAC-35 are the user's own and are never started by this pipeline.
- Product Contract preservation: new bootstrap plan, no upstream requirements doc to preserve.
- Scoping synthesis (headless): Stated is P-00 bootstrap plus preflight; Inferred bets recorded as Assumptions (repo root, Python 3.12, local-only commit, `.env` collected at execution); Out of scope is P-01 onward.
