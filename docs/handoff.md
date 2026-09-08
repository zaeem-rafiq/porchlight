# Porchlight handoff

## Done

- HAC-24 P-00, HAC-25 P-01, HAC-26 P-02, HAC-27 P-03, HAC-28 P-04 DONE (proofs commented, commits local-only).
- HAC-29 P-05 DONE: Runtime READY + wave accepted/logged; signed webhook → triage stored; interrupt held/resumed across invocations; Memory ACTIVE with retrievable records; SAM valid + trace PNG (15 spans). Committed as 2020321. Proof + walkthrough in `docs/proofs/P-05.md`.
- Transport state: SMS blocked (30034/30032); TFV pending; Telegram loop live. ADR-001..005 current. `agent/models.py` protected.
- Outstanding: TFV approval; Sonnet 5 grant; `git remote add origin` + push; post-hackathon secret rotation (ADR-005.3).

## Next

- HAC-30 P-06 STOPPED after run 2 per one-change rule: 25/24/30/15 (thresholds 27/26/30/27). Change 1 (reason-language) moved status 24→25, need 22→24, judge flat. Judge harness itself is flaky (cases flip J run-to-run untouched). History in evals/results/2026-09-07-run{1,2}.md. Safety file 6/6 green.

## Anything I must do (needs Zaeem)

- Watch for toll-free verification approval; SMS re-proofs run when it clears.
- P-06 needs FAIL-trace labeling after the first full run — I'll stop with the traces.
