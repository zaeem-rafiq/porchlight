"""Exercise outbound, model-output, and console trust boundaries without live I/O."""

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from agent import outreach, telegram, triage
from agent.models import Triage


def test_outbound_phone_and_chat_allowlists_block_before_transport(monkeypatch):
    env = {"PHONE_ALLOWLIST": "+15550000001", "OWNER_PHONE": "+15550000001",
           "TELEGRAM_OWNER_CHAT_ID": "123"}
    monkeypatch.setattr(telegram, "_env", lambda: env)
    monkeypatch.setenv("PHONE_ALLOWLIST", env["PHONE_ALLOWLIST"])
    calls = []
    monkeypatch.setattr(telegram, "api", lambda *args: calls.append(args))
    with pytest.raises(PermissionError):
        outreach.send_one(None, "+19999999999", "telegram", "Check in", env["OWNER_PHONE"])
    with pytest.raises(PermissionError):
        telegram.send_message("999", "Check in")
    env["PHONE_ALLOWLIST"] = ""
    with pytest.raises(PermissionError):
        telegram.send_message("123", "Check in")
    assert calls == []


@pytest.mark.parametrize("response", [
    {"ok": False, "result": {"message_id": 123}},
    {"ok": True, "result": {"message_id": 0}},
    {"ok": True, "result": {"message_id": "123"}},
    {"ok": True, "result": {"message_id": True}},
    {"ok": True},
])
def test_failed_telegram_response_never_reports_a_send(monkeypatch, response):
    env = {"PHONE_ALLOWLIST": "+15550000001", "OWNER_PHONE": "+15550000001",
           "TELEGRAM_OWNER_CHAT_ID": "123"}
    monkeypatch.setattr(telegram, "_env", lambda: env)
    monkeypatch.setenv("PHONE_ALLOWLIST", env["PHONE_ALLOWLIST"])
    monkeypatch.setattr(telegram, "owner_chat_id", lambda: "123")
    monkeypatch.setattr(telegram, "api", lambda *args: response)
    assert outreach.send_one(None, env["OWNER_PHONE"], "telegram", "Check in", env["OWNER_PHONE"]) == ("", "failed")


def test_success_and_simulation_remain_distinct(monkeypatch):
    env = {"PHONE_ALLOWLIST": "+15550000001,+15550000002", "OWNER_PHONE": "+15550000001",
           "TELEGRAM_OWNER_CHAT_ID": "123"}
    monkeypatch.setattr(telegram, "_env", lambda: env)
    monkeypatch.setenv("PHONE_ALLOWLIST", env["PHONE_ALLOWLIST"])
    monkeypatch.setattr(telegram, "owner_chat_id", lambda: "123")
    calls = []

    def send(*args):
        calls.append(args)
        return {"ok": True, "result": {"message_id": 42}}

    monkeypatch.setattr(telegram, "api", send)
    assert outreach.send_one(None, env["OWNER_PHONE"], "telegram", "Check in", env["OWNER_PHONE"]) == ("TG-42", "telegram")
    sid, channel = outreach.send_one(None, "+15550000002", "telegram", "Check in", env["OWNER_PHONE"])
    assert channel == "simulated" and sid.startswith("SIM-")
    assert len(calls) == 1


class WaveStore:
    def __init__(self):
        self.rows = {"residents": [{"id": "r1", "name": "Test Resident", "phone": "+15550000001", "opted_out": False}],
                     "contacts": [], "audit_log": []}
    def schema(self, _): return self
    def table(self, name):
        self.name, self.filters, self.operation, self.value = name, [], "select", None
        return self
    def select(self, *_): return self
    def eq(self, key, value): self.filters.append((key, value)); return self
    def limit(self, *_): return self
    def insert(self, value): self.operation, self.value = "insert", value; return self
    def update(self, value): self.operation, self.value = "update", value; return self
    def execute(self):
        table = self.rows[self.name]
        if self.operation == "insert":
            row = {"id": f"{self.name}-{len(table)}", **self.value}
            table.append(row)
            return SimpleNamespace(data=[row.copy()])
        rows = [row for row in table if all(row.get(key) == value for key, value in self.filters)]
        if self.operation == "update":
            for row in rows:
                row.update(self.value)
        return SimpleNamespace(data=[row.copy() for row in rows])


