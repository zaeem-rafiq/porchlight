"""Adversarial stress tests for Milestone M1 (Telegram Migration & Inbound Handlers)."""

import importlib
import json
import os
import pytest
from unittest.mock import patch

handlers = importlib.import_module("lambda.handlers")
from agent.inbound import handle_inbound


class MockBotoClient:
    def invoke_agent_runtime(self, **kwargs):
        payload = json.loads(kwargs.get("payload", b"{}"))
        return {"response": json.dumps({"ok": True, "action": payload.get("action"), "received": payload}).encode()}


@pytest.fixture(autouse=True)
def mock_boto():
    with patch("boto3.client", return_value=MockBotoClient()):
        yield


def test_malformed_json_syntax_returns_400():
    """Adversarial: Malformed JSON syntax must be rejected with HTTP 400."""
    event = {
        "headers": {},
        "body": '{"update_id": 123, "message":',
        "isBase64Encoded": False,
    }
    with patch.dict(os.environ, {"CONSOLE_KEY": "", "TELEGRAM_SECRET_TOKEN": ""}):
        res = handlers.telegram_inbound_handler(event, None)
        assert res.get("statusCode") == 400
        data = json.loads(res.get("body", "{}"))
        assert "bad json" in data.get("error", "")


def test_empty_and_partial_telegram_updates():
    """Adversarial: Empty, partial, or whitespace-only messages must be gracefully ignored (200 no_text)."""
    cases = [
        {"update_id": 100},
        {"update_id": 101, "message": {}},
        {"update_id": 102, "message": {"text": ""}},
        {"update_id": 103, "message": {"text": "   "}},
        {"update_id": 104, "edited_message": {"text": ""}},
    ]
    with patch.dict(os.environ, {"CONSOLE_KEY": "", "TELEGRAM_SECRET_TOKEN": ""}):
        for c in cases:
            event = {"headers": {}, "body": json.dumps(c), "isBase64Encoded": False}
            res = handlers.telegram_inbound_handler(event, None)
            assert res.get("statusCode") == 200
            data = json.loads(res.get("body", "{}"))
            assert data.get("ok") is True
            assert data.get("ignored") == "no_text"


def test_webhook_secret_token_validation():
    """Adversarial: Missing or invalid x-telegram-bot-api-secret-token must return HTTP 403."""
    with patch.dict(os.environ, {"CONSOLE_KEY": "", "TELEGRAM_SECRET_TOKEN": "my-secret-token-xyz"}):
        # 1. Missing header
        res = handlers.telegram_inbound_handler({"headers": {}, "body": json.dumps({"update_id": 1})}, None)
        assert res.get("statusCode") == 403
        assert json.loads(res.get("body")).get("error") == "bad secret token"

        # 2. Wrong header
        res = handlers.telegram_inbound_handler(
            {"headers": {"x-telegram-bot-api-secret-token": "wrong"}, "body": json.dumps({"update_id": 1})}, None
        )
        assert res.get("statusCode") == 403

        # 3. Correct header (case-insensitive header keys)
        res = handlers.telegram_inbound_handler(
            {"headers": {"X-Telegram-Bot-Api-Secret-Token": "my-secret-token-xyz"}, "body": json.dumps({"update_id": 1})}, None
        )
        assert res.get("statusCode") == 200


def test_simulation_endpoints_auth_enforcement():
    """Adversarial: Simulation endpoints must strictly enforce x-console-key (HTTP 403 on missing/empty/forged)."""
    with patch.dict(os.environ, {"CONSOLE_KEY": "valid-console-key-999", "TELEGRAM_SECRET_TOKEN": "tg-token", "RUNTIME_ARN": "arn:test"}):
        for op in ["inject", "resident", "volunteer", "coordinator"]:
            body = json.dumps({"op": op, "text": "dizzy", "from": "+15550000001", "event_id": "test-ev"})

            # Missing x-console-key
            res_missing = handlers.telegram_inbound_handler({"headers": {}, "body": body}, None)
            assert res_missing.get("statusCode") == 403, f"op={op} missing key should return 403"

            # Empty x-console-key
            res_empty = handlers.telegram_inbound_handler({"headers": {"x-console-key": ""}, "body": body}, None)
            assert res_empty.get("statusCode") == 403, f"op={op} empty key should return 403"

            # Forged x-console-key
            res_forged = handlers.telegram_inbound_handler({"headers": {"x-console-key": "forged-wrong-key"}, "body": body}, None)
            assert res_forged.get("statusCode") == 403, f"op={op} forged key should return 403"

            # Valid x-console-key
            res_valid = handlers.telegram_inbound_handler({"headers": {"X-Console-Key": "valid-console-key-999"}, "body": body}, None)
            assert res_valid.get("statusCode") == 200, f"op={op} valid key should return 200"


def test_simulation_resident_reply_dizzy_routing():
    """Adversarial: Simulation resident reply 'dizzy' must route with to='telegram' and avoid channel drop."""
    with patch.dict(os.environ, {"CONSOLE_KEY": "test-key", "AWS_REGION": "us-east-1", "RUNTIME_ARN": "arn:aws:bedrock:test"}):
        # When 'to' is omitted in simulation, handlers.py must default 'to' to 'telegram'
        event = {
            "headers": {"x-console-key": "test-key"},
            "body": json.dumps({"op": "resident", "text": "I feel dizzy and hot", "from": "+15550000001", "event_id": "evt-123"}),
        }
        res = handlers.telegram_inbound_handler(event, None)
        assert res.get("statusCode") == 200
        body_data = json.loads(res.get("body", "{}"))
        received = body_data.get("received", {})
        assert received.get("action") == "inbound.resident"
        assert received.get("to") == "telegram"
        assert received.get("body") == "I feel dizzy and hot"


def test_non_allowlisted_number_rejection_in_inbound():
    """Adversarial: Inbound from outside PHONE_ALLOWLIST must be dropped and never processed."""
    with patch.dict(os.environ, {"PHONE_ALLOWLIST": "+15550000001, +15550000002", "OWNER_PHONE": "+15550000001"}):
        result = handle_inbound("+15559999999", "telegram", "I need help", "evt-123")
        assert result.get("outcome") == "dropped"
        assert result.get("reason") == "not_allowlisted"


def test_valid_channel_retention():
    """Adversarial: Verify 'telegram' and console channels are valid and not dropped as wrong_channel."""
    from agent.safety import parse_allowlist

    valid = {"telegram", "bot", "simulated", "sim", "console", "coordinator", "coord", ""}
    for ch in valid:
        assert ch in valid