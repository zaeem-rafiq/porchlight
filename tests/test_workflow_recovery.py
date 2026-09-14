"""Exercise real Lambda/runtime handlers using in-memory DB and messaging adapters."""
import copy
import importlib
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from agent import app as runtime
from agent import coordinator, inbound, telegram
from agent.models import Triage

handlers = importlib.import_module("lambda.handlers")
NOW = datetime(2026, 9, 14, 22, 0, tzinfo=timezone.utc)
OWNER = "+1555010001"
OTHER = "+1555010002"


class Query:
    def __init__(self, db, table):
        self.db, self.name = db, table
        self.filters, self.op, self.payload, self.sort, self.cap = [], "select", None, None, None

    def select(self, *args): return self
    def eq(self, key, value):
        self.filters.append((key, value))
        return self
    def order(self, key, desc=False):
        self.sort = (key, desc)
        return self
    def limit(self, count):
        self.cap = count
        return self
    def insert(self, payload):
        self.op, self.payload = "insert", payload
        return self
    def update(self, payload):
        self.op, self.payload = "update", payload
        return self
    def execute(self):
        table = self.db.rows.setdefault(self.name, [])
        if self.op == "insert":
            row = copy.deepcopy(self.payload)
            self.db.counter += 1
            row.setdefault("id", f"record-{self.db.counter}")
            row.setdefault("created_at", (NOW + timedelta(microseconds=self.db.counter)).isoformat())
            row.setdefault("status", "open")
            table.append(row)
            return SimpleNamespace(data=[copy.deepcopy(row)])
        matched = [r for r in table if all(r.get(k) == v for k, v in self.filters)]
        if self.sort:
            key, desc = self.sort
            matched.sort(key=lambda r: r.get(key, ""), reverse=desc)
        if self.cap is not None:
            matched = matched[:self.cap]
        if self.op == "update":
            for row in matched:
                row.update(self.payload)
        return SimpleNamespace(data=copy.deepcopy(matched))


class DB:
    def __init__(self):
        self.counter = 0
        self.rows = {
            "hazard_events": [{"id": "event", "status": "open", "headline": "Heat drill"}],
            "residents": [
                {"id": "r1", "name": "Owner Resident", "phone": OWNER, "emergency_contact": OWNER, "opted_out": False},
                {"id": "r2", "name": "Ruth Alvarez", "phone": OTHER, "emergency_contact": OWNER, "opted_out": False},
            ],
            "volunteers": [{"id": "v1", "name": "Marcus Webb", "phone": OWNER, "opted_in": True}],
            "resources": [{"id": "center", "name": "Library", "kind": "cooling_center", "hours": "9-5"}],
            "contacts": [
                {"id": "c1", "resident_id": "r1", "event_id": "event", "status": "sent", "attempts": 1,
                 "last_outbound": NOW.isoformat(), "tier": 1},
                {"id": "c2", "resident_id": "r2", "event_id": "event", "status": "sent", "attempts": 1,
                 "last_outbound": NOW.isoformat(), "tier": 1},
            ],
        }
    def table(self, name): return Query(self, name)


@pytest.fixture
def system(monkeypatch):
    db, sends = DB(), []
    for key, value in {"OWNER_PHONE": OWNER, "PHONE_ALLOWLIST": f"{OWNER},{OTHER}",
                       "TELEGRAM_OWNER_CHAT_ID": "12345", "CONSOLE_KEY": "test-console",
                       "TELEGRAM_SECRET_TOKEN": "test-webhook", "ROSTER_MODE": "synthetic",
                       "PYTHON_DOTENV_DISABLED": "1"}.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(runtime, "get_config", lambda: {"OWNER_PHONE": OWNER})
    monkeypatch.setattr(runtime, "_sb", lambda: db)
    monkeypatch.setattr(inbound, "_sb", lambda: db)
    monkeypatch.setattr(handlers, "_runtime", lambda payload, suffix: runtime.porchlight(payload))
    monkeypatch.setattr(telegram, "send_message", lambda chat, text: sends.append((chat, text)) or len(sends))
    monkeypatch.setattr(inbound, "triage_reply", lambda body, resident: (
        Triage(status="medical", need="cooling", confidence=.9, quote=body, reason="medical-sounding reply"), True))
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None): return NOW
    monkeypatch.setattr(runtime, "datetime", Clock)
    return db, sends


