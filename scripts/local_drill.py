"""Run the real console/workflow against isolated synthetic adapters.

Start with ``python scripts/local_drill.py``. Configure the Next.js console with
SUPABASE_URL=http://127.0.0.1:8765, SUPABASE_ANON_KEY=local-drill,
FUNCTION_URL=http://127.0.0.1:8765, CONSOLE_KEY=local-drill, and LOCAL_DRILL=1.
The key is a public local fixture, not a production credential. Restart to reset.
This harness makes no AWS calls or external sends and is not deployment proof.
"""

from __future__ import annotations

import copy
import html
import importlib
import json
import os
import re
import socket
import sys
from contextlib import ExitStack
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
LABEL = "Local synthetic drill; model and Telegram adapters simulated"
KEY = "local-drill"
OWNER = "+12025550100"
TABLES = {"hazard_events", "residents", "contacts", "audit_log", "dispatches",
          "gate_pending", "volunteers", "resources", "protocol", "escalations"}


class Query:
    """Small in-memory adapter for the query methods these handlers actually use."""

    def __init__(self, db, name):
        self.db, self.name = db, name
        self.filters, self.op, self.payload = [], "select", None
        self.sort, self.cap, self.columns, self.conflict = None, None, "*", "id"

    def select(self, columns="*"):
        self.columns = columns
        return self

    def eq(self, key, value):
        self.filters.append(lambda row: row.get(key) == value)
        return self

    def ilike(self, key, value):
        pattern = re.compile("^" + re.escape(value).replace("%", ".*").replace("_", ".") + "$", re.I)
        self.filters.append(lambda row: bool(pattern.match(str(row.get(key, "")))))
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

    def upsert(self, payload, on_conflict="id"):
        self.op, self.payload, self.conflict = "upsert", payload, on_conflict
        return self

    def update(self, payload):
        self.op, self.payload = "update", payload
        return self

    def execute(self):
        table = self.db.rows[self.name]
        if self.op in ("insert", "upsert"):
            result = []
            for payload in self.payload if isinstance(self.payload, list) else [self.payload]:
                row = None
                if self.op == "upsert":
                    keys = self.conflict.split(",")
                    row = next((r for r in table if all(r.get(k) == payload.get(k) for k in keys)), None)
                if row is None:
                    row = copy.deepcopy(payload)
                    self.db.counter += 1
                    row.setdefault("id", f"local-{self.name}-{self.db.counter}")
                    row.setdefault("created_at", datetime.now(timezone.utc).isoformat())
                    if self.name == "gate_pending":
                        row.setdefault("status", "open")
                    table.append(row)
                else:
                    row.update(copy.deepcopy(payload))
                self.db.trace(self.op, self.name, row)
                result.append(row)
        else:
            result = [row for row in table if all(check(row) for check in self.filters)]
            if self.sort:
                key, desc = self.sort
                result.sort(key=lambda row: row.get(key) or "", reverse=desc)
            if self.cap is not None:
                result = result[:self.cap]
            if self.op == "update":
                for row in result:
                    row.update(copy.deepcopy(self.payload))
                    self.db.trace("update", self.name, row)
        result = copy.deepcopy(result)
        if "residents(" in self.columns:
            for row in result:
                resident = next((r for r in self.db.rows["residents"] if r["id"] == row.get("resident_id")), {})
                row["residents"] = {"name": resident.get("name")}
        return SimpleNamespace(data=result)


