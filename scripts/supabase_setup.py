"""One-shot Supabase setup for P-00 (stdlib only, no third-party imports).

Reads SUPABASE_PAT, SUPABASE_URL from .env (never prints values) and:
  1. Creates the `porchlight` schema via the Management API query endpoint.
  2. Adds `porchlight` to the PostgREST exposed schemas (db_schema).
  3. Verifies both and prints status lines (names and codes only).

Usage: python scripts/supabase_setup.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request

REF_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")


def load_env(path: str) -> dict[str, str]:
    values: dict[str, str] = {}
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            values[key.strip()] = val.strip().strip('"').strip("'")
    return values


def api(method: str, path: str, pat: str, body: dict | None = None) -> tuple[int, str]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"https://api.supabase.com{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {pat}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()[:200]


def main() -> int:
    env = load_env(REF_FILE)
    pat = env.get("SUPABASE_PAT", "")
    project_url = env.get("SUPABASE_URL", "").rstrip("/")
    if not pat or not project_url:
        print("supabase_setup=BLOCKED missing SUPABASE_PAT or SUPABASE_URL in .env")
        return 2
    try:
        ref = project_url.split("https://", 1)[1].split(".", 1)[0]
    except IndexError:
        print("supabase_setup=BLOCKED malformed SUPABASE_URL")
        return 2

    ok = True

    status, _ = api(
        "POST", f"/v1/projects/{ref}/database/query", pat,
        {"query": "create schema if not exists porchlight;"},
    )
    print(f"supabase_schema={'PASS' if status == 201 else 'FAIL'} http={status}")
    ok = ok and status == 201

    status, payload = api("GET", f"/v1/projects/{ref}/postgrest", pat)
    schemas = ""
    if status == 200:
        try:
            schemas = json.loads(payload).get("db_schema", "") or ""
        except json.JSONDecodeError:
            status = 500
    print(f"postgrest_read={'PASS' if status == 200 else 'FAIL'} http={status}")
    ok = ok and status == 200

    if status == 200:
        current = [s.strip() for s in schemas.split(",") if s.strip()]
        if "porchlight" not in current:
            current.append("porchlight")
            status, _ = api(
                "PATCH", f"/v1/projects/{ref}/postgrest", pat,
                {"db_schema": ",".join(current)},
            )
            print(f"postgrest_expose={'PASS' if status == 200 else 'FAIL'} http={status}")
            ok = ok and status == 200
        else:
            print("postgrest_expose=PASS already-exposed")

    status, payload = api(
        "POST", f"/v1/projects/{ref}/database/query", pat,
        {"query": "select schema_name from information_schema.schemata where schema_name='porchlight';"},
    )
    verified = status == 201 and "porchlight" in payload
    print(f"supabase_verify={'PASS' if verified else 'FAIL'} http={status}")
    ok = ok and verified

    print(f"PROOF supabase_setup={'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
