# September 14 verification checkpoint

Date: 2026-09-14. Baseline public commit: `e254173f09b23b25d6c64283cef66a2f6cde86c4`.

This note separates local execution, simulated integrations, historical evidence, and current deployment verification. It is a checkpoint for work on `codex/porchlight-deadline-fixes`, not a claim that the updated package has been deployed or posted.

## Current observations

| Evidence | Observation | Limit |
| --- | --- | --- |
| Integrated offline regression | The full `tests` command below completed with **136 passed, 58 skipped, 2 deselected**, exit 0, after coordinator menu-token binding, volunteer request-ID binding, and the README test correction. | Skipped and deselected integration checks do not establish live provider behavior. |
| Outbound/model/proxy boundary and existing outreach/safety tests | `../porchlight-venv/bin/python -m pytest -q tests/test_boundary_recovery.py tests/test_outreach_triage.py tests/test_safety.py` — **32 passed**, exit 0, after atomic outreach claims were added. | Database, model, and transport responses are substituted in focused tests. Later edits require the affected checks to be rerun. |
| TypeScript check | `./node_modules/.bin/tsc --noEmit --incremental false` from `console` — exit 0 after volunteer request-ID binding. | Compilation does not prove browser interactions or deployment. |
| Console production build | `npm run build -- --webpack` from `console` — exit 0, including TypeScript validation. | Browser interactions and hosting are not established by this build. |
| Local drill tests | `env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHON_DOTENV_DISABLED=1 AWS_EC2_METADATA_DISABLED=true AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../porchlight-venv/bin/python -m pytest tests/test_local_drill.py -q` — **3 passed**, exit 0. | Real handlers run with synthetic database, model, and transport adapters. |
| Supabase JavaScript client against local bridge | Readback returned 40 synthetic residents, 0 events, and no client error. | This exercised the local bridge, not hosted Supabase. |
| Patch whitespace check | `git diff --check` — exit 0 after the boundary/outreach changes. | Not a correctness test. |
| Real Strands/Bedrock triage, 22:54 UTC | The current local `triage_reply` function called `us.anthropic.claude-sonnet-4-5-20250929-v1:0` for fictional input `AC broke, dizzy`: `used_model_call=true`, `medical` / `cooling`, confidence 0.95, exact quote. The invoking assertion completed with exit 0. [Sanitized result](evidence/deadline-real-triage.json). | One provider integration check. No fixed evaluation, deployed-runtime verification, or real resident outcome. |

Exact integrated command, run from the repository root:

```bash
env -i PATH=/opt/homebrew/bin:/usr/bin:/bin \
PYTHON_DOTENV_DISABLED=1 AWS_EC2_METADATA_DISABLED=true \
AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null \
../porchlight-venv/bin/python -m pytest -q tests \
-k 'not telegram_messaging_integration and not out_of_bounds_residents_and_invalid_ops'
```

The two explicitly deselected cases require unavailable credentials in the isolated test environment. The 58 skipped cases were not executed. The Python environment path above is the review workspace's installed environment; a fresh checkout can use `.venv/bin/python` after installing the existing requirements. Browser acceptance remains unverified at this checkpoint. The README does not claim that every integration test passed.

The default Turbopack build did not complete in this sandbox because of font/process errors. The Webpack build above completed successfully. The failed build has not been attributed to an application defect.

The README coverage test was updated to require the audience, implemented components, safety boundaries, runnable local instructions, historical/current evidence distinction, and license. It no longer requires a particular opening sentence or claims about unverified sponsor features. `tests/test_p08_rehearsal_artifacts.py::test_readme_specification_coverage` passed after that correction; no runtime assertions were weakened.

## Behavior covered by focused checks

- Disallowed phone and chat recipients are rejected before the transport is invoked.
- Invalid or zero Telegram message results cannot become `TG-0` success.
- A whole outreach wave validates its selected recipients before the first send.
- Atomic contact reservations prevent repeated waves from overwriting triage or sending again; a database uniqueness conflict does not send.
- Failed initial delivery leaves `send_failed`, zero confirmed attempts, and no successful outbound timestamp.
- Invalid triage enums, out-of-range/nonfinite confidence, and invented or empty quotes require coordinator review.
- Explicit `1` and `2` skip the model; grounded model output follows the normal path.
- Coordinator commands identify the reviewed menu with `COORD <menu code> <number>`; old or missing menu codes are rejected. Volunteer replies identify the reviewed request with `Y <request ID>` or `N <request ID>`; the console sends the same ID with its choice.
- The actual TypeScript proxy rejects missing/wrong caller keys and missing destination configuration before a stub upstream call; the request body cannot override the inbound operation.

## Local drill boundary

`scripts/local_drill.py` uses the application's Lambda/runtime handlers with an in-memory database, a small fixture classifier, and captured outbound messages. Its bridge binds to loopback, clears provider configuration inside the drill context, and blocks external socket connections. Its model adapter recognizes fixed demonstration phrases. No Bedrock invocation or Telegram delivery is established by a local drill recording.

The browser UI connects to the bridge through explicit local URLs. The public `local-drill` access key belongs only to that isolated fixture. It is not an operational credential.

## Provider and delivery state

| Surface | Current checkpoint |
| --- | --- |
| Updated AgentCore runtime | **Not yet verified live in this note.** A provider resource reporting READY alone does not prove execution of the changed handlers. |
| Current Bedrock model and fixed evaluation | **One real Sonnet 4.5 triage call verified at 22:54 UTC.** Fixed evaluation not rerun; no current accuracy score asserted. |
| Owner Telegram delivery and response | **Not yet verified for the updated package in this note.** |
| Database migration 006 | Prepared; application to a real database is not asserted here. |
| Public Next.js console | No accessible hosted deployment is established here. Local execution is separate. |
| Devpost replacement copy, repository publication, or media upload | Prepared artifacts do not establish publication or submission. |

## Historical evidence

The files under `evals/results/` and older `docs/proofs/` preserve their original observations and claims. The September 7 run-7 file reports 27/30 status matches, 26/30 need matches, 30/30 quote matches, and 29/30 deterministic language/length checks. These results belong to the earlier implementation and evaluation contract. They must not be presented as the updated model's score or as evidence of real resident outcomes.

The current schema rejects `unreachable` as a classification for a received reply; silence is handled separately. Some historical fixture expectations and direct-triage keyword cases therefore need explicit reconciliation before a current evaluation can be compared fairly. Do not edit old result files to make them match newer behavior.

## Remaining limits and recovery

- Real resident use, clinical accuracy, dispatch completion, and measurable coordinator benefit remain unproven.
- Matching a quote to the reply does not establish that the classification is correct.
- Conditional claims and database uniqueness reduce duplicate work; they do not establish exactly-once delivery across a provider timeout or process interruption.
- `sending` or failed delivery records require deliberate operator recovery. A duplicate hazard invocation does not automatically retry an ambiguous send.
- A configured cooling center is not proof it is open or suitable. Confirm availability before arranging a visit.
- Historical architecture diagrams may show optional or incomplete integrations. The README's current implementation description supersedes those architectural claims.
