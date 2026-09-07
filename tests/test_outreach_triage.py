"""Offline P-03 checks: short-circuit, ladder, copy (no network, no sends)."""

from agent.inbound import ResidentAgent, ladder_action
from agent.outreach import compose
from agent.triage import short_circuit


def test_short_circuits_skip_model():
    ok = short_circuit("1")
    assert ok is not None and ok.status == "ok" and ok.need == "none"
    need = short_circuit("2")
    assert need is not None and need.status == "needs_help"
    assert short_circuit("I feel dizzy") is None


def test_ladder_steps():
    silent = {"status": "sent", "attempts": 1, "_sent_min": 0}
    assert ladder_action(silent, 0.5, resend_after=1, unreachable_after=2) is None
    assert ladder_action(silent, 1.0, resend_after=1, unreachable_after=2) == "resend"
    silent2 = {"status": "resent", "attempts": 2, "_sent_min": 0}
    assert ladder_action(silent2, 2.0, resend_after=1, unreachable_after=2) == "flag_unreachable"
    assert ladder_action({"status": "ok", "attempts": 1, "_sent_min": 0}, 99) is None


def test_copy_plain_words_and_stop_line():
    en = {"name": "Ruth Alvarez", "language": "en"}
    text = compose(en, {"en": "Hot.", "es": "Calor."}, first_contact=True)
    assert "Ruth" in text and "STOP" in text and "!" not in text
    again = compose(en, {"en": "Hot.", "es": "Calor."}, first_contact=False)
    assert "STOP" not in again
    agent = ResidentAgent("evt", {"id": "r1", "name": "Ruth Alvarez"})
    assert agent.session_id == "evt:r1"