def console(op, **payload):
    response = handlers.telegram_inbound_handler({"headers": {"x-console-key": "test-console"},
        "body": json.dumps({"op": op, "event_id": "event", **payload})}, None)
    assert response["statusCode"] == 200
    return json.loads(response["body"])


def menu_token(db):
    pings = [row for row in db.rows.get("audit_log", []) if row.get("action") == "coordinator_ping"]
    return json.loads(pings[-1]["detail"])["menu_token"] if pings else ""


def request_id(db):
    return db.rows["dispatches"][-1]["id"]


def message(text, chat="12345", secret="test-webhook", token=None):
    if token is not None and text.startswith("COORD "):
        text = "COORD " + token + " " + text[6:]

    response = handlers.telegram_inbound_handler({"headers": {"x-telegram-bot-api-secret-token": secret},
        "body": json.dumps({"event_id": "event", "message": {"chat": {"id": chat}, "text": text}})}, None)
    return response["statusCode"], json.loads(response["body"])


def test_distress_approval_and_real_volunteer_reply_follow_handler_flow(system):
    db, sends = system
    out = console("resident", **{"from": OTHER, "text": "AC broke, dizzy"})
    assert out["status"] == "medical" and out["coordinator_alert"]["outcome"] == "pinged"
    assert not db.rows.get("dispatches")
    assert f"COORD {menu_token(db)} 1" in sends[-1][1] and "Ruth Alvarez" in sends[-1][1]
    status, approved = message("COORD 1", token=menu_token(db))
    assert status == 200 and approved["outcome"] == "approved"
    assert approved["dispatch"]["outcome"] == "asked"
    assert f"Reply Y {request_id(db)}" in sends[-1][1]
    dispatch = db.rows["dispatches"][0]
    assert dispatch["resident_id"] == "r2" and dispatch["resource_id"] == "center"
    assert dispatch["status"] == "proposed"
    _, accepted = message(f"Y {request_id(db)}")
    assert accepted["outcome"] == "accepted" and dispatch["status"] == "accepted"
    _, duplicate = message(f"Y {request_id(db)}")
    assert duplicate["outcome"] == "ignored"
    _, repeated_approval = message("COORD 1", token=menu_token(db))
    assert repeated_approval["outcome"] == "ignored"
    assert len(db.rows["dispatches"]) == 1 and len(sends) == 2


def test_coordinator_identity_and_missing_webhook_auth_are_rejected(system, monkeypatch):
    db, sends = system
    assert message("COORD 1", chat="99999")[0] == 403
    assert message("COORD 1", secret="wrong")[0] == 403
    monkeypatch.delenv("TELEGRAM_SECRET_TOKEN")
    assert message("COORD 1", token=menu_token(db))[0] == 503
    assert runtime.on_inbound_coordinator({"from": OTHER, "body": "1", "event_id": "event"})["outcome"] == "dropped"
    assert not sends and not db.rows.get("dispatches")


def test_ill_handle_it_uses_sent_menu_and_does_not_dispatch(system):
    db, sends = system
    console("resident", **{"from": OTHER, "text": "dizzy"})
    # A new pending item arriving after the menu must not steal the displayed final option.
    coordinator.pending_add(db, "event", "dispatch_help", {"resident_id": "r1", "resident_name": "Owner Resident"})
    _, out = message("COORD 2", token=menu_token(db))
    assert out["outcome"] == "human_handling"
    gates = db.rows["gate_pending"]
    assert gates[0]["status"] == "human_handling" and gates[1]["status"] == "open"
    assert not db.rows.get("dispatches") and len(sends) == 1


def test_failed_volunteer_send_keeps_decision_open(system, monkeypatch):
    db, sends = system
    console("resident", **{"from": OTHER, "text": "dizzy"})
    monkeypatch.setattr(telegram, "send_message", lambda *args: 0)
    _, out = message("COORD 1", token=menu_token(db))
    assert out["outcome"] == "needs_coordinator" and out["reason"] == "failed"
    assert db.rows["gate_pending"][0]["status"] == "open"
    assert db.rows["dispatches"][0]["status"] == "failed"


