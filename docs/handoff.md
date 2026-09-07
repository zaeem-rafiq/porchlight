# Porchlight handoff

## Done

- HAC-24 P-00 DONE (Linear marked Done, proof commented): full PROOF PASS, exit 0, committed as 7b3a932 on `zaeem/hac-24-p-00-pre-flight-bootstrap-two-twilio-channels-nws-calendar` (local-only, no remote configured). Proof + 5-line walkthrough in `docs/proofs/P-00.md`.
- Decisions: Bedrock = Sonnet 4.5 inference profile (Sonnet 5 not granted); AWS via login; Supabase `porchlight` schema REST-exposed via SQL block (PAT route abandoned).
- Outstanding (non-blocking): enable Sonnet 5 in Bedrock Model access when convenient; `git remote add origin` + push before sharing.

## Next

- HAC-25 P-01 (pre-condition P-00 PASS met): schema migrate + seed 40/5/3, protocol row, 2 fixtures; proofs on counts, allowlist, idempotent reset. Placeholders = fictional 555 numbers to append to PHONE_ALLOWLIST (safe, unassigned range).

## Anything I must do (needs Zaeem)

- AWS auth done via `aws login` (account 292341338711, region us-east-1) — preflight env gate relaxed in 8cb1a0e, no AWS keys needed in `.env`.
- Supabase DONE (verified): `porchlight` schema exists and is REST-exposed (PGRST205 probe), service key works (`rest_root=200`). PAT/Management-API route abandoned after persistent 403s; SQL-block route used instead.
- Still missing in `.env`: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_NUMBER_A, TWILIO_NUMBER_B, OWNER_PHONE, PHONE_ALLOWLIST, DEMO_ZONE. (`.env` is gitignored, never committed.)
- Confirm the second Twilio number (number B) is purchased (pre-approved, ~$1/month).
