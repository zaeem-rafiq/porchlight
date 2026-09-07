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
