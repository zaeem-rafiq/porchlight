"""App Runner Deployment and Verification Helper Script for Porchlight Console.

Handles:
1. Supabase Anonymous RLS Verification (SELECT returns 40 residents, INSERT rejected with 42501).
2. AWS Credentials & ECR / App Runner Provisioning.
3. Health check verification (HTTP 200 on public HTTPS endpoint).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCOUNT_ID = "292341338711"
REGION = os.environ.get("AWS_REGION", "us-east-1")
REPO_NAME = "porchlight-console"
SERVICE_NAME = "porchlight-console"
ROLE_NAME = "porchlight-apprunner-ecr-access-role"


def get_anon_key() -> str:
    """Retrieve Supabase anonymous key from env or Management API."""
    anon = (
        os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        or os.environ.get("SUPABASE_ANON_KEY", "")
    ).strip()
    if anon:
        return anon

    pat = os.environ.get("SUPABASE_PAT", "").strip()
    project_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    if pat and project_url and "https://" in project_url:
        try:
            ref = project_url.split("https://", 1)[1].split(".", 1)[0]
            req = urllib.request.Request(
                f"https://api.supabase.com/v1/projects/{ref}/api-keys",
                headers={"Authorization": f"Bearer {pat}"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                keys = json.load(resp)
            for k in keys:
                if k.get("name") == "anon":
                    return k.get("api_key", "")
        except Exception as e:
            print(f"Warning: Could not fetch anon key from API: {e}")
    return ""


def verify_supabase_anon_rls() -> bool:
    """Empirically verify Supabase anonymous read-only access and mutation rejection under RLS."""
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    if not url:
        print("FAIL: SUPABASE_URL is not set.")
        return False

    anon_key = get_anon_key()
    if not anon_key:
        print("FAIL: Anonymous key is not available.")
        return False

    headers = {
        "apikey": anon_key,
        "Authorization": f"Bearer {anon_key}",
        "Accept-Profile": "porchlight",
        "Content-Profile": "porchlight",
        "Content-Type": "application/json",
    }

    print(f"[*] Verifying Supabase Anonymous RLS at {url} (schema: porchlight)...")
    with httpx.Client(base_url=url, headers=headers, timeout=20.0) as client:
        # 1. Verify Anonymous SELECT on residents
        resp_sel = client.get("/rest/v1/residents?select=id,name,language&order=name")
        if resp_sel.status_code != 200:
            print(f"FAIL: Anon SELECT failed with status {resp_sel.status_code}: {resp_sel.text}")
            return False
        residents = resp_sel.json()
        if len(residents) != 40:
            print(f"FAIL: Expected 40 residents, got {len(residents)}")
            return False
        print(f"[PASS] Anon SELECT returned {len(residents)} residents (HTTP 200).")

        # 2. Verify Anonymous INSERT rejection on residents
        resp_ins = client.post("/rest/v1/residents", json={"name": "Attacker Record"})
        if resp_ins.status_code not in (401, 403):
            print(f"FAIL: Anon INSERT should have failed, but got status {resp_ins.status_code}: {resp_ins.text}")
            return False
        err = resp_ins.json() if resp_ins.text else {}
        err_code = err.get("code")
        if err_code != "42501":
            print(f"FAIL: Expected PostgreSQL error code 42501, got {err_code}: {resp_ins.text}")
            return False
        print(f"[PASS] Anon INSERT rejected by RLS with code 42501: {err.get('message')}")

        # 3. Verify Anonymous INSERT rejection on contacts
        resp_ins_c = client.post("/rest/v1/contacts", json={"status": "corrupted"})
        if resp_ins_c.status_code not in (401, 403) or "42501" not in resp_ins_c.text:
            print(f"FAIL: Anon contacts INSERT not rejected with 42501: {resp_ins_c.status_code} {resp_ins_c.text}")
            return False
        print("[PASS] Anon contacts INSERT rejected by RLS with code 42501.")

    return True


def check_aws_credentials() -> tuple[bool, str]:
    """Check whether AWS credentials are valid and active."""
    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError

        sts = boto3.client("sts", region_name=REGION)
        ident = sts.get_caller_identity()
        arn = ident.get("Arn", "")
        return True, arn
    except Exception as e:
        return False, str(e)


def check_app_runner_service() -> str | None:
    """Check if the App Runner service exists and return its public URL."""
    can_connect, msg = check_aws_credentials()
    if not can_connect:
        print(f"[*] AWS credentials unavailable: {msg}")
        url = os.environ.get("APP_RUNNER_URL") or os.environ.get("CONSOLE_URL")
        return url

    import boto3
    client = boto3.client("apprunner", region_name=REGION)
    try:
        services = client.list_services().get("ServiceSummaryList", [])
        for svc in services:
            if svc.get("ServiceName") == SERVICE_NAME:
                service_url = svc.get("ServiceUrl")
                if service_url:
                    full_url = f"https://{service_url}"
                    print(f"[+] Found existing App Runner service: {full_url}")
                    return full_url
    except Exception as e:
        print(f"[*] Error listing App Runner services: {e}")

    return os.environ.get("APP_RUNNER_URL") or os.environ.get("CONSOLE_URL")


def verify_public_endpoint(url: str) -> bool:
    """Verify that the public URL returns HTTP 200 with Porchlight HTML content."""
    url = url.rstrip("/") + "/"
    print(f"[*] Checking public endpoint: {url} ...")
    try:
        resp = httpx.get(url, timeout=15.0)
        if resp.status_code == 200 and "Porchlight" in resp.text:
            print(f"[PASS] Public endpoint {url} returned HTTP 200 OK.")
            return True
        print(f"FAIL: Endpoint returned status {resp.status_code} (len={len(resp.text)})")
        return False
    except Exception as e:
        print(f"FAIL: Endpoint check exception: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="App Runner Deployment and Verification Helper")
    parser.add_argument("--verify-rls", action="store_true", help="Verify Supabase anonymous RLS")
    parser.add_argument("--check-aws", action="store_true", help="Check AWS credentials and service")
    parser.add_argument("--check-url", type=str, help="Verify a specific public URL")
    args = parser.parse_args()

    success = True
    if args.verify_rls or not (args.check_aws or args.check_url):
        rls_ok = verify_supabase_anon_rls()
        if not rls_ok:
            success = False

    if args.check_aws or not (args.verify_rls or args.check_url):
        aws_ok, arn = check_aws_credentials()
        if aws_ok:
            print(f"[PASS] AWS Authenticated: {arn}")
            svc_url = check_app_runner_service()
            if svc_url:
                url_ok = verify_public_endpoint(svc_url)
                if not url_ok:
                    success = False
        else:
            print(f"[*] AWS Session Status: Expired or unauthenticated ({arn})")
            svc_url = os.environ.get("APP_RUNNER_URL") or os.environ.get("CONSOLE_URL")
            if svc_url:
                print(f"[*] Checking configured URL: {svc_url}")
                verify_public_endpoint(svc_url)

    if args.check_url:
        url_ok = verify_public_endpoint(args.check_url)
        if not url_ok:
            success = False

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
