"""Adversarial stress harness for Milestone M2 (Simulation, Authentication & Packaging).

Empirically challenges:
1. Simulation endpoint authentication (HTTP 403 on missing, empty, whitespace, and forged keys).
2. Simulation parameter routing ('to' defaulted to 'telegram', never dropped).
3. Payload corruption and non-object simulation request safety.
4. Container specification benchmarks (non-root execution, minimal surface, port exposure).
"""

import importlib
import json
import os
import re
import pytest
from unittest.mock import patch

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
handlers = importlib.import_module("lambda.handlers")


class MockBotoClient:
    def invoke_agent_runtime(self, **kwargs):
        payload = json.loads(kwargs.get("payload", b"{}"))
        return {
            "response": json.dumps({
                "ok": True,
                "action": payload.get("action"),
                "received": payload,
                "runtimeSessionId": kwargs.get("runtimeSessionId"),
            }).encode()
        }


@pytest.fixture(autouse=True)
def mock_boto():
    with patch("boto3.client", return_value=MockBotoClient()):
        yield


# ==============================================================================
# Challenge 1: Adversarial Authentication on Simulation Endpoints
# ==============================================================================

@pytest.mark.parametrize("op", ["inject", "resident", "volunteer", "coordinator"])
@pytest.mark.parametrize("bad_key_header", [
    None,            # Missing header
    "",              # Empty header
    "   ",           # Whitespace-only header
    "forged-token",  # Forged/tampered header
    "Bearer secret", # Wrong prefix format
    "null",          # String 'null'
])
def test_simulation_endpoints_reject_unauthorized_keys_with_403(op: str, bad_key_header: str | None):
    """Adversarially asserts that all simulation ops with missing, empty, or forged keys return 403."""
    console_secret = "super-secret-console-key-2026"
    headers = {}
    if bad_key_header is not None:
        headers["x-console-key"] = bad_key_header

    body = json.dumps({"op": op, "text": "test", "from": "+15550000001", "event_id": "evt-auth-1"})
    event = {"headers": headers, "body": body, "isBase64Encoded": False}

    with patch.dict(os.environ, {
        "CONSOLE_KEY": console_secret,
        "TELEGRAM_SECRET_TOKEN": "tg-sec-1",
        "RUNTIME_ARN": "arn:aws:bedrock:test",
    }):
        res = handlers.telegram_inbound_handler(event, None)
        assert res.get("statusCode") == 403, (
            f"Expected HTTP 403 for op={op} with x-console-key={bad_key_header!r}, got {res.get('statusCode')}"
        )
        data = json.loads(res.get("body", "{}"))
        assert "error" in data


@pytest.mark.parametrize("header_name", [
    "x-console-key",
    "X-Console-Key",
    "X-CONSOLE-KEY",
    "x-CoNsOlE-kEy",
])
def test_simulation_authentication_case_insensitivity(header_name: str):
    """Verifies that legitimate console keys are accepted regardless of header casing."""
    console_secret = "correct-console-key-xyz"
    body = json.dumps({"op": "coordinator", "text": "1", "event_id": "evt-case-1"})
    event = {
        "headers": {header_name: console_secret},
        "body": body,
        "isBase64Encoded": False,
    }

    with patch.dict(os.environ, {
        "CONSOLE_KEY": console_secret,
        "RUNTIME_ARN": "arn:aws:bedrock:test",
    }):
        res = handlers.telegram_inbound_handler(event, None)
        assert res.get("statusCode") == 200
        data = json.loads(res.get("body", "{}"))
        assert data.get("ok") is True
        assert data.get("action") == "inbound.coordinator"


def test_simulation_key_with_corrupt_payloads():
    """Adversarial: Simulation endpoint with valid key but corrupted/non-dict payload."""
    console_secret = "secret-123"

    with patch.dict(os.environ, {"CONSOLE_KEY": console_secret, "RUNTIME_ARN": "arn:test"}):
        # 1. Invalid JSON
        event_bad_json = {
            "headers": {"x-console-key": console_secret},
            "body": "{not-valid-json",
            "isBase64Encoded": False,
        }
        res = handlers.telegram_inbound_handler(event_bad_json, None)
        assert res.get("statusCode") == 400
        assert "bad json" in json.loads(res.get("body", "{}")).get("error", "")

        # 2. JSON array instead of object
        event_array = {
            "headers": {"x-console-key": console_secret},
            "body": json.dumps(["not", "an", "object"]),
            "isBase64Encoded": False,
        }
        res2 = handlers.telegram_inbound_handler(event_array, None)
        assert res2.get("statusCode") == 400
        assert "must be a JSON object" in json.loads(res2.get("body", "{}")).get("error", "")


# ==============================================================================
# Challenge 2: Resident Reply Simulation Parameter Routing & Channel Retention
# ==============================================================================

