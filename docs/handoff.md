# Porchlight handoff

## Done

- HAC-24 P-00, HAC-25 P-01, HAC-26 P-02, HAC-27 P-03, HAC-28 P-04 DONE (proofs commented, commits local-only).
- HAC-29 P-05 DONE: Runtime READY + wave accepted/logged; signed webhook → triage stored; interrupt held/resumed across invocations; Memory ACTIVE with retrievable records; SAM valid + trace PNG (15 spans). Committed as 2020321. Proof + walkthrough in `docs/proofs/P-05.md`.
- Transport state: SMS blocked (30034/30032); TFV pending; Telegram loop live. ADR-001..005 current. `agent/models.py` protected.
- Outstanding: TFV approval; Sonnet 5 grant; `git remote add origin` + push; post-hackathon secret rotation (ADR-005.3).

## Next

- HAC-30 P-06 DONE: run 7 hits 27/26/30/29, all thresholds. Committed as bf15a82. Proof + walkthrough in `docs/proofs/P-06.md`; failure modes in `docs/evals.md`; README table live.
- HAC-31 P-07 DONE: Twilio retired, Telegram sole messaging provider; Next.js standalone container configured for AWS App Runner; Supabase anon RLS verified; simulation drill updates within SLA (28.8s & 6.8s < 90s); Lighthouse 96/100; desktop screenshots verified. Proof + walkthrough in `docs/proofs/P-07.md`. Victory audit confirmed.

## Next

- HAC-32 P-08: Dress rehearsal, reset script, README + diagram, freeze.

## Anything I must do (needs Zaeem)

- Run `aws login` when ready to push ECR container image to AWS App Runner.
- P-08 dress rehearsal runbook (`docs/runbook-demo.md`).
