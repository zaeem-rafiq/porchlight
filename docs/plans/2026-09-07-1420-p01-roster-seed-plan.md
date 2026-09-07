# P-01 implementation plan (short artifact)

## Goal

`porchlight` schema holds a believable synthetic roster (40 residents, 5 volunteers, 3 cooling centers, 1 protocol row) plus 2 alert fixtures, seeded idempotently; every phone allowlisted.

## Units

- U1. Migration SQL `db/migrations/001_porchlight_schema.sql`: 8 tables in `porchlight` schema + grants (usage/tables/sequences/default privileges to anon, authenticated, service_role). Applied once by owner in SQL Editor (Management API token lacks rights; REST cannot DDL).
- U2. Seed data `seeds/*.py` + `scripts/seed.py --reset`: delete in FK order, insert, print proof lines. Ruth Alvarez = OWNER_PHONE (tier 1, 81, alone, no AC); 39 placeholders from fictional 555-01XX range appended to PHONE_ALLOWLIST in `.env` (append-only, disclosed).
- U3. Fixtures `data/fixtures/alerts/heat.json` (Extreme Heat Warning, ARZ001, NWS shape) + `outage.json` (synthetic outage event).
- U4. Offline test `tests/test_roster.py` (counts, Ruth first, allowlist-format, eval-case residents present) + live seed-twice verification.

## Proofs

- `PROOF P-01: residents=40 volunteers=5 resources=3 protocol=1 fixtures=2 = PASS`
- `PROOF P-01: allowlist check — 40/40 resident phones allowlisted, 1 real (OWNER_PHONE) = PASS`
- `PROOF P-01: seed --reset twice → identical row counts = PASS`

## Risks

- Seed via REST needs schema exposed (done P-00) + grants (in migration). If seed hits PGRST205, grants/exposure are the cause, not data.
