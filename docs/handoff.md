# Porchlight handoff

## Done

- HAC-24 P-00 planning: plan at `docs/plans/2026-09-07-1048-feat-porchlight-p00-preflight-plan.md` (implementation-ready).
- HAC-24 marked In Progress in Linear; branch `zaeem/hac-24-p-00-pre-flight-bootstrap-two-twilio-channels-nws-calendar` created from empty root.
- U1 skeleton committed (41962bd): LICENSE, .gitignore, .env.example, requirements, README, `.agents/rules/porchlight.md` (global rules, `trigger: always_on`), docs skeleton.
- U2 code committed (same commit): `agent/safety.py` allowlist guard + `tests/test_safety.py` (2 passed, no live sends) + `scripts/preflight.py` gate.
- Guard proof observed: `pytest tests/test_safety.py -q` → 2 passed.

## Next

- Fill `.env` (user-owned), then run `python scripts/preflight.py` to exit 0, capture the `PROOF P-00:` line to `docs/proofs/P-00.md`, confirm two owner-phone texts, commit as `P-xx: <title> — PROOF PASS`, push, comment proof on HAC-24, mark Done, write 5-line walkthrough, then pick up HAC-25.
- No remote is configured yet — first push will need `git remote add origin <url>` + `git push -u origin <branch>`.

## Anything I must do (needs Zaeem)

- AWS auth done via `aws login` (account 292341338711, region us-east-1) — preflight env gate relaxed in 8cb1a0e, no AWS keys needed in `.env`.
- Supabase DONE (verified): `porchlight` schema exists and is REST-exposed (PGRST205 probe), service key works (`rest_root=200`). PAT/Management-API route abandoned after persistent 403s; SQL-block route used instead.
- Still missing in `.env`: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_NUMBER_A, TWILIO_NUMBER_B, OWNER_PHONE, PHONE_ALLOWLIST, DEMO_ZONE. (`.env` is gitignored, never committed.)
- Confirm the second Twilio number (number B) is purchased (pre-approved, ~$1/month).
