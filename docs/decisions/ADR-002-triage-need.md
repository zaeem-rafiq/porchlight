# ADR-002: Triage `need` values align with HAC-27

- Status: accepted
- Date: 2026-09-07
- Context: `agent/models.py` (P-02) defined `Triage.need` as transport/power/wellness/cooling/none. HAC-27 requires `wellness_check` (not `wellness`) and `other` (bare "2" replies carry no detail).
- Decision: `need` values become none/cooling/transport/power/wellness_check/other.
- Consequences: `agent/triage.py` short-circuits "2" to needs_help/other; P-06 evals assert these values.
