# ADR-005: P-05 platform findings (sessions, secrets, packaging)

- Status: accepted
- Date: 2026-09-07
- Context: AgentCore sessions, runtime secrets, and CodeZip packaging behaved differently than assumed.
- Decisions:
  1. Interrupt state lives in `gate_pending` (Supabase), not in any session manager. The P-05 fallback (S3SessionManager for session state) did not fire: platform `runtimeSessionId` works, and no S3 bucket was created.
  2. Runtime secrets load from Secrets Manager `porchlight/app` into `os.environ` at startup (`agent/app.py:get_config`), so all existing modules work unchanged in cloud and local.
  3. The AgentCore CLI ships the whole code-location tree including `.env` (no ignore support found). Mitigation: move `.env` out of the tree for every deploy and restore immediately after. Follow-up after the hackathon: rotate Twilio Auth Token and Supabase service key (both were inside older ECR assets; private account boundary, no known exposure).
  4. `BedrockAgentCoreApp` requires the `app.run()` main guard or workers never start (found via init-timeout diagnosis).
