"""Local harness acceptance: real handlers, fictional state, captured I/O only."""

import http.client
import json
import socket
import threading
from pathlib import Path

import pytest

from scripts.local_drill import Drill, KEY, LABEL, OWNER, make_server


@pytest.fixture
def drill():
    with Drill(log=False) as state:
        yield state


def heat():
    return json.loads((Path(__file__).resolve().parents[1] / "data/fixtures/alerts/heat.json").read_text())


def test_real_handler_lifecycle_is_captured_and_explicitly_synthetic(drill):
    status, injected = drill.invoke({"op": "inject", "alert": heat(), "fixture": "heat.json"})
    assert status == 200 and injected["accepted"]
    assert injected["wave"] == {"sent": 40, "simulated": 40, "real": 0, "failed": 0, "skipped": 0}
    assert len(drill.rows["contacts"]) == 40 and len(drill.outbox) == 40
    event_id = injected["event_id"]
    _, okay = drill.invoke({"op": "resident", "event_id": event_id, "from": "+12025550101", "text": "1"})
    assert okay["status"] == "ok" and okay["used_model"] is False
    _, distress = drill.invoke({"op": "resident", "event_id": event_id, "from": OWNER, "text": "AC broke, dizzy"})
    assert distress["status"] == "medical" and distress["used_model"] is False
    assert distress["quote"] == "AC broke, dizzy" and distress["_drill"] == LABEL
    assert drill.rows["gate_pending"][0]["status"] == "open"
    assert not drill.rows["dispatches"] and len(drill.outbox) == 41
    menu = json.loads(next(row["detail"] for row in reversed(drill.rows["audit_log"]) if row["action"] == "coordinator_ping"))
    assert menu["menu_token"] in drill.outbox[-1]["body"]
    _, approved = drill.invoke({"op": "coordinator", "event_id": event_id, "text": "1", "menu_token": menu["menu_token"]})
    assert approved["outcome"] == "approved" and approved["dispatch"]["outcome"] == "asked"
    assert drill.rows["dispatches"][0]["status"] == "proposed"
    request_id = drill.rows["dispatches"][0]["id"]
    assert f"Reply Y {request_id}" in drill.outbox[-1]["body"]
    _, accepted = drill.invoke({"op": "volunteer", "event_id": event_id, "text": "Y", "dispatch_id": request_id})
    assert accepted["outcome"] == "accepted" and drill.rows["dispatches"][0]["status"] == "accepted"
    _, duplicate = drill.invoke({"op": "volunteer", "event_id": event_id, "text": "Y", "dispatch_id": request_id})
    assert duplicate["outcome"] == "ignored" and len(drill.rows["dispatches"]) == 1
    assert len(drill.outbox) == 42 and all(m["channel"] == "simulated" for m in drill.outbox)
    assert LABEL in drill.outbox_html() and "none were delivered" in drill.outbox_html()


def test_unknown_speech_routes_to_human_and_transport_is_fail_closed(drill):
    result, used_model = drill.fixture_triage("This sentence is not a fixture", {})
    assert result.status == "unclear" and result.confidence == 0.0 and not used_model
    assert len(drill.allowlist) > 40 and all(phone.startswith("+120255501") for phone in drill.allowlist)
    with pytest.raises(PermissionError):
        drill.capture_send(None, "+19999999999", "telegram", "hello", OWNER)
    with socket.socket() as connection, pytest.raises(PermissionError, match="external"):
        connection.connect(("203.0.113.1", 443))
    assert drill.invoke({"op": "inject", "alert": heat()}, key="wrong")[0] == 403
    assert drill.invoke({"op": "tick"})[0] == 400
    assert not drill.outbox and not drill.rows["hazard_events"]


def test_http_contract_supports_console_queries_and_rejects_writes(drill):
    with make_server(drill, port=0) as server:
        assert server.server_address[0] == "127.0.0.1"
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            def request(method, path, payload=None, key=KEY):
                connection = http.client.HTTPConnection(*server.server_address, timeout=5)
                connection.request(method, path, json.dumps(payload) if payload is not None else None,
                                   {"apikey": key, "X-Console-Key": key, "Content-Type": "application/json"})
                response = connection.getresponse()
                body, status = response.read(), response.status
                connection.close()
                return status, json.loads(body)

            status, residents = request("GET", "/rest/v1/residents?select=*&order=name.asc")
            assert status == 200 and len(residents) == 40 and residents[0]["name"] == "Agnes Kowalski"
            assert request("GET", "/rest/v1/residents?select=*", key="wrong")[0] == 403
            assert request("POST", "/rest/v1/residents", {"name": "external"})[0] == 404
            status, injected = request("POST", "/", {"op": "inject", "alert": heat(), "fixture": "heat.json"})
            assert status == 200 and injected["wave"]["real"] == 0
            event_id = injected["event_id"]
            status, contacts = request("GET", f"/rest/v1/contacts?select=*&event_id=eq.{event_id}")
            assert status == 200 and len(contacts) == 40
            status, audit = request("GET", f"/rest/v1/audit_log?select=*&event_id=eq.{event_id}&detail=ilike.%25Ruth%25&order=created_at.asc")
            assert status == 200 and len(audit) == 1 and "Ruth Alvarez" in audit[0]["detail"]
            assert request("GET", "/rest/v1/not_a_table?select=*")[0] == 400
        finally:
            server.shutdown()
            worker.join(timeout=5)