class Drill:
    def __init__(self, log=True):
        from scripts.seed import build_rows

        self.counter, self.outbox, self.log = 0, [], log
        self.rows = {name: [] for name in TABLES}
        self.rows.update(build_rows(OWNER))
        for index, resident in enumerate(self.rows["residents"]):
            resident.update(id=f"resident-{index + 1}", phone=f"+120255501{index:02d}",
                            emergency_contact=f"+120255501{index + 40:02d}", opted_out=False)
        for index, volunteer in enumerate(self.rows["volunteers"]):
            volunteer.update(id=f"volunteer-{index + 1}", phone=OWNER if index == 0 else f"+120255501{index + 80:02d}")
        for index, resource in enumerate(self.rows["resources"]):
            resource.update(id=f"resource-{index + 1}", phone=f"+120255501{index + 90:02d}")
        self.allowlist = {value for name in ("residents", "volunteers", "resources")
                          for row in self.rows[name] for key, value in row.items()
                          if key in ("phone", "emergency_contact")}
        if not all(re.fullmatch(r"\+120255501\d{2}", phone) for phone in self.allowlist):
            raise ValueError("Local drill requires exclusively fictional phone numbers")

    def schema(self, name):
        if name != "porchlight":
            raise ValueError("unsupported schema")
        return self

    def table(self, name):
        if name not in TABLES:
            raise ValueError("unsupported table")
        return Query(self, name)

    def trace(self, op, table, row):
        if self.log:
            print(json.dumps({"drill_change": op, "table": table,
                              **{k: row[k] for k in ("id", "resident_id", "status", "action", "detail") if k in row}},
                             ensure_ascii=False), flush=True)

    def capture_send(self, sb, to_phone, from_number, body, owner_phone):
        from agent.safety import assert_allowed

        assert_allowed(to_phone, self.allowlist)
        if not body.strip():
            return "", "failed"
        message = {"id": f"LOCAL-{len(self.outbox) + 1}", "to": to_phone, "body": body,
                   "channel": "simulated", "created_at": datetime.now(timezone.utc).isoformat()}
        self.outbox.append(message)
        self.trace("capture", "local_outbox", {**message, "detail": body})
        return message["id"], "simulated"

    @staticmethod
    def fixture_triage(body, resident):
        from agent.models import Triage
        from agent.triage import short_circuit

        deterministic = short_circuit(body)
        if deterministic is not None:
            return deterministic, False
        distress = body.strip().lower() in {"ac broke, dizzy", "i feel dizzy"}
        return Triage(status="medical" if distress else "unclear",
                      need="cooling" if distress else "wellness_check", confidence=0.0,
                      quote=body, reason="Local fixture adapter; no model was called"), False

    def __enter__(self):
        from agent import app as runtime, inbound, outreach, triage
        import supabase

        self.handlers = importlib.import_module("lambda.handlers")
        self.stack = ExitStack()
        self.stack.enter_context(patch.dict(os.environ, {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "PYTHON_DOTENV_DISABLED": "1", "AWS_EC2_METADATA_DISABLED": "true",
            "AWS_CONFIG_FILE": "/dev/null", "AWS_SHARED_CREDENTIALS_FILE": "/dev/null",
            "OWNER_PHONE": OWNER, "PHONE_ALLOWLIST": ",".join(sorted(self.allowlist)),
            "CONSOLE_KEY": KEY, "ROSTER_MODE": "synthetic", "SUPABASE_URL": "http://127.0.0.1:8765",
            "SUPABASE_SERVICE_KEY": KEY, "TELEGRAM_BOT_USERNAME": "local-drill",
        }, clear=True))
        self.stack.enter_context(patch.object(runtime, "_config", dict(os.environ)))
        self.stack.enter_context(patch.object(supabase, "create_client", lambda *_a, **_k: self))
        self.stack.enter_context(patch.object(self.handlers, "_runtime", lambda payload, suffix: runtime.porchlight(payload)))
        self.stack.enter_context(patch.object(outreach, "send_one", self.capture_send))
        self.stack.enter_context(patch.object(outreach, "reviewed_template", lambda lang: outreach.TEMPLATES[lang]))
        self.stack.enter_context(patch.object(inbound, "triage_reply", self.fixture_triage))
        self.stack.enter_context(patch.object(triage, "triage_reply", self.fixture_triage))
        original_connect = socket.socket.connect

        def loopback_only(sock, address):
            if not isinstance(address, tuple) or address[0] not in ("127.0.0.1", "::1"):
                raise PermissionError("Local drill blocks external network connections")
            return original_connect(sock, address)

        self.stack.enter_context(patch.object(socket.socket, "connect", loopback_only))
        return self

    def __exit__(self, *args):
        return self.stack.__exit__(*args)

    def invoke(self, payload, key=KEY):
        if not isinstance(payload, dict) or payload.get("op") not in ("inject", "resident", "inbound", "coordinator", "volunteer"):
            return 400, {"error": "unsupported local drill operation"}
        response = self.handlers.telegram_inbound_handler({"headers": {"X-Console-Key": key},
                            "body": json.dumps(payload)}, None)
        result = json.loads(response["body"])
        result["_drill"] = LABEL
        return response["statusCode"], result

    def read(self, table, params):
        query = self.table(table)
        for key, values in params.items():
            value = values[0]
            if key == "select":
                query.select(value)
            elif key == "order":
                column, _, direction = value.partition(".")
                if direction not in ("asc", "desc", ""):
                    raise ValueError("unsupported order")
                query.order(column, desc=direction == "desc")
            elif key == "limit":
                query.limit(max(0, min(1000, int(value))))
            elif value.startswith("eq."):
                value = value[3:]
                query.eq(key, {"true": True, "false": False}.get(value, value))
            elif value.startswith("ilike.") and len(value) < 300:
                query.ilike(key, value[6:])
            else:
                raise ValueError("unsupported local query")
        return query.execute().data

    def outbox_html(self):
        esc = lambda value: html.escape(str(value))
        messages = "".join(f'<article><small>{esc(m["id"])} · {esc(m["created_at"])} · simulated adapter</small>'
                           f'<p>{esc(m["body"])}</p></article>' for m in reversed(self.outbox))
        states = json.dumps({"gate_pending": self.rows["gate_pending"], "dispatches": self.rows["dispatches"]}, indent=2)
        return (f'<!doctype html><html lang="en"><meta charset="utf-8"><meta http-equiv="refresh" content="3">'
                f'<title>Porchlight local drill outbox</title><style>body{{max-width:1000px;margin:40px auto;padding:20px;font:18px system-ui;background:#fffaf0;color:#292524}}'
                'article,pre{padding:18px;border:1px solid #d6d3d1;border-radius:12px;background:white;white-space:pre-wrap;overflow-wrap:anywhere;margin:12px 0}small{color:#57534e}p{line-height:1.5}</style>'
                f'<h1>Porchlight · captured messages</h1><p><strong>{LABEL}</strong></p>'
                '<p>In-memory synthetic database. These messages were emitted by the workflow and captured locally; none were delivered.</p>'
                f'<p>{len(self.outbox)} captured messages · <a href="http://127.0.0.1:3000">Open console</a></p>'
                f'{messages or "<p>No messages yet. Inject a heat drill in the console.</p>"}'
                f'<h2>Current gate and dispatch records</h2><pre>{esc(states)}</pre></html>')


