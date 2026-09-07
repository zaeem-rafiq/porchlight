"""Offline P-01 roster checks (no DB, no sends)."""

import json
import os

from seeds.residents import ROSTER
from seeds.support import PROTOCOL_YAML, RESOURCES, VOLUNTEERS


def test_roster_counts_and_ruth_first():
    assert len(ROSTER) == 40
    assert ROSTER[0][0] == "Ruth Alvarez"
    assert len(VOLUNTEERS) == 5
    assert len(RESOURCES) == 3


def test_roster_variety_and_eval_cases():
    langs = {r[1] for r in ROSTER}
    assert langs == {"en", "es"}
    notes = " ".join(r[8] for r in ROSTER)
    assert "oxygen concentrator" in notes
    assert "answers voice calls" in notes
    assert "Replies 'fine' to everything" in notes
    channels = {r[7] for r in ROSTER}
    assert channels == {"sms", "call"}


def test_protocol_and_fixtures_present():
    assert "retry_ladder" in PROTOCOL_YAML and "quiet_hours" in PROTOCOL_YAML
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data", "fixtures", "alerts")
    for name in ("heat.json", "outage.json"):
        with open(os.path.join(base, name), encoding="utf-8") as fh:
            alert = json.load(fh)
        assert alert["type"] == "Feature"
        assert alert["properties"]["event"] in ("Extreme Heat Warning", "Power Outage")
    with open(os.path.join(base, "heat.json"), encoding="utf-8") as fh:
        heat_raw = fh.read()
    assert "ARZ001" in heat_raw or "Benton" in heat_raw