def test_failed_wave_does_not_persist_sent_contacts(monkeypatch):
    import supabase

    store = WaveStore()
    monkeypatch.setattr(supabase, "create_client", lambda *_: store)
    monkeypatch.setenv("PHONE_ALLOWLIST", "+15550000001")
    monkeypatch.setattr(outreach, "compose", lambda *_args, **_kwargs: "Check in")
    monkeypatch.setattr(outreach, "send_one", lambda *_: ("", "failed"))
    result = outreach.send_wave("e1", {"r1": 1})
    assert result == {"sent": 0, "real": 0, "simulated": 0, "failed": 1, "skipped": 0}
    contact = store.rows["contacts"][0]
    assert contact["status"] == "send_failed" and contact["attempts"] == 0
    assert "last_outbound" not in contact
    assert store.rows["audit_log"][0]["action"] == "wave tier1 failed"


def test_repeated_wave_preserves_triage_and_attempts(monkeypatch):
    import supabase

    store, sends = WaveStore(), []
    monkeypatch.setattr(supabase, "create_client", lambda *_: store)
    monkeypatch.setenv("PHONE_ALLOWLIST", "+15550000001")
    monkeypatch.setattr(outreach, "compose", lambda *_args, **_kwargs: "Check in")
    monkeypatch.setattr(outreach, "send_one", lambda *_: sends.append("sent") or ("SIM-1", "simulated"))
    assert outreach.send_wave("e1", {"r1": 1})["sent"] == 1
    contact = store.rows["contacts"][0]
    contact.update(status="medical", attempts=2, last_inbound="2026-09-14T22:00:00Z")
    before = contact.copy()
    again = outreach.send_wave("e1", {"r1": 1})
    assert again["sent"] == 0 and again["skipped"] == 1
    assert contact == before and sends == ["sent"]


def test_concurrent_contact_claim_does_not_send(monkeypatch):
    import supabase

    store, sends = WaveStore(), []
    original_insert = store.insert

    class Conflict(Exception):
        code = "23505"

    def insert(value):
        if store.name == "contacts":
            raise Conflict()
        return original_insert(value)

    monkeypatch.setattr(store, "insert", insert)
    monkeypatch.setattr(supabase, "create_client", lambda *_: store)
    monkeypatch.setenv("PHONE_ALLOWLIST", "+15550000001")
    monkeypatch.setattr(outreach, "compose", lambda *_args, **_kwargs: "Check in")
    monkeypatch.setattr(outreach, "send_one", lambda *_: sends.append("send"))
    assert outreach.send_wave("e1", {"r1": 1})["skipped"] == 1
    assert sends == []


def test_wave_checks_all_recipients_before_first_send(monkeypatch):
    import supabase

    class Store:
        def schema(self, _): return self
        def table(self, _): return self
        def select(self, *_): return self
        def eq(self, *_): return self
        def execute(self):
            return SimpleNamespace(data=[{"id": "r1", "phone": "+15550000001"},
                                         {"id": "r2", "phone": "+19999999999"}])

    calls = []
    monkeypatch.setattr(supabase, "create_client", lambda *_: Store())
    monkeypatch.setenv("PHONE_ALLOWLIST", "+15550000001")
    monkeypatch.setattr(outreach, "send_one", lambda *_: calls.append("send"))
    with pytest.raises(PermissionError):
        outreach.send_wave("e1", {"r1": 1, "r2": 1})
    assert calls == []