@pytest.mark.parametrize("to_input, expected_to", [
    (None, "telegram"),
    ("", "telegram"),
    ("telegram", "telegram"),
    ("TELEGRAM", "TELEGRAM"),
    ("console", "console"),
    ("simulated", "simulated"),
])
def test_resident_reply_simulation_defaults_to_telegram(to_input: str | None, expected_to: str):
    """Verifies that simulation of resident replies always routes with a valid channel and never drops."""
    console_secret = "console-key-routing"
    payload = {
        "op": "resident",
        "text": "I feel dizzy and have no AC",
        "from": "+15550000001",
        "event_id": "evt-route-1",
    }
    if to_input is not None:
        payload["to"] = to_input

    event = {
        "headers": {"x-console-key": console_secret},
        "body": json.dumps(payload),
        "isBase64Encoded": False,
    }

    with patch.dict(os.environ, {
        "CONSOLE_KEY": console_secret,
        "RUNTIME_ARN": "arn:aws:bedrock:test",
    }):
        res = handlers.telegram_inbound_handler(event, None)
        assert res.get("statusCode") == 200
        data = json.loads(res.get("body", "{}"))
        received = data.get("received", {})
        assert received.get("action") == "inbound.resident"
        assert received.get("to") == expected_to
        assert received.get("body") == "I feel dizzy and have no AC"
        assert received.get("from") == "+15550000001"


def test_telegram_channel_in_handle_inbound_never_drops():
    """Empirically asserts that inbound routing accepts 'telegram' and never flags 'dropped_wrong_channel'."""
    from agent.inbound import handle_inbound

    # Mock supabase client
    class MockTable:
        def __init__(self, name=""):
            self.name = name
        def select(self, *a): return self
        def eq(self, *a): return self
        def update(self, *a): return self
        def insert(self, *a): return self
        def execute(self):
            if self.name == "contacts":
                return type("Res", (), {"data": [{"status": "sent", "resident_id": "res-1"}]})()
            return type("Res", (), {"data": [{"id": "res-1", "name": "Ruth Alvarez", "phone": "+15550000001"}]})()

    class MockSB:
        def table(self, name): return MockTable(name)

    with patch("agent.inbound._sb", return_value=MockSB()):
        with patch.dict(os.environ, {
            "PHONE_ALLOWLIST": "+15550000001",
            "OWNER_PHONE": "+15550000001",
            "TWILIO_NUMBER_B": "+15551112222",
        }):
            # Test with channel = "telegram"
            out = handle_inbound("+15550000001", "telegram", "1", "evt-123")
            assert out.get("outcome") != "dropped", f"Expected success or triage, got dropped: {out}"
            assert out.get("reason") != "wrong_channel"



# ==============================================================================
# Challenge 3: Container Specification & Security Benchmark Validation
# ==============================================================================

def test_dockerfile_security_and_packaging_benchmarks():
    """Validates Dockerfile against CIS Docker / container security benchmarks."""
    dockerfile_path = os.path.join(REPO_ROOT, "console", "Dockerfile")
    assert os.path.exists(dockerfile_path), "console/Dockerfile does not exist"

    with open(dockerfile_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Benchmark 1: Multi-stage build structure
    from_stages = re.findall(r"^FROM\s+([^\s]+)\s+AS\s+([^\s]+)", content, re.MULTILINE | re.IGNORECASE)
    assert len(from_stages) >= 2, f"Dockerfile must have multiple stages, found: {from_stages}"
    stage_names = [s[1].lower() for s in from_stages]
    assert "runner" in stage_names or "run" in stage_names, "Missing runner stage"

    # Benchmark 2: Non-root execution
    user_match = re.search(r"^USER\s+([^\s]+)", content, re.MULTILINE)
    assert user_match is not None, "Dockerfile must define a non-root USER directive"
    user_name = user_match.group(1).strip()
    assert user_name != "root" and user_name != "0", f"Container must NOT run as root (found {user_name})"

    # Verify user and group creation with system flags and unprivileged UIDs
    assert "addgroup" in content, "Dockerfile should explicitly create system group"
    assert "adduser" in content, "Dockerfile should explicitly create system user"
    assert "1001" in content, "Non-root UID/GID 1001 expected"

    # Benchmark 3: Port and Hostname Binding
    assert "EXPOSE 3000" in content, "Dockerfile must expose port 3000"
    assert 'ENV HOSTNAME="0.0.0.0"' in content or "ENV HOSTNAME=0.0.0.0" in content, (
        "Dockerfile must bind HOSTNAME to 0.0.0.0 for container networking"
    )
    assert "ENV PORT=3000" in content or "ENV PORT 3000" in content

    # Benchmark 4: Secret protection in build context
    dockerignore_path = os.path.join(REPO_ROOT, "console", ".dockerignore")
    assert os.path.exists(dockerignore_path), "console/.dockerignore does not exist"
    with open(dockerignore_path, "r", encoding="utf-8") as f:
        ignore_content = f.read()
    assert ".env*" in ignore_content, ".dockerignore must ignore .env* secrets"
    assert "node_modules" in ignore_content, ".dockerignore must ignore local node_modules"
    assert ".git" in ignore_content, ".dockerignore must ignore .git"

    # Benchmark 5: Standalone Next.js entrypoint in exec form
    cmd_match = re.search(r'CMD\s*\[\s*"node"\s*,\s*"server\.js"\s*\]', content)
    assert cmd_match is not None, 'CMD must be in exec form: CMD ["node", "server.js"]'
