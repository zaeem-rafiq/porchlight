# Porchlight — Judging Keep-Alive & Operational Health Log

This document tracks system health checks and scheduled state resets for Porchlight throughout the hackathon judging period (September 14, 2026 – October 8, 2026).

---

## Operating Protocol

1. **Automated Daily Reset**: An AWS EventBridge schedule triggers `scripts/reset_demo.py` daily at 04:00 UTC to close expired mock hazards, purge dynamic records, and idempotently re-seed 40 synthetic residents, 5 volunteers, and 3 cooling centers.
2. **Weekly Health Check**: Validates AgentCore Runtime (`READY`), Lambda Function URLs (`3/3`), Next.js Console (`200 OK`), and Telegram Bot API (`getMe OK`).
3. **Emergency Recovery Runbook**: If a live health check fails during judging, consult `docs/runbook-demo.md` and execute `python scripts/reset_demo.py`.

---

## Health Check Log

| Date / Timestamp (UTC) | Action | Runtime Status | Lambdas | Console HTTP | Telegram API | Result | Verified By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **2026-09-14 21:04 UTC** | **Initial Hackathon Submission Baseline** | `READY` | `3/3` | `200` | `OK (@porchlight_checkon_bot)` | **PASS** | Autonomous System |
| *2026-09-21 12:00 UTC* | Scheduled Week 1 Review | Scheduled | — | — | — | *Pending* | EventBridge Monitor |
| *2026-09-28 12:00 UTC* | Scheduled Week 2 Review | Scheduled | — | — | — | *Pending* | EventBridge Monitor |
| *2026-10-05 12:00 UTC* | Scheduled Week 3 Review | Scheduled | — | — | — | *Pending* | EventBridge Monitor |
| *2026-10-08 23:59 UTC* | Judging Period Closeout | Scheduled | — | — | — | *Pending* | EventBridge Monitor |

---

## Scheduled Reset Configuration

- **Schedule Name**: `porchlight-daily-reset`
- **Target**: Lambda `PorchlightResetDemo` / AgentCore Runtime maintenance task
- **Cron Expression**: `cron(0 4 * * ? *)`
- **Status**: Enabled and active through October 8, 2026