def make_server(drill, port=8765):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def respond(self, status, data, content_type="application/json"):
            body = (json.dumps(data, ensure_ascii=False) if content_type == "application/json" else data).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type + "; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            url = urlsplit(self.path)
            if url.path == "/drill/outbox":
                return self.respond(200, drill.outbox_html(), "text/html")
            if url.path == "/drill/status":
                return self.respond(200, {"mode": LABEL, "database": "in-memory synthetic", "external_sends": 0})
            if not url.path.startswith("/rest/v1/"):
                return self.respond(404, {"error": "not found"})
            if self.headers.get("apikey") != KEY:
                return self.respond(403, {"error": "invalid local key"})
            try:
                rows = drill.read(url.path.removeprefix("/rest/v1/"), parse_qs(url.query))
                self.respond(200, rows)
            except ValueError as exc:
                self.respond(400, {"error": str(exc)})

        def do_POST(self):
            if urlsplit(self.path).path != "/":
                return self.respond(404, {"error": "not found"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 1024 * 1024:
                    return self.respond(413, {"error": "invalid body size"})
                payload = json.loads(self.rfile.read(length))
                status, result = drill.invoke(payload, self.headers.get("X-Console-Key", ""))
                self.respond(status, result)
            except (ValueError, TypeError, KeyError):
                self.respond(400, {"error": "invalid local payload"})
            except Exception as exc:
                print(f"local_drill_error={type(exc).__name__}", flush=True)
                self.respond(500, {"error": type(exc).__name__, "_drill": LABEL})

    return HTTPServer(("127.0.0.1", port), Handler)


def main():
    os.chdir(ROOT)
    with Drill() as drill, make_server(drill) as server:
        print(LABEL, flush=True)
        print("http://127.0.0.1:8765/drill/outbox · public local key: local-drill", flush=True)
        print("Fictional roster only; external network connections blocked; restart resets memory.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
