"""People-safety guard: allowlist enforcement (global rules, P-00).

When ROSTER_MODE=synthetic, every phone number in residents, volunteers and
emergency_contacts must be in PHONE_ALLOWLIST. Any other number aborts before
any send. Never text or call outside the allowlist.
"""

from __future__ import annotations


def normalize(phone: str) -> str:
    return "".join(ch for ch in phone.strip() if ch.isdigit() or ch == "+")


def parse_allowlist(raw: str) -> set[str]:
    return {normalize(p) for p in raw.split(",") if p.strip()}


def is_allowed(phone: str, allowlist: set[str]) -> bool:
    return normalize(phone) in allowlist


def assert_allowed(phone: str, allowlist: set[str]) -> None:
    if not is_allowed(phone, allowlist):
        raise PermissionError(f"Refusing send to number outside PHONE_ALLOWLIST: {phone}")


def assert_roster_allowed(phones: list[str], allowlist: set[str], roster_mode: str) -> None:
    if roster_mode == "synthetic":
        for phone in phones:
            assert_allowed(phone, allowlist)