def test_decline_and_wrong_volunteer_cannot_accept(system):
    db, sends = system
    console("resident", **{"from": OTHER, "text": "dizzy"})
    message("COORD 1", token=menu_token(db))
    out = runtime.on_inbound_volunteer({"from": OTHER, "body": "Y", "event_id": "event",
                                       "dispatch_id": db.rows["dispatches"][0]["id"]})
    assert out["outcome"] == "dropped"
    _, out = message(f"N {request_id(db)}")
    assert out["outcome"] == "declined" and db.rows["dispatches"][0]["status"] == "declined"


def test_actual_age_resend_once_then_unreachable(system):
    db, sends = system
    assert runtime.on_tick({"event_id": "event", "age_min": 10**9})["fired"] == []
    contact = db.rows["contacts"][0]
    contact["last_outbound"] = (NOW - timedelta(minutes=46)).isoformat()
    out = runtime.on_tick({"event_id": "event"})
    assert out["fired"] == ["resend:c1"]
    assert contact["status"] == "resent" and contact["attempts"] == 2 and len(sends) == 1
    assert runtime.on_tick({"event_id": "event"})["fired"] == []
    contact["last_outbound"] = (NOW - timedelta(minutes=46)).isoformat()
    assert runtime.on_tick({"event_id": "event"})["fired"] == ["unreachable:c1"]
    assert contact["status"] == "unreachable" and len(sends) == 2


def test_medical_silence_uses_inbound_timestamp_and_escalates_once(system):
    db, sends = system
    contact = db.rows["contacts"][1]
    contact.update(status="medical", last_inbound=(NOW - timedelta(minutes=19)).isoformat())
    assert runtime.on_tick({"event_id": "event"})["fired"] == []
    contact["last_inbound"] = (NOW - timedelta(minutes=21)).isoformat()
    assert runtime.on_tick({"event_id": "event"})["fired"] == ["silence:Ruth Alvarez:telegram"]
    assert runtime.on_tick({"event_id": "event"})["fired"] == []
    assert len(db.rows["escalations"]) == 1 and len(sends) == 1


def test_opt_out_cancels_future_triage_and_retry(system):
    db, sends = system
    assert console("resident", **{"from": OWNER, "text": "STOP"})["outcome"] == "opted_out"
    assert console("resident", **{"from": OWNER, "text": "dizzy"})["reason"] == "opted_out"
    db.rows["contacts"][0]["last_outbound"] = (NOW - timedelta(minutes=100)).isoformat()
    runtime.on_tick({"event_id": "event"})
    assert not sends and db.rows["contacts"][0]["status"] == "opted_out"


def test_decline_reopens_decision_and_keeps_medical_ladder_active(system):
    db, sends = system
    console("resident", **{"from": OTHER, "text": "dizzy"})
    message("COORD 1", token=menu_token(db))
    _, decline = message(f"N {request_id(db)}")
    assert decline["outcome"] == "declined" and decline["coordinator_alert"]["outcome"] == "pinged"
    assert db.rows["gate_pending"][0]["status"] == "open"
    assert "Volunteer declined" in sends[-1][1] and "Ruth Alvarez" in sends[-1][1]
    # The sole volunteer has declined: do not ask them repeatedly or quietly close the case.
    _, retry = message("COORD 1", token=menu_token(db))
    assert retry["outcome"] == "needs_coordinator" and retry["reason"] == "no_volunteer"
    assert db.rows["gate_pending"][0]["status"] == "open"
    assert len(db.rows["dispatches"]) == 1 and len(sends) == 4
    assert "No available volunteer" in sends[-1][1]
    db.rows["contacts"][1]["last_inbound"] = (NOW - timedelta(minutes=21)).isoformat()
    assert runtime.on_tick({"event_id": "event"})["fired"] == ["silence:Ruth Alvarez:telegram"]
    assert runtime.on_tick({"event_id": "event"})["fired"] == []
    assert len(db.rows["escalations"]) == 1


