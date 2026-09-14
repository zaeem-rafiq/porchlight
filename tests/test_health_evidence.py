"""Health evidence must come from observed provider state, never local config."""
from unittest.mock import MagicMock, patch

import pytest

from scripts import reset_demo


@pytest.mark.parametrize("state, expected", [("READY", "READY"), ("CREATING", "CREATING"), (None, "UNKNOWN")])
def test_runtime_reports_actual_state(state, expected):
    client = MagicMock()
    client.list_agent_runtimes.return_value = {
        "agentRuntimes": [{"agentRuntimeName": "porchlight", "status": state}]
    }
    with patch("boto3.client", return_value=client):
        assert reset_demo.probe_runtime() == expected


def test_configured_runtime_arn_selects_the_actual_target(monkeypatch):
    monkeypatch.setenv("RUNTIME_ARN", "arn:target")
    client = MagicMock()
    client.list_agent_runtimes.return_value = {"agentRuntimes": [
        {"agentRuntimeName": "porchlight", "agentRuntimeArn": "arn:other", "status": "READY"},
        {"agentRuntimeName": "porchlight-generated", "agentRuntimeArn": "arn:target", "status": "UPDATE_FAILED"},
    ]}
    with patch("boto3.client", return_value=client):
        assert reset_demo.probe_runtime() == "UPDATE_FAILED"


def test_runtime_paginates_and_missing_runtime_is_not_ready():
    client = MagicMock()
    client.list_agent_runtimes.side_effect = [
        {"agentRuntimes": [], "nextToken": "page-2"},
        {"agentRuntimes": [{"agentRuntimeName": "porchlight", "status": "READY"}]},
    ]
    with patch("boto3.client", return_value=client):
        assert reset_demo.probe_runtime() == "READY"
    assert client.list_agent_runtimes.call_args.kwargs["nextToken"] == "page-2"
    client.list_agent_runtimes.side_effect = None
    client.list_agent_runtimes.return_value = {"agentRuntimes": []}
    with patch("boto3.client", return_value=client):
        assert reset_demo.probe_runtime() == "NOT_FOUND"


@pytest.mark.parametrize("third, expected", [
    ({"State": "Active", "LastUpdateStatus": "Successful"}, "3/3"),
    ({"State": "Pending", "LastUpdateStatus": "Successful"}, "2/3"),
    ({"State": "Active", "LastUpdateStatus": "Failed"}, "2/3"),
    ({"State": "Active"}, "2/3"),
])
def test_lambda_health_requires_all_three_provider_states(third, expected):
    cf, lambdas = MagicMock(), MagicMock()
    cf.get_paginator.return_value.paginate.return_value = [{"StackResourceSummaries": [
        {"LogicalResourceId": name, "ResourceType": "AWS::Lambda::Function", "PhysicalResourceId": name}
        for name in ("NwsPoll", "TwilioInbound", "Tick")
    ]}]
    lambdas.get_function_configuration.side_effect = [
        {"State": "Active", "LastUpdateStatus": "Successful"},
        {"State": "Active", "LastUpdateStatus": "Successful"}, third,
    ]
    with patch("boto3.client", side_effect=lambda service, **_: cf if service == "cloudformation" else lambdas):
        assert reset_demo.probe_lambdas() == expected
    assert lambdas.get_function_configuration.call_count == 3


def test_provider_failure_never_passes_from_local_configuration(capsys):
    assert reset_demo.configuration_diagnostics()["runtime_config"] is True
    with patch("boto3.client", side_effect=RuntimeError("secret-provider-detail")):
        assert reset_demo.probe_runtime() == "UNVERIFIED"
        assert reset_demo.probe_lambdas() == "UNVERIFIED"
    output = capsys.readouterr().out
    assert "[PASS]" not in output
    assert "secret-provider-detail" not in output


def test_remote_console_failure_does_not_pass_from_localhost(monkeypatch):
    monkeypatch.setenv("CONSOLE_URL", "https://unavailable.example")
    with patch("httpx.get", side_effect=OSError("unreachable")) as get, patch("subprocess.Popen") as start:
        assert reset_demo.probe_console(start_if_needed=True) == (0, None)
    get.assert_called_once_with("https://unavailable.example/", timeout=3.0)
    start.assert_not_called()


def test_incomplete_health_cannot_emit_pass(capsys):
    with patch.object(reset_demo, "get_sb_client"), patch.object(reset_demo, "reset_database"), \
         patch.object(reset_demo, "configuration_diagnostics"), \
         patch.object(reset_demo, "probe_runtime", return_value="UNVERIFIED"), \
         patch.object(reset_demo, "probe_lambdas", return_value="3/3"), \
         patch.object(reset_demo, "probe_console", return_value=(200, None)), \
         patch.object(reset_demo, "probe_telegram", return_value="ok"):
        assert reset_demo.main() == 1
    assert "= PASS" not in capsys.readouterr().out


def test_allowlist_failure_precedes_every_database_mutation(monkeypatch):
    monkeypatch.setenv("OWNER_PHONE", "+1555010001")
    monkeypatch.setenv("PHONE_ALLOWLIST", "+1555010001")
    database = MagicMock()
    with pytest.raises(RuntimeError, match="ABORTED"):
        reset_demo.reset_database(database)
    database.table.assert_not_called()
