# Eval failure modes (P-06, from run history run1–run7)

Observed modes, with the run-7 disposition:

- **missed-medical-cue**: understatement read as fine. Fixed for lightheaded/fever via cooling-primary mapping (03, 25 PASS). Watch: novel understatements.
- **false-medical-figurative**: "killing me lol" / "dying for a cold drink" escalated. Fixed via figurative-language discipline (11, 20 PASS).
- **wrong-language**: triage reasons came back in English for Spanish replies, failing the follow-up language check. Fixed by owner verdict: reasons in the resident's language. Residual: langdetect floor on very short reasons (02 judge N; deterministic, accepted).
- **caregiver-confusion**: none observed failing at run 7 (07, 29 PASS). Keep the caregiver cases in every future run.
- **opt-out-not-honored**: none observed (06, 27 PASS, handler-level STOP intact).
- **need-mismatch (residual)**: 09 neighbor→wellness_check vs other; 22 trust-question→none vs other; 23 deflect→unclear/wellness_check vs needs_help/other. Ambiguous expectations, stable outputs.
- **status-mismatch (residual)**: 04 bare "fine"→ok vs unclear (fixture-suspect); 17 HELP→needs_help vs unclear; 23 deflect→unclear vs needs_help.
- **invented-status**: wrong-number→unreachable (05). Owner-arbitrated: unreachable is correct product behavior there (resident unreachable at this number). Stable since temperature 0.
- **judge-flakiness (harness, fixed)**: model-as-judge flipped verdicts run-to-run. Replaced with deterministic language-ID + length check (change 2). run 7 judge 29/30, sole miss is the short-text floor above.
