"""Adversarial Row-Level Security (RLS) and Permission Boundary Test Suite.

Empirically tests Supabase anonymous access across all porchlight schema tables:
1. Anonymous SELECT: succeeds with HTTP 200 and reads data cleanly across all tables.
2. Anonymous INSERT: strictly rejected by PostgreSQL RLS with error code 42501 across all tables.
3. Anonymous PUT / UPSERT: strictly rejected by PostgreSQL RLS with error code 42501 across all tables.
4. Anonymous UPDATE / DELETE: strictly blocked from altering or removing any row (0 rows touched).
5. Data Integrity: verifies all core rows and counts remain completely pristine and unaltered.
"""

from __future__ import annotations

import os
import httpx
import pytest
from dotenv import load_dotenv
from scripts.deploy_apprunner import get_anon_key

load_dotenv()

TARGET_TABLES = [
    "residents",
    "hazard_events",
    "contacts",
    "dispatches",
    "escalations",
    "audit_log",
    "resources",
    "volunteers",
    "protocol",
    "gate_pending",
]

SAMPLE_INSERT_PAYLOADS = {
    "residents": {
        "name": "Adversary Resident",
        "phone": "+15559990001",
        "emergency_contact": "+1555010900",
        "age_band": "75-84",
    },
    "hazard_events": {
        "type": "heat",
        "severity": "extreme",
        "headline": "Adversary Alert",
        "zone": "DEMO_TEST",
        "source": "attacker",
    },
    "contacts": {
        "tier": 1,
        "status": "adversary_corrupted",
    },
    "dispatches": {
        "detail": "adversary unauthorized dispatch",
        "status": "forged",
    },
    "escalations": {
        "reason": "adversary unauthorized escalation",
        "status": "forged",
    },
    "audit_log": {
        "actor": "anonymous_attacker",
        "action": "tamper_database",
        "detail": "exploit_payload",
    },
    "resources": {
        "name": "Adversary Cooling Center",
        "kind": "cooling",
        "address": "666 Malicious Way",
        "hours": "24/7",
    },
    "volunteers": {
        "name": "Adversary Volunteer",
        "phone": "+15559990002",
        "home_block": "Block X",
    },
    "protocol": {
        "id": "adversary_protocol",
        "rules_yaml": "malicious: true",
    },
    "gate_pending": {
        "tool": "malicious_tool",
        "input": "{}",
    },
}


@pytest.fixture(scope="module")
def supabase_url() -> str:
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    if not url:
        pytest.skip("SUPABASE_URL not configured")
    return url


@pytest.fixture(scope="module")
def anon_key() -> str:
    key = get_anon_key()
    if not key:
        pytest.skip("Supabase anonymous key unavailable")
    return key


