# Porchlight handoff

## Done

- HAC-24 P-00 DONE, HAC-25 P-01 DONE, HAC-26 P-02 DONE (proofs commented, commits local-only).
- HAC-27 P-03 DONE: all 5 proofs PASS over Telegram transport (ADR-004). Wave 40 sent (1 real); "1"→ok no model; dizzy→medical/cooling/quoted; 3 simulated triaged + ladder on 1-min clock; STOP→opted_out with re-wave real=0. Committed as be0e574. Proof + walkthrough in `docs/proofs/P-03.md`.
- Transport state: SMS blocked both roads (30034 long-code A2P failed; 30032 toll-free needs verification). Toll-free …5152 bought. Telegram bot bound to owner. ADR-003 single-sender; ADR-001/002 triage model fixes. `agent/models.py` protected.
- Outstanding: TFV submission (owner console); Sonnet 5 grant; `git remote add origin` + push.

## Next

- HAC-28 P-04 dispatcher + the one consolidated coordinator ping (needs owner phone for the ping proof; coordinator commands via `COORD ` prefix per ADR-003).

## Anything I must do (needs Zaeem)

- Watch for the toll-free verification approval; SMS wave re-proof runs when it clears.
- P-04 ping will text the owner — reply as instructed when asked.