def test_proposal_alone_does_not_suppress_medical_ladder(system):
    db, sends = system
    console("resident", **{"from": OTHER, "text": "dizzy"})
    message("COORD 1", token=menu_token(db))
    assert db.rows["gate_pending"][0]["status"] == "approved"
    assert db.rows["dispatches"][0]["status"] == "proposed"
    db.rows["contacts"][1]["last_inbound"] = (NOW - timedelta(minutes=21)).isoformat()
    assert runtime.on_tick({"event_id": "event"})["fired"] == ["silence:Ruth Alvarez:telegram"]


def test_old_menu_or_bare_number_cannot_approve_a_new_case(system):
    db, sends = system
    console("resident", **{"from": OTHER, "text": "dizzy"})
    old_token = menu_token(db)
    _, first = message("COORD 2", token=old_token)
    assert first["outcome"] == "human_handling"
    console("resident", **{"from": OWNER, "text": "I feel dizzy"})
    new_token = menu_token(db)
    assert new_token != old_token
    assert "Owner Resident" in sends[-1][1]
    _, stale = message("COORD 1", token=old_token)
    _, bare = message("COORD 1")
    assert stale["outcome"] == bare["outcome"] == "ignored"
    assert not db.rows.get("dispatches")
    _, current = message("COORD 1", token=new_token)
    assert current["outcome"] == "approved"
    assert db.rows["dispatches"][0]["resident_id"] == "r1"


def test_console_requires_the_reviewed_menu_token(system):
    db, sends = system
    console("resident", **{"from": OTHER, "text": "dizzy"})
    assert console("coordinator", text="1")["outcome"] == "ignored"
    assert console("coordinator", text="1", menu_token="00000000")["outcome"] == "ignored"
    assert not db.rows.get("dispatches")
    assert console("coordinator", text="1", menu_token=menu_token(db))["outcome"] == "approved"


def test_explicit_secret_id_loads_config_without_lambda_environment(monkeypatch):
    import boto3

    monkeypatch.setattr(runtime, "_config", {})
    monkeypatch.delenv("AWS_EXECUTION_ENV", raising=False)
    monkeypatch.delenv("OWNER_PHONE", raising=False)
    monkeypatch.setenv("PORCHLIGHT_SECRET_ID", "porchlight/app")
    calls = []
    class Secrets:
        def get_secret_value(self, **kwargs):
            calls.append(kwargs)
            return {"SecretString": json.dumps({"OWNER_PHONE": OWNER})}
    monkeypatch.setattr(boto3, "client", lambda name: Secrets())
    assert runtime.get_config()["OWNER_PHONE"] == OWNER
    assert runtime.get_config()["OWNER_PHONE"] == OWNER
    assert calls == [{"SecretId": "porchlight/app"}]


def test_old_volunteer_reply_cannot_target_a_later_resident(system):
    db, sends = system
    console("resident", **{"from": OTHER, "text": "dizzy"})
    message("COORD 1", token=menu_token(db))
    old_request = request_id(db)
    assert message("N")[1]["outcome"] == "ignored"
    assert message(f"N {old_request}")[1]["outcome"] == "declined"
    message("COORD 2", token=menu_token(db))
    console("resident", **{"from": OWNER, "text": "I feel dizzy"})
    message("COORD 1", token=menu_token(db))
    new_request = request_id(db)
    assert new_request != old_request
    assert db.rows["dispatches"][-1]["resident_id"] == "r1"
    assert message(f"N {old_request}")[1]["outcome"] == "ignored"
    assert message("Y")[1]["outcome"] == "ignored"
    assert db.rows["dispatches"][-1]["status"] == "proposed"
    assert message(f"Y {new_request}")[1]["outcome"] == "accepted"


def test_console_volunteer_reply_requires_explicit_request_id(system):
    db, sends = system
    console("resident", **{"from": OTHER, "text": "dizzy"})
    message("COORD 1", token=menu_token(db))
    assert console("volunteer", text="Y")["outcome"] == "ignored"
    assert console("volunteer", text="Y", dispatch_id="old-id")["outcome"] == "ignored"
    assert db.rows["dispatches"][0]["status"] == "proposed"
    assert console("volunteer", text="Y", dispatch_id=request_id(db))["outcome"] == "accepted"
