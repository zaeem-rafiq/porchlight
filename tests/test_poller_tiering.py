"""Offline P-02 checks: normalization mapping + deterministic scoring (no network)."""

from agent.poller import EVENT_TYPES, load_protocol, normalize
from agent.tiering import deterministic_tier, is_boundary, score_resident


def test_heat_names_and_outage_map():
    load_protocol()
    for name, kind in [("Extreme Heat Warning", "heat"), ("Excessive Heat Warning", "heat"),
                       ("Heat Advisory", "heat"), ("Extreme Cold Warning", "cold"),
                       ("Winter Storm Warning", "cold"), ("Power Outage", "outage")]:
        assert EVENT_TYPES[name] == kind
    heat = normalize({"id": "x", "properties": {"event": "Excessive Heat Warning",
                                                "headline": "h"}}, "nws:x")
    assert heat is not None and heat["row"].type == "heat"
    assert normalize({"id": "y", "properties": {"event": "Tornado Warning"}}, "nws:y") is None


def test_ruth_tier1_heat_and_oxygen_tier1_outage():
    ruth = {"name": "Ruth Alvarez", "lives_alone": True, "has_ac": False,
            "powered_medical_device": None, "age_band": "75-84", "mobility": "independent"}
    assert deterministic_tier(score_resident(ruth, "heat")) == 1
    elena = {"name": "Elena Vasquez", "lives_alone": True, "has_ac": False,
             "powered_medical_device": "oxygen concentrator", "age_band": "75-84",
             "mobility": "limited"}
    assert deterministic_tier(score_resident(elena, "outage")) == 1
    assert deterministic_tier(score_resident(elena, "heat")) == 1
    low = {"name": "Low Risk", "lives_alone": False, "has_ac": True,
           "powered_medical_device": None, "age_band": "65-74", "mobility": "independent"}
    assert deterministic_tier(score_resident(low, "heat")) == 3
    assert is_boundary(4) and is_boundary(6) and not is_boundary(0)
