"""Allowlist guard unit tests (P-00, no live sends)."""

from agent.safety import assert_allowed, assert_roster_allowed, is_allowed, parse_allowlist


def test_refuses_number_outside_allowlist():
    allowlist = parse_allowlist("+15550001111, +15550002222")
    assert is_allowed("+15550001111", allowlist) is True
    assert is_allowed("+19999999999", allowlist) is False
    try:
        assert_allowed("+19999999999", allowlist)
    except PermissionError:
        pass
    else:
        raise AssertionError("expected PermissionError for outside number")


def test_permits_inside_number_without_sending():
    allowlist = parse_allowlist("+15550001111")
    assert_allowed("+15550001111", allowlist)
    assert_roster_allowed(["+15550001111"], allowlist, "synthetic")


"""P-06 safety invariants (pure predicates over drill state, no sends)."""


def _tier1_closed_early(contacts):
    return [c for c in contacts
            if c.get("tier") == 1 and c.get("status") in ("ok", "closed") and c.get("attempts", 0) < 2]


def _medical_unresolved(triage_outcomes, decisions, escalations):
    return [t for t in triage_outcomes
            if t.get("status") == "medical"
            and t.get("resident") not in decisions | escalations]


def _volunteer_double_booked(dispatches):
    seen = {}
    for d in dispatches:
        if d.get("status") != "accepted":
            continue
        if d.get("volunteer") in seen:
            return True
        seen[d.get("volunteer")] = d.get("window")
    return False


def test_tier1_never_closed_without_two_attempts():
    ok_state = [{"tier": 1, "status": "ok", "attempts": 2},
                {"tier": 2, "status": "ok", "attempts": 1}]
    assert _tier1_closed_early(ok_state) == []
    bad_state = [{"tier": 1, "status": "ok", "attempts": 1}]
    assert len(_tier1_closed_early(bad_state)) == 1


def test_medical_always_decided_or_escalated():
    assert _medical_unresolved([{"status": "medical", "resident": "Mabel"}],
                               {"Mabel"}, set()) == []
    assert len(_medical_unresolved([{"status": "medical", "resident": "Mabel"}],
                                   set(), set())) == 1
    assert _medical_unresolved([{"status": "medical", "resident": "Mabel"}],
                               set(), {"Mabel"}) == []


def test_no_volunteer_double_booking():
    assert _volunteer_double_booked(
        [{"volunteer": "Marcus", "status": "accepted", "window": "w1"}]) is False
    assert _volunteer_double_booked(
        [{"volunteer": "Marcus", "status": "accepted", "window": "w1"},
         {"volunteer": "Marcus", "status": "accepted", "window": "w1"}]) is True
    assert _volunteer_double_booked(
        [{"volunteer": "Marcus", "status": "proposed", "window": "w1"},
         {"volunteer": "Marcus", "status": "accepted", "window": "w1"}]) is False


def test_allowlist_guard_rejects_outside_number():
    allowlist = parse_allowlist("+15550001111")
    assert is_allowed("+19999999999", allowlist) is False
    assert_roster_allowed(["+15550001111"], allowlist, "synthetic")
