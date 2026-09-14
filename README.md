# Porchlight

**Turn an extreme-heat check-in roster into a coordinator's next action.**

Porchlight is a hackathon prototype for neighborhood groups, senior centers, and other organizations that already know whom to check on during dangerous heat. It prioritizes a roster, requests a check-in, interprets free-text replies with Strands Agents, and holds assistance requests for a human coordinator.

The demonstration uses **40 synthetic residents**. In the configured Telegram sandbox, only the owner's allowlisted identity receives real messages; other roster messages are recorded as simulated. The local drill described below simulates **all** database, model, and messaging integrations. Neither mode establishes a real resident pilot or emergency-response readiness.

## The complete loop

1. An NWS alert or a labeled heat-drill fixture enters the Python runtime.
2. Deterministic vulnerability scoring orders residents into three outreach tiers. An existing contact for the same event is preserved, so a repeated alert does not restart a completed check-in.
3. `1` means OK and `2` means help without a model call. `STOP` and re-enrollment commands are handled in code.
4. Free-text replies use a Strands `Agent` with structured `Triage` output: status, need, confidence, reason, and a verbatim quote. Code rejects unsupported values, invalid confidence, and invented quotes. An unavailable or invalid model response becomes `unclear` for coordinator review.
5. Medical, help, and unclear replies enter a durable database queue. A coordinator message presents specific cases. A reply must identify the current menu and selected option before an assistance request proceeds.
6. The coordinator can ask a volunteer or take responsibility for the case. An authenticated volunteer replies `Y <request ID>` or `N <request ID>` so the response updates the request they reviewed. Declines return the case to coordinator attention.
7. Stored timestamps drive the retry and medical-silence ladders. The console shows contact state and the audit timeline; transport failures remain failures.

The supported demonstration focuses on **extreme heat**. The repository recognizes other event types, but its outreach wording and resource choices are not validated for every hazard.

## Where Strands and AWS fit

| Component | Current role |
| --- | --- |
| Strands Agents and `BedrockModel` | Classify an individual free-text reply into the validated triage schema. A live Sonnet 4.5 call was verified on one fictional reply; model selection comes from `BEDROCK_MODEL_ID`. |
| Amazon Bedrock AgentCore Runtime | Hosts the Python entrypoint and its action handlers when deployed. Current deployment verification is tracked separately below. |
| Lambda and EventBridge | Provide webhook, weather-poll, and timer adapters. Configuration is not evidence that a schedule or deployment has run successfully. |
| Supabase PostgreSQL | Stores contacts, coordinator decisions, dispatches, escalations, and audit events. Conditional state changes and uniqueness constraints limit duplicate actions. |
| Telegram | Carries messages to the explicitly configured owner chat in the synthetic sandbox. |
| Next.js console | Displays roster state and provides access-key-protected drill controls. A local console is reproducible; no publicly hosted console is claimed here. |

The production coordinator gate is **ordinary deterministic code backed by persisted records**. It does not depend on a Strands interrupt/resume demonstration. A parallel-triage helper, optional hook, and memory-related files remain in the repository, but the demonstrated workflow does not establish 40 concurrent agents, persistent AgentCore Memory use, or Google Calendar completion.

## Evidence and limits

See [September 14 verification](docs/deadline-verification.md) for exact commands, observations, omissions, and deployment state. The most useful current checks exercise the actual handlers through distressed reply, coordinator choice, volunteer response, repeated requests, and failure cases with explicitly substituted external adapters.

At 22:54 UTC on September 14, the current `triage_reply` function made a real Strands/Bedrock call using `us.anthropic.claude-sonnet-4-5-20250929-v1:0`. The fictional reply `AC broke, dizzy` returned `medical` / `cooling` with the exact quote and `used_model_call=true`. [Sanitized result](docs/evidence/deadline-real-triage.json). This verifies one model integration call; it is not an accuracy benchmark or proof of the deployed runtime.

Historical [September 7 evaluations](evals/results/2026-09-07-run7.md) recorded 27/30 status matches, 26/30 need matches, and 30/30 quote matches on a fixed synthetic reply set. These are **historical results from an earlier implementation**, not scores for the current stricter validation or current model configuration. [Historical failure notes](docs/evals.md) are retained unchanged. The runner's exit code alone does not establish that its score thresholds passed.

Known boundaries:

- No real resident pilot, measured response-time improvement, or validated clinical triage is claimed.
- A matching quote proves containment in the reply; it does not prove the model's interpretation is correct.
- Resource selection uses configured records. Opening hours, transport availability, and the actual visit require human confirmation.
- The application does not call emergency services. Its silence message asks the designated contact to check on the resident and seek emergency help if needed.
- Failed or ambiguous delivery reservations require operator recovery. They are not automatically replayed as if delivery were known to have failed.
- Database audit records are operational history, not a certified immutable or complete evidence log. Anonymous board access is for the synthetic demonstration; real personal data needs a separate access and privacy design.

## Reproduce the local synthetic drill

Requires Python 3.12 and Node.js 22 with npm. From a fresh checkout:

```bash
git clone https://github.com/zaeem-rafiq/porchlight.git
cd porchlight
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm ci --prefix console
```

In one terminal:

```bash
.venv/bin/python scripts/local_drill.py
```

In a second terminal, start the console with the local adapter explicitly selected:

```bash
cd console
LOCAL_DRILL=1 \
NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:8765 \
NEXT_PUBLIC_SUPABASE_ANON_KEY=local-drill \
SUPABASE_URL=http://127.0.0.1:8765 \
SUPABASE_ANON_KEY=local-drill \
FUNCTION_URL=http://127.0.0.1:8765 \
CONSOLE_KEY=local-drill \
npm run dev
```

Open [the local console](http://127.0.0.1:3000) and [captured messages](http://127.0.0.1:8765/drill/outbox). Enter `local-drill` as the access key; it is a public local fixture, not a production credential.

1. Inject the heat fixture.
2. Select a synthetic resident and submit `I feel dizzy`.
3. Read the captured coordinator menu and use its menu code and option in the console.
4. Copy the resulting request's ID into **Volunteer request ID**, then choose **Volunteer Y**; inspect the dispatch and audit state. On Telegram, the equivalent reply is `Y <request ID>`; a bare `Y` or `N` is rejected.

The local fixture recognizes the demonstration distress phrases. It does not call Bedrock. The bridge keeps its database in memory, captures outbound messages, and blocks external socket connections. Restarting it resets the drill. The console makes loopback requests to this bridge.

## Tests and operational setup

Run focused checks without provider credentials:

```bash
.venv/bin/python -m pytest -q tests/test_boundary_recovery.py tests/test_workflow_recovery.py tests/test_local_drill.py
cd console
npx tsc --noEmit
npm run build -- --webpack
```

Commands are reproduction instructions; recorded results and any excluded checks belong in the [verification note](docs/deadline-verification.md).

Real integrations require a separate, explicitly configured sandbox: an AWS runtime and Bedrock model, a Supabase schema with the applicable migrations, a Telegram bot and owner chat, and an explicit `PHONE_ALLOWLIST`. `CONSOLE_KEY` and `FUNCTION_URL` must be configured; the console will not borrow a server key for an unauthenticated caller or fall back to a hard-coded cloud endpoint. Never put those credentials in the repository or public demonstration.

`reset_demo.py` changes the configured database. It is not a read-only health check or a prerequisite for the isolated local drill. Inspect deployment and reset scripts, select the intended environment, and verify their actual output before using them. Additive migration `006_dispatch_escalation_uniqueness.sql` aborts on conflicting records rather than deleting them.

## License

[MIT](LICENSE).
