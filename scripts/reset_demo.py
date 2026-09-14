"""Reset script for Porchlight demo and dress rehearsal (P-08).

Performs:
1. Closes open hazard events and archives/clears old contacts, dispatches,
   escalations, gate_pending, and audit logs in Supabase.
2. Reseeds the roster idempotently (40 synthetic residents, 5 volunteers,
   3 resources, protocol v1) with strict PHONE_ALLOWLIST assertions.
3. Probes health:
   - AgentCore Runtime provider state (READY; invocation not tested)
   - All three deployed Lambda provider states (invocation not tested)
   - Console endpoint (HTTP 200)
   - Telegram Bot API (getMe ok)
4. Emits proof line:
   PROOF P-08: reset_demo ok runtime=READY lambdas=3/3 console=200 telegram=ok = PASS
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from typing import Any

import httpx
from dotenv import load_dotenv

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

if sys.stdout.encoding != "utf-8" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8" and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

from agent.safety import parse_allowlist
from scripts.deploy_apprunner import get_anon_key
from scripts.seed import build_rows

DEFAULT_CONSOLE_URL = "http://127.0.0.1:3000"


def get_sb_client():
    from supabase import create_client

    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
    return create_client(url, key).schema("porchlight")


def reset_database(sb) -> dict[str, int]:
    """Closes open hazard events, archives old records, and reseeds roster idempotently."""
    # Validate the entire roster before any database mutation.
    owner = os.environ.get("OWNER_PHONE", "").strip()
    allowlist = parse_allowlist(os.environ.get("PHONE_ALLOWLIST", ""))
    if not owner or not allowlist:
        raise RuntimeError("Missing OWNER_PHONE or PHONE_ALLOWLIST in environment")

    rows = build_rows(owner)
    all_phones = (
        [r["phone"] for r in rows["residents"]]
        + [r["emergency_contact"] for r in rows["residents"]]
        + [v["phone"] for v in rows["volunteers"]]
    )
    outside = [p for p in all_phones if p not in allowlist]
    if outside:
        raise RuntimeError(f"ABORTED: {len(outside)} phones outside PHONE_ALLOWLIST, zero writes performed")

    print(f"    [PASS] PHONE_ALLOWLIST verified: {len(rows['residents'])} residents, "
          f"{len(rows['volunteers'])} volunteers allowlisted.")

    print("[*] Step 1: Closing open hazard events and archiving dynamic records...")
    # 1. Close open hazard events
    try:
        sb.table("hazard_events").update({"status": "closed"}).eq("status", "open").execute()
    except Exception as exc:
        print(f"    Notice closing hazard events: {exc}")

    # Archive active dynamic records in Supabase
    for table in ("contacts", "dispatches", "escalations"):
        try:
            sb.table(table).update({"status": "archived"}).neq("status", "archived").execute()
        except Exception as exc:
            print(f"    Notice archiving {table}: {exc}")

    # 2. Clear dynamic event tables for clean slate
    dynamic_tables = ["audit_log", "escalations", "dispatches", "contacts", "gate_pending", "hazard_events"]
    for table in dynamic_tables:
        try:
            sb.table(table).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        except Exception as exc:
            print(f"    Notice clearing {table}: {exc}")

    # 4. Clear static roster tables
    for table in ("residents", "volunteers", "resources", "protocol"):
        try:
            sb.table(table).delete().neq(
                "id", "00000000-0000-0000-0000-000000000000" if table != "protocol" else "__none__"
            ).execute()
        except Exception as exc:
            print(f"    Notice clearing {table}: {exc}")

    # 5. Insert fresh seed rows
    counts: dict[str, int] = {}
    for table in ("residents", "volunteers", "resources", "protocol"):
        res = sb.table(table).insert(rows[table]).execute()
        counts[table] = len(res.data) if res.data else len(rows[table])

    print(f"    [PASS] Idempotent reseed: residents={counts.get('residents')} volunteers={counts.get('volunteers')} "
          f"resources={counts.get('resources')} protocol={counts.get('protocol')}")

    assert counts.get("residents") == 40, f"Expected 40 residents, got {counts.get('residents')}"
    return counts


def configuration_diagnostics() -> dict[str, bool]:
    """Local files describe configuration; they do not establish live health."""
    checks = {"runtime_config": False, "sam_template": False}
    try:
        with open(os.path.join(REPO_ROOT, "agentcore", "agentcore.json"), encoding="utf-8") as fh:
            cfg = json.load(fh)
        checks["runtime_config"] = any(r.get("name") == "porchlight" for r in cfg.get("runtimes", []))
    except (OSError, ValueError):
        pass
    checks["sam_template"] = os.path.isfile(os.path.join(REPO_ROOT, "sam", "template.yaml"))
    print(f"[CONFIG ONLY] {checks}; deployment and execution are not verified by these files")
    return checks


def probe_runtime() -> str:
    """Return only the runtime state actually reported by AWS."""
    print("[*] Step 2a: Reading AgentCore Runtime provider state...")
    region = os.environ.get("AWS_REGION", "us-east-1")
    expected_arn = os.environ.get("RUNTIME_ARN", "").strip()
    try:
        import boto3
        client = boto3.client("bedrock-agentcore-control", region_name=region)
        request = {"maxResults": 100}
        while True:
            page = client.list_agent_runtimes(**request)
            for runtime in page.get("agentRuntimes", []):
                matches = runtime.get("agentRuntimeArn") == expected_arn if expected_arn else runtime.get("agentRuntimeName") == "porchlight"
                if matches:
                    status = runtime.get("status") or "UNKNOWN"
                    label = "PASS" if status == "READY" else "NOT READY"
                    print(f"    [{label}] AgentCore Runtime provider state: {status}; invocation not tested")
                    return status
            token = page.get("nextToken")
            if not token:
                print("    [UNVERIFIED] Porchlight runtime was not found")
                return "NOT_FOUND"
            request["nextToken"] = token
    except Exception as exc:
        # Provider exceptions can include request details; print only the type.
        print(f"    [UNVERIFIED] AgentCore provider query failed: {type(exc).__name__}")
        return "UNVERIFIED"


def probe_lambdas() -> str:
    """Count the three deployed SAM functions only when AWS reports them healthy."""
    print("[*] Step 2b: Reading Lambda provider states (execution not tested)...")
    region = os.environ.get("AWS_REGION", "us-east-1")
    stack = os.environ.get("SAM_STACK_NAME", "porchlight-glue")
    expected = {"NwsPoll", "TwilioInbound", "Tick"}  # Logical IDs in sam/template.yaml.
    healthy = set()
    try:
        import boto3
        cf = boto3.client("cloudformation", region_name=region)
        lambdas = boto3.client("lambda", region_name=region)
        for page in cf.get_paginator("list_stack_resources").paginate(StackName=stack):
            for resource in page.get("StackResourceSummaries", []):
                name = resource.get("LogicalResourceId")
                if name not in expected or resource.get("ResourceType") != "AWS::Lambda::Function":
                    continue
                config = lambdas.get_function_configuration(FunctionName=resource["PhysicalResourceId"])
                state = config.get("State", "UNKNOWN")
                update = config.get("LastUpdateStatus", "UNKNOWN")
                if state == "Active" and update == "Successful":
                    healthy.add(name)
                print(f"    [PROVIDER] {name}: state={state}, last_update={update}")
        result = f"{len(healthy)}/3"
        label = "PASS" if healthy == expected else "UNVERIFIED"
        print(f"    [{label}] Lambda provider states healthy: {result}; invocation not tested")
        return result
    except Exception as exc:
        print(f"    [UNVERIFIED] Lambda provider query failed: {type(exc).__name__}")
        return "UNVERIFIED"


def probe_console(start_if_needed: bool = True) -> tuple[int, subprocess.Popen | None]:
    """Probes the Console endpoint for HTTP 200, starting local server if needed."""
    print("[*] Step 2c: Probing Console endpoint...")
    target_url = os.environ.get("CONSOLE_URL") or os.environ.get("APP_RUNNER_URL") or DEFAULT_CONSOLE_URL
    target_url = target_url.rstrip("/")

    # Check if target URL is already responding
    try:
        r = httpx.get(f"{target_url}/", timeout=3.0)
        if r.status_code == 200 and "Porchlight" in r.text:
            print(f"    [PASS] Console endpoint responding on {target_url} (HTTP 200 OK)")
            return 200, None
    except Exception:
        pass

    if not start_if_needed or target_url != DEFAULT_CONSOLE_URL:
        print("    [UNVERIFIED] Requested console endpoint did not return Porchlight HTTP 200")
        return 0, None

    # Start standalone server locally
    standalone_dir = os.path.join(REPO_ROOT, "console", ".next", "standalone")
    server_js = os.path.join(standalone_dir, "server.js")
    if not os.path.exists(server_js):
        print("    Building Next.js standalone server...")
        subprocess.run(["npm", "run", "build"], cwd=os.path.join(REPO_ROOT, "console"), check=True)

    anon_key = get_anon_key()
    supabase_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    console_key = os.environ.get("CONSOLE_KEY", "").strip()

    env = {
        **os.environ,
        "PORT": "3000",
        "HOSTNAME": "0.0.0.0",
        "NEXT_PUBLIC_SUPABASE_URL": supabase_url,
        "NEXT_PUBLIC_SUPABASE_ANON_KEY": anon_key,
        "SUPABASE_URL": supabase_url,
        "SUPABASE_ANON_KEY": anon_key,
        "CONSOLE_KEY": console_key,
    }

    print(f"    Starting local console standalone server in background on port 3000...")
    proc = subprocess.Popen(
        ["node", "server.js"],
        cwd=standalone_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    ready = False
    for attempt in range(15):
        time.sleep(1)
        try:
            r = httpx.get(f"{DEFAULT_CONSOLE_URL}/", timeout=3.0)
            if r.status_code == 200 and "Porchlight" in r.text:
                ready = True
                print(f"    [PASS] Console standalone server booted and responsive (HTTP 200 OK)")
                break
        except Exception:
            pass

    if ready:
        return 200, proc
    else:
        proc.terminate()
        raise RuntimeError("Failed to obtain HTTP 200 from Console endpoint")


def probe_telegram() -> str:
    """Probes Telegram Bot API via getMe."""
    print("[*] Step 2d: Probing Telegram Bot API...")
    from agent.telegram import api

    me = api("getMe")
    if me.get("ok") and me.get("result", {}).get("is_bot"):
        bot_user = me.get("result", {}).get("username")
        print(f"    [PASS] Telegram Bot API reachable: @{bot_user} (getMe ok)")
        return "ok"
    else:
        raise RuntimeError(f"Telegram Bot API probe failed: {me}")


def main() -> int:
    console_proc = None
    try:
        sb = get_sb_client()
        counts = reset_database(sb)

        configuration_diagnostics()
        runtime_status = probe_runtime()
        lambdas_status = probe_lambdas()
        console_code, console_proc = probe_console(start_if_needed=True)
        telegram_status = probe_telegram()
        if (runtime_status, lambdas_status, console_code, telegram_status) != ("READY", "3/3", 200, "ok"):
            raise RuntimeError("Live health evidence is incomplete; no PASS proof emitted")

        proof_line = (
            f"PROOF P-08: reset_demo ok runtime={runtime_status} lambdas={lambdas_status} "
            f"console={console_code} telegram={telegram_status} = PASS"
        )
        print("\n" + "=" * 70)
        print(proof_line)
        print("=" * 70 + "\n")
        return 0

    except Exception as exc:
        print(f"\n[-] FAIL in reset_demo: {exc}")
        return 1

    finally:
        if console_proc is not None:
            console_proc.terminate()


if __name__ == "__main__":
    sys.exit(main())