@pytest.mark.parametrize("bad", [
    {"status": "safe"}, {"status": "unreachable"}, {"status": "opted_out"},
    {"need": "medicine"}, {"confidence": 1.1}, {"confidence": -0.1},
    {"confidence": float("nan")}, {"confidence": "0.9"},
    {"quote": "I am perfectly fine"}, {"quote": ""},
])
def test_invalid_model_output_requires_human_review(monkeypatch, bad):
    import strands
    import strands.models

    body = "I feel dizzy"
    value = {"status": "medical", "need": "cooling", "confidence": 0.9,
             "reason": "reported distress", "quote": body, **bad}
    monkeypatch.setattr(strands.models, "BedrockModel", lambda **_: object())
    monkeypatch.setattr(strands, "Agent", lambda **_: lambda _prompt: SimpleNamespace(structured_output=value))
    result, used_model = triage.triage_reply(body, {})
    assert (result.status, result.need, result.confidence, used_model) == ("unclear", "wellness_check", 0.0, False)
    assert result.quote == body


def test_grounded_model_output_and_deterministic_digits(monkeypatch):
    import strands
    import strands.models

    calls = []

    def invoke(prompt):
        calls.append(prompt)
        return SimpleNamespace(structured_output=Triage(status="medical", need="cooling", confidence=0.9, quote="feel dizzy"))

    monkeypatch.setattr(strands.models, "BedrockModel", lambda **_: object())
    monkeypatch.setattr(strands, "Agent", lambda **_: invoke)
    assert triage.triage_reply("1", {})[0].status == "ok"
    assert triage.triage_reply("2", {})[0].status == "needs_help"
    assert calls == []
    result, used_model = triage.triage_reply("I feel dizzy today", {})
    assert used_model and result.quote == "feel dizzy" and result.status == "medical"
    assert len(calls) == 1


def test_console_proxy_rejects_missing_key_before_upstream():
    root = Path(__file__).resolve().parents[1]
    compiler = root / "console/node_modules/typescript"
    if not compiler.exists():
        pytest.skip("console dependencies not installed")
    route = root / "console/app/api/simulate/[op]/route.ts"
    script = r"""
const assert = require('node:assert/strict');
const fs = require('node:fs');
const ts = require(COMPILER);
const compiled = ts.transpileModule(fs.readFileSync(ROUTE, 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 }
}).outputText;
const exported = { exports: {} };
new Function('require', 'module', 'exports', compiled)(name => name === 'next/server'
  ? { NextResponse: { json: (data, options) => ({ data, status: options.status }) } }
  : require(name), exported, exported.exports);
let calls = [];
global.fetch = async (url, options) => { calls.push(options); return { status: 200, json: async () => ({ ok: true }) }; };
process.env.CONSOLE_KEY = 'test-key';
process.env.FUNCTION_URL = 'http://127.0.0.1:9999';
delete process.env.SIMULATE_FUNCTION_URL;
const req = key => ({ headers: { get: () => key }, json: async () => ({ event_id: 'e1', from: '+15550000001', text: '1', op: 'timer' }) });
const context = { params: Promise.resolve({ op: 'resident' }) };
(async () => {
  assert.equal((await exported.exports.POST(req(null), context)).status, 403);
  assert.equal((await exported.exports.POST(req('wrong-key'), context)).status, 403);
  assert.equal(calls.length, 0);
  assert.equal((await exported.exports.POST(req('test-key'), context)).status, 200);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].headers['X-Console-Key'], 'test-key');
  assert.equal(JSON.parse(calls[0].body).op, 'inbound');
  process.env.CONSOLE_KEY = '';
  assert.equal((await exported.exports.POST(req('test-key'), context)).status, 503);
  process.env.CONSOLE_KEY = 'test-key';
  delete process.env.FUNCTION_URL;
  assert.equal((await exported.exports.POST(req('test-key'), context)).status, 503);
  assert.equal(calls.length, 1);
  console.log('console boundary checks passed');
})().catch(error => { console.error(error); process.exitCode = 1; });
""".replace("COMPILER", json.dumps(str(compiler))).replace("ROUTE", json.dumps(str(route)))
    result = subprocess.run(["node", "-e", script], text=True, capture_output=True, timeout=20)
    assert result.returncode == 0, result.stdout + result.stderr
