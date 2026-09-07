# Porchlight handoff

## Done

- HAC-24 P-00, HAC-25 P-01, HAC-26 P-02, HAC-27 P-03 DONE (proofs commented, commits local-only).
- HAC-28 P-04 DONE: all 4 proofs PASS. Dispatcher matches + volunteer ask/accept (calendar skipped); gate holds via hook interrupt with DB-durable queue; one ping per 15-min window; bare-digit/COORD/A-channel coordinator routing; silence ladder to EC; audit 137 actions; no 911 capability. Committed as 242ce20. Proof + walkthrough in `docs/proofs/P-04.md`.
- Transport state: SMS blocked (30034/30032); TFV pending; Telegram loop live. ADR-001..004 current. `agent/models.py` protected.
- Outstanding: TFV approval; Sonnet 5 grant; `git remote add origin` + push.

## Next

- HAC-29 P-05 AgentCore Runtime (long-running event session), Memory, Observability, Lambda glue. Needs owner phone for proofs; Telegram loop stands in for webhooks until Lambda lands.

## Anything I must do (needs Zaeem)

- Watch for toll-free verification approval; SMS re-proofs run when it clears.
- P-05 proofs will need live replies again — I'll ask when there.
