# September 14 verification checkpoint

Date: 2026-09-14. Baseline public commit: `e254173f09b23b25d6c64283cef66a2f6cde86c4`. Published fixes: [e7328c1](https://github.com/zaeem-rafiq/porchlight/commit/e7328c14558a874f518ca55197b32d0b35a29fba).

The repaired source is published, migration 006 is applied, and the corrected Devpost copy and additional information were saved. Runtime version 7 and all three Lambda packages are deployed with matching artifact and healthy-state readbacks. The authenticated Telegram webhook is registered. At 23:48 UTC, one synthetic workflow passed through the actual runtime, Bedrock, hosted database and Telegram, with three owner-routed messages and verified cleanup. Inbound test replies were assistant-generated; this does not establish human acceptance or a physical visit. The replacement video is published as an unlisted YouTube video and saved on the published Devpost submission.

This note distinguishes published source, local execution, simulated integrations, historical evidence, and provider deployment.

## Current observations

| Evidence | Observation | Limit |
| --- | --- | --- |
| Integrated offline regression | The full `tests` command below completed with **136 passed, 58 skipped, 2 deselected**, exit 0, after coordinator menu-token binding, volunteer request-ID binding, and the README test correction. | Skipped and deselected integration checks do not establish live provider behavior. |
| Outbound/model/proxy boundary and existing outreach/safety tests | `../porchlight-venv/bin/python -m pytest -q tests/test_boundary_recovery.py tests/test_outreach_triage.py tests/test_safety.py` — **32 passed**, exit 0, after atomic outreach claims were added. | Database, model, and transport responses are substituted in focused tests. Later edits require the affected checks to be rerun. |
| TypeScript check | `./node_modules/.bin/tsc --noEmit --incremental false` from `console` — exit 0 after volunteer request-ID binding. | Compilation does not prove browser interactions or deployment. |
| Console production build | `npm run build -- --webpack` from `console` — exit 0, including TypeScript validation. | Browser interactions and hosting are not established by this build. |
| Local drill tests | `env -i PATH=/opt/homebrew/bin:/usr/bin:/bin PYTHON_DOTENV_DISABLED=1 AWS_EC2_METADATA_DISABLED=true AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../porchlight-venv/bin/python -m pytest tests/test_local_drill.py -q` — **3 passed**, exit 0. | Real handlers run with synthetic database, model, and transport adapters. |
| Supabase JavaScript client against local bridge | Initial readback returned 40 synthetic residents, 0 events, and no client error. | This exercised the local bridge, not hosted Supabase. |
| Actual browser acceptance, 23:18 UTC | Chrome exercised the production Webpack build against the isolated bridge: heat injection, fictional resident reply, menu-bound approval, request-bound acceptance, unauthorized access rejection, and repeated injection. Detailed outcomes appear below. | Database, model, and messaging adapters were simulated. No real Telegram or hosted-database workflow was demonstrated. |
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

The two explicitly deselected cases require unavailable credentials in the isolated test environment. The 58 skipped cases were not executed. The Python environment path above is the review workspace's installed environment; a fresh checkout can use `.venv/bin/python` after installing the existing requirements. The README does not claim that every integration test passed.

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

## Browser acceptance — September 14, 23:18 UTC

The production Webpack build was exercised in Chrome at `http://127.0.0.1:3777` against the isolated local bridge. The visible disclosure stated that model and Telegram adapters were simulated. The following operations returned observed responses:

- Heat injection: HTTP 200, 40 simulated contacts, no real messages.
- Ruth Alvarez, `AC broke, dizzy`: HTTP 200, medical/cooling with the exact quote and `used_model=false`; coordinator case appeared open.
- Current menu code + option 1: HTTP 200, approved; the volunteer request appeared proposed.
- Exact volunteer request ID + Y: HTTP 200, accepted; the board displayed accepted and the audit recorded `volunteer_accepted`.
- Immediate repeated Y: HTTP 429 from the console throttle. This browser action does not prove handler idempotence; focused handler tests cover that boundary.
- Wrong console access key: HTTP 403, `valid access key required`.
- Repeat authorized heat injection: HTTP 200, sent 0, skipped 40. The accepted request and medical status remained visible.

No browser console errors were returned by the inspected error-log surface. The recorded interaction is a local synthetic workflow, not a live Telegram or hosted-database demonstration. Its separate real Bedrock check is described above.

## Provider and delivery state

| Surface | Current checkpoint |
| --- | --- |
| Public source | Fixes published to existing GitHub `main` at [e7328c1](https://github.com/zaeem-rafiq/porchlight/commit/e7328c14558a874f518ca55197b32d0b35a29fba). A fresh remote HEAD readback matched the local commit after the no-force push. |
| Updated AgentCore runtime and three Lambda code packages | **Deployed and exercised live.** Runtime version 7 is READY with the exact prepared artifact; all three Lambda hashes match and their states are Active/Successful. A guarded resume completed the partially deployed release without creating another runtime version. The nonexistent-event tick returned HTTP 200, accepted=true, fired=[]. |
| Telegram authentication configuration and webhook | **Configured and registered.** Three prepared inbound environment fields match readback; the existing Lambda URL is registered with the matching webhook secret and zero pending updates. Invalid console credentials returned HTTP 403. The drill used authenticated console calls, not human Telegram replies, for inbound commands. |
| Current Bedrock model and fixed evaluation | **One real Sonnet 4.5 triage call verified at 22:54 UTC.** Fixed evaluation not rerun; no current accuracy score asserted. |
| Owner-only real workflow drill | **Passed at 23:48 UTC.** Forty hosted contacts, one real owner outreach plus 39 simulated routes, actual model medical/cooling triage, coordinator approval before dispatch, and a request-bound accepted response. Three real Telegram provider message IDs. Inputs were assistant-generated. Cleanup closed the event, released its reservation and disabled the temporary volunteer. [Sanitized live receipt](evidence/deadline-live-workflow.json). |
| Database migration 006 | **Applied to the existing database; all three additive unique index definitions verified.** This establishes the constraints, not a completed live application workflow. |
| Next.js console | Production build and local browser acceptance verified as described above. No accessible public hosted console is claimed. |
| Devpost submission text | Corrected public copy saved at **23:09:41 UTC**; additional information saved at **23:14 UTC**. The submission readback showed **5 of 5 steps complete and submitted**. Version 5 saved the replacement video at **23:26:02 UTC**; a fresh API readback confirmed the new video URL, published state, and preserved submission. |
| Replacement demo video | [Revised Porchlight demo](https://www.youtube.com/watch?v=N54tBdeevWo) is **published Unlisted**. The **1:56.5**, 1920×1080, 30 fps H.264 video has no audio and uses actual local UI recording. Cut-boundary inspection and independent full decoding completed without errors. YouTube copyright and Community Guidelines checks completed with no issues. Watch-page playback advanced to 1:08 and the corrected Devpost embed to 1:07. This does not establish a full watch-through of the hosted copy. |

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
