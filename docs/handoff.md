# Porchlight handoff

## Done

- HAC-24 P-00 DONE: full PROOF PASS exit 0, committed as 7b3a932 on `zaeem/hac-24-...` (local-only, no remote). Proof + walkthrough in `docs/proofs/P-00.md`.
- HAC-25 P-01 DONE: triple PROOF PASS (40/5/3/1/2, 40/40 allowlisted 1 real, reset-twice identical), committed as 688c700 + psycopg pin c1fbf9b. Proof + walkthrough in `docs/proofs/P-01.md`.
- HAC-26 P-02 DONE: live poll HTTP 200 with 2 alerts observed_only; inject dedupe 1 then 1 dupe; heat tier1=15/tier2=10/tier3=15 in 38s; outage tier1=16 with oxygen tier1 in 39s. Committed as 36d8f71. Proof + walkthrough in `docs/proofs/P-02.md`.
- Decisions: Bedrock = Sonnet 4.5 inference profile (Sonnet 5 not granted); AWS via login; Supabase schema REST-exposed via SQL block (PAT route abandoned); `agent/models.py` now protected (ADR for changes).
- Outstanding (non-blocking): enable Sonnet 5 in Bedrock Model access when convenient; `git remote add origin` + push before sharing.

## Next

- HAC-27 P-03 outreach wave + per-resident conversation agents (needs owner REAL phone for proofs — STOP condition; never simulate owner replies).

## Anything I must do (needs Zaeem)

- Nothing blocking right now. HAC-27+ proofs need the owner real phone: texts will arrive, reply as instructed, and work continues.
