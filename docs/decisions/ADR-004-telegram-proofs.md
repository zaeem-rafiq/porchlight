# ADR-004: Telegram transport for P-03+ proofs pending toll-free verification

- Status: accepted
- Date: 2026-09-07
- Context: US carrier SMS has no unapproved road (10DLC hard block 30034 on long codes; 30032 block on unverified toll-free). Toll-free verification is submitted/in flight; A2P brand path failed. Proofs need a real two-way phone loop today.
- Decision (user-directed, chosen over WhatsApp sandbox): run the live conversation proofs over a Telegram bot. Same copy, same `handle_inbound` core, same triage agents; only the edge adapter differs (Telegram chat bound to OWNER_PHONE identity). SMS code path stays intact and the wave-receipt proof re-runs on SMS the moment TFV clears.
- Consequences: `agent/telegram.py` edge adapter + `TELEGRAM_BOT_TOKEN`/`TELEGRAM_OWNER_CHAT_ID` in `.env`. Proof file records the transport deviation honestly. No safety rule changes: owner identity binding is 1:1, placeholders stay simulated.
