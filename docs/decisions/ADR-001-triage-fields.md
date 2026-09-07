# ADR-001: Triage gains `unclear` status and `quote` field

- Status: accepted
- Date: 2026-09-07
- Context: `agent/models.py` (P-02) defined `Triage.status` as ok/needs_help/medical/unreachable/opted_out with a `reason` field. HAC-27 requires `unclear` (model could not decide — distinct from `unreachable`, which means no reply arrived) and `quote` (the resident's exact words that decided it, for the liability record and evals).
- Decision: add `unclear` to status values and `quote` alongside `reason`. No other model changes.
- Consequences: `agent/triage.py` returns `unclear` + `quote` on ambiguous replies; evals (P-06) assert on `quote`.
