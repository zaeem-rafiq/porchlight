# September 14 deadline recovery

Objective: replace unsupported completion claims with an accurate submission and demonstrate the smallest complete synthetic check-in and coordinator workflow before 00:00 UTC September 15.

Baseline: public commit e254173f09b23b25d6c64283cef66a2f6cde86c4. Work branch: codex/porchlight-deadline-fixes. No unrelated working-tree changes at start.

## Work sequence and ownership

1. Workflow agent: resident reply -> durable coordinator decision -> volunteer request -> authenticated volunteer response -> accepted dispatch; real elapsed retry timing and idempotent silence escalation.
2. Boundary agent: outgoing allowlist and delivery errors, model-output validation, console operator authentication.
3. Health agent: provider-backed health checks and isolated full-test environment.
4. Root: database constraints, integration review, README/submission correction, a captured synthetic demonstration, and delivery verification.

Independent agents own disjoint source files. Root integrates and commits only task-owned changes.

## Acceptance

- A runnable offline flow uses real handlers with explicitly fake database/model/transport boundaries, including approval, volunteer response, repeat requests, and failure cases.
- Actual phone/cloud verification is separately identified and requires restored access and an authorized owner-only drill.
- No unauthenticated simulator mutation, unallowlisted outgoing message, or failed-send success claim.
- Retry and medical silence use stored timestamps; repeat ticks do not create duplicate effects.
- Health checks cannot turn configuration or unavailable provider access into a live PASS.
- Correct public project identity and URLs; honest synthetic/replay labels; no unsupported Calendar, concurrency, memory, safety, or impact claims.
- Relevant tests, full available suite, console build and interactive acceptance, final diff review.

## Delivery and recovery

At 23:08 UTC, the owner directed completion within 30 minutes after the scoped delivery proposal. Migration 006 applied and all three additive indexes were verified. The corrected Devpost write-up was published at 23:09:41 UTC; replacement media is in progress. Cloud code deployment is pending automatic approval review. No real Telegram drill messages have been sent at this checkpoint. Preserve historical proof files; new evidence supersedes old claims rather than rewriting history.

Deployment order if authorized: inspect existing state and snapshot synthetic data -> apply additive uniqueness constraints (abort on conflicting existing rows) -> deploy compatible backend -> deploy console -> exercise owner-only drill -> publish verified source and corrected demo/submission. On failure keep the existing submission, report incomplete verification, and roll back only task-owned deployments using saved prior versions.

AWS authentication is restored. Final integrated checks: 136 passed, 58 skipped, 2 credential-dependent checks deselected; production Webpack build passed. Rollback code/configuration and synthetic database snapshots are stored privately outside the repository. The public console and bonus-story URLs do not resolve; they are removed from corrected submission claims. Browser acceptance and replacement recording are in progress; cloud code and authenticated webhook remain pending approval review.