@pytest.fixture(scope="module")
def anon_client(supabase_url: str, anon_key: str):
    headers = {
        "apikey": anon_key,
        "Authorization": f"Bearer {anon_key}",
        "Accept-Profile": "porchlight",
        "Content-Profile": "porchlight",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    with httpx.Client(base_url=supabase_url, headers=headers, timeout=20.0) as client:
        yield client


# ==============================================================================
# Challenge 1: Anonymous SELECT Must Succeed on All Tables
# ==============================================================================

@pytest.mark.parametrize("table", TARGET_TABLES)
def test_anonymous_select_succeeds_cleanly(anon_client: httpx.Client, table: str):
    """Verifies that anonymous users can read all tables cleanly with HTTP 200."""
    resp = anon_client.get(f"/rest/v1/{table}?select=*&limit=5")
    assert resp.status_code == 200, f"SELECT failed on {table}: {resp.status_code} {resp.text}"
    data = resp.json()
    assert isinstance(data, list), f"Expected JSON list from {table}, got {type(data)}"


def test_anonymous_select_returns_exact_resident_count(anon_client: httpx.Client):
    """Verifies that anonymous SELECT on residents returns all 40 roster entries."""
    resp = anon_client.get("/rest/v1/residents?select=id,name,phone,language&order=name")
    assert resp.status_code == 200
    residents = resp.json()
    assert len(residents) == 40, f"Expected 40 residents, got {len(residents)}"

    # Anchor resident Ruth Alvarez must be readable
    ruth = [r for r in residents if r["name"] == "Ruth Alvarez"]
    assert len(ruth) == 1
    assert ruth[0]["phone"] == "+18129551686"


# ==============================================================================
# Challenge 2: Direct Anonymous INSERT Must Be Strictly Rejected by RLS (42501)
# ==============================================================================

@pytest.mark.parametrize("table", TARGET_TABLES)
def test_anonymous_insert_rejected_with_42501(anon_client: httpx.Client, table: str):
    """Adversarially attempts direct anonymous INSERT on every table. Must fail with RLS 42501."""
    payload = SAMPLE_INSERT_PAYLOADS.get(table, {"test": "val"})
    resp = anon_client.post(f"/rest/v1/{table}", json=payload)

    assert resp.status_code in (401, 403), (
        f"Expected HTTP 401/403 for INSERT on {table}, got {resp.status_code}: {resp.text}"
    )

    err = resp.json() if resp.text.startswith("{") else {}
    err_code = err.get("code")
    err_msg = err.get("message", "")

    assert err_code == "42501", (
        f"Expected PostgreSQL RLS error code 42501 on {table}, got {err_code!r} ({err_msg})"
    )
    assert "violates row-level security policy" in err_msg.lower(), (
        f"Expected RLS violation message on {table}, got: {err_msg}"
    )


# ==============================================================================
# Challenge 3: Anonymous PUT & Upsert Must Be Strictly Rejected with 42501
# ==============================================================================

@pytest.mark.parametrize("table", TARGET_TABLES)
def test_anonymous_put_replacement_rejected_with_42501(anon_client: httpx.Client, table: str):
    """Adversarially attempts full PUT replacement on existing or fake ID. Must fail with 42501."""
    sel = anon_client.get(f"/rest/v1/{table}?limit=1")
    rows = sel.json() if sel.status_code == 200 else []
    if rows:
        row = dict(rows[0])
        row_id = row.get("id", "00000000-0000-0000-0000-000000000000")
    else:
        row = SAMPLE_INSERT_PAYLOADS.get(table, {"id": "fake"})
        row_id = "00000000-0000-0000-0000-000000000000"

    resp = anon_client.put(f"/rest/v1/{table}?id=eq.{row_id}", json=row)
    assert resp.status_code in (401, 403), f"PUT on {table} must be rejected, got {resp.status_code}"

    err = resp.json() if resp.text.startswith("{") else {}
    assert err.get("code") == "42501", f"Expected code 42501 for PUT on {table}, got {err.get('code')}"


def test_anonymous_upsert_rejected_with_42501(anon_client: httpx.Client):
    """Adversarially attempts POST with Prefer: resolution=merge-duplicates. Must fail with 42501."""
    upsert_headers = {"Prefer": "resolution=merge-duplicates"}
    payload = {
        "id": "38807157-dc1f-4890-9226-1d4289fc3fa4",
        "name": "Ruth Alvarez Tampered",
        "phone": "+18129551686",
        "emergency_contact": "+1555010900",
        "age_band": "75-84",
    }
    resp = anon_client.post("/rest/v1/residents", json=payload, headers=upsert_headers)
    assert resp.status_code in (401, 403)
    err = resp.json()
    assert err.get("code") == "42501"
    assert "violates row-level security policy" in err.get("message", "").lower()


# ==============================================================================
# Challenge 4: Anonymous UPDATE and DELETE Blocked from Affecting Any Rows
# ==============================================================================

@pytest.mark.parametrize("table", TARGET_TABLES)
def test_anonymous_update_touches_zero_rows(anon_client: httpx.Client, table: str):
    """Adversarially attempts PATCH update with return=representation. RLS must block any changes."""
    sel = anon_client.get(f"/rest/v1/{table}?limit=1")
    rows = sel.json() if sel.status_code == 200 else []
    if not rows:
        pytest.skip(f"Table {table} has no rows to test UPDATE on")

    row_id = rows[0].get("id")
    # Attempt PATCH update
    update_payload = {"notes": "malicious_note"} if "notes" in rows[0] else {"detail": "malicious_detail"}
    resp = anon_client.patch(f"/rest/v1/{table}?id=eq.{row_id}", json=update_payload)

    # PostgREST either rejects with 401/403 or returns 200 with an empty list (0 rows modified)
    if resp.status_code == 200:
        modified_rows = resp.json()
        assert modified_rows == [], f"RLS bypass detected! UPDATE on {table} modified: {modified_rows}"
    else:
        assert resp.status_code in (400, 401, 403)


@pytest.mark.parametrize("table", TARGET_TABLES)
def test_anonymous_delete_touches_zero_rows(anon_client: httpx.Client, table: str):
    """Adversarially attempts DELETE on existing row. RLS must block any deletions."""
    sel = anon_client.get(f"/rest/v1/{table}?limit=1")
    rows = sel.json() if sel.status_code == 200 else []
    if not rows:
        pytest.skip(f"Table {table} has no rows to test DELETE on")

    row_id = rows[0].get("id")
    resp = anon_client.delete(f"/rest/v1/{table}?id=eq.{row_id}", headers={"Prefer": "count=exact"})

    # PostgREST returns 204 with content-range: */0 indicating 0 rows were deleted, or 401/403
    if resp.status_code in (200, 204):
        content_range = resp.headers.get("content-range")
        if content_range:
            assert content_range.endswith("/0"), f"RLS bypass detected! DELETE modified rows: {content_range}"
        if resp.text:
            assert resp.json() == []
    else:
        assert resp.status_code in (401, 403)


# ==============================================================================
# Challenge 5: Integrity Verification of Core Dataset Post-Attack
# ==============================================================================

def test_dataset_integrity_preserved_post_adversarial_testing(anon_client: httpx.Client):
    """Verifies that all dataset rows and fields remain pristine following adversarial attacks."""
    # 1. Residents count must remain exactly 40
    res = anon_client.get("/rest/v1/residents?select=id,name,notes,opted_out")
    assert res.status_code == 200
    residents = res.json()
    assert len(residents) == 40

    # 2. Ruth Alvarez must remain uncorrupted
    ruth = [r for r in residents if r["name"] == "Ruth Alvarez"][0]
    assert "Tier 1: 81, lives alone, no AC. Answers fast. Eval anchor." in ruth["notes"]
    assert ruth["opted_out"] is False

    # 3. Resources count must remain 3
    res_res = anon_client.get("/rest/v1/resources?select=id")
    assert res_res.status_code == 200
    assert len(res_res.json()) == 3

    # 4. Volunteers count must remain 5
    res_vol = anon_client.get("/rest/v1/volunteers?select=id")
    assert res_vol.status_code == 200
    assert len(res_vol.json()) == 5
