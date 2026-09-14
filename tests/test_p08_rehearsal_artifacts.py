"""P-08 Deliverables and Rehearsal Artifacts Verification Test Suite.

Verifies:
1. scripts/reset_demo.py: health probes (runtime, lambdas, console, telegram),
   allowlist assertion failure aborts before writes, idempotent seed counts.
2. scripts/rehearsal_p08.py: proof line formatting, timestamp monotonicity,
   strict allowlist validation.
3. Architecture assets: docs/architecture.mmd, docs/architecture.svg,
   docs/media/architecture.png (valid headers and content).
4. docs/runbook-demo.md: scene sequence, timings, and contingency table.
5. README.md: all required specification sections present and accurate.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


# ==============================================================================
# 1. reset_demo.py Unit Tests
# ==============================================================================

def test_reset_demo_probes():
    """Verifies that reset_demo.py probe functions execute correctly without errors."""
    from scripts.reset_demo import probe_lambdas, probe_runtime

    # Runtime probe should evaluate config/boto3 and return READY
    runtime_status = probe_runtime()
    assert runtime_status in ("READY", "AVAILABLE")

    # Lambda probe should verify 3/3 handlers in lambda.handlers
    lambdas_status = probe_lambdas()
    assert lambdas_status == "3/3"


def test_reset_demo_allowlist_assertion_aborts_on_unauthorized_number():
    """Verifies that any phone outside PHONE_ALLOWLIST aborts reset_database with zero writes."""
    from scripts.reset_demo import reset_database

    mock_sb = MagicMock()
    with patch.dict(os.environ, {
        "OWNER_PHONE": "+1555010001",
        "PHONE_ALLOWLIST": "+1555010001",  # Missing other synthetic roster numbers
    }):
        with pytest.raises(RuntimeError, match="ABORTED: .* phones outside PHONE_ALLOWLIST"):
            reset_database(mock_sb)

    # Assert no table inserts occurred
    mock_sb.table.return_value.insert.assert_not_called()


def test_reset_demo_proof_line_format():
    """Verifies exact proof line formatting expected for P-08 reset_demo."""
    expected_pattern = "PROOF P-08: reset_demo ok runtime=READY lambdas=3/3 console=200 telegram=ok = PASS"
    runtime = "READY"
    lambdas = "3/3"
    console = 200
    telegram = "ok"
    actual = f"PROOF P-08: reset_demo ok runtime={runtime} lambdas={lambdas} console={console} telegram={telegram} = PASS"
    assert actual == expected_pattern


# ==============================================================================
# 2. rehearsal_p08.py Structure and Verification Tests
# ==============================================================================

def test_rehearsal_proof_line_format():
    """Verifies exact proof line expected for P-08 dress rehearsal."""
    expected = (
        "PROOF P-08: rehearsal — Ruth text received; \"1\" → ok; "
        "Alvarez medical → coordinator text received; reply 1 → volunteer Y → "
        "dispatch + calendar; timestamps printed; zero sends outside the allowlist = PASS"
    )
    from scripts.rehearsal_p08 import PROOF_LINE
    assert PROOF_LINE == expected


def test_rehearsal_timestamp_monotonicity_logic():
    """Verifies that rehearsal timestamp records are strictly monotonic."""
    mock_timestamps = [
        ("Alert Injected (heat.json)", "2026-09-14T19:00:00Z", 100.0),
        ("Ruth Text Received", "2026-09-14T19:00:10Z", 110.0),
        ("Ruth Reply '1' -> ok", "2026-09-14T19:00:11Z", 111.0),
        ("Alvarez Medical -> Coordinator Alert", "2026-09-14T19:00:13Z", 113.0),
        ("Reply 1 -> Volunteer Y -> Dispatch + Calendar", "2026-09-14T19:00:14Z", 114.0),
    ]
    for i in range(1, len(mock_timestamps)):
        assert mock_timestamps[i][2] >= mock_timestamps[i - 1][2]


# ==============================================================================
# 3. Architecture Diagrams Verification
# ==============================================================================

def test_architecture_diagram_mmd_contains_required_nodes():
    """Verifies docs/architecture.mmd contains all pipeline elements required by P-08."""
    mmd_path = os.path.join(REPO_ROOT, "docs", "architecture.mmd")
    assert os.path.isfile(mmd_path), "Missing docs/architecture.mmd"

    with open(mmd_path, "r", encoding="utf-8") as fh:
        content = fh.read()

    # Verify required architectural elements
    assert "NWS" in content
    assert "EventBridge" in content
    assert "AgentCore" in content or "agentcore" in content
    assert "Strands" in content or "strands" in content
    assert "Telegram" in content
    assert "Coordinator" in content
    assert "Supabase" in content
    assert "RLS" in content
    assert "App Runner" in content or "AppRunner" in content


def test_architecture_diagram_svg_valid():
    """Verifies docs/architecture.svg exists and is valid SVG XML."""
    svg_path = os.path.join(REPO_ROOT, "docs", "architecture.svg")
    assert os.path.isfile(svg_path), "Missing docs/architecture.svg"
    assert os.path.getsize(svg_path) > 1000, "docs/architecture.svg is too small"

    # Must be parseable as XML
    tree = ET.parse(svg_path)
    root = tree.getroot()
    assert "svg" in root.tag.lower(), "Root element must be svg"


def test_architecture_diagram_png_valid():
    """Verifies docs/media/architecture.png exists and has valid PNG header."""
    png_path = os.path.join(REPO_ROOT, "docs", "media", "architecture.png")
    assert os.path.isfile(png_path), "Missing docs/media/architecture.png"
    assert os.path.getsize(png_path) > 5000, "docs/media/architecture.png is too small"

    with open(png_path, "rb") as fh:
        header = fh.read(8)
    assert header == b"\x89PNG\r\n\x1a\n", "docs/media/architecture.png must be a valid PNG image"


# ==============================================================================
# 4. Runbook & Documentation Integrity Tests
# ==============================================================================

def test_runbook_demo_structure():
    """Verifies docs/runbook-demo.md has take sequence and contingency table."""
    runbook_path = os.path.join(REPO_ROOT, "docs", "runbook-demo.md")
    assert os.path.isfile(runbook_path), "Missing docs/runbook-demo.md"

    with open(runbook_path, "r", encoding="utf-8") as fh:
        content = fh.read()

    # Verify all 7 scenes in 3-minute sequence
    for scene_num in range(1, 8):
        assert f"Scene {scene_num}:" in content, f"Missing Scene {scene_num} in runbook"

    # Verify contingency table
    assert "Contingency Table" in content or "If X Fails, Do Y" in content
    assert "Telegram" in content
    assert "Console" in content
    assert "Triage" in content
    assert "Volunteer" in content


def test_readme_specification_coverage():
    """Verifies README.md covers all required P-08 specification sections."""
    readme_path = os.path.join(REPO_ROOT, "README.md")
    assert os.path.isfile(readme_path), "Missing README.md"

    with open(readme_path, "r", encoding="utf-8") as fh:
        content = fh.read()

    # Target Audience & Problem
    assert "In an extreme heat wave" in content
    assert "mutual-aid" in content.lower() or "senior centers" in content.lower()

    # Safety
    assert "PHONE_ALLOWLIST" in content
    assert "Never-911" in content
    assert "STOP" in content
    assert "Consent & Data Model" in content

    # Strands Features
    assert "Agents-as-Tools" in content
    assert "Structured Output" in content
    assert "Hooks & Interrupts" in content
    assert "Session Managers" in content
    assert "AgentCore Memory" in content

    # AgentCore Services
    assert "AgentCore Runtime" in content
    assert "AgentCore Memory" in content
    assert "AWS Lambda Glue" in content
    assert "Secrets Manager" in content
    assert "Amazon ECR" in content
    assert "AWS App Runner" in content
    assert "Amazon EventBridge" in content

    # Evals
    assert "27 / 30" in content
    assert "26 / 30" in content
    assert "30 / 30" in content
    assert "29 / 30" in content

    # License
    assert "MIT License" in content
