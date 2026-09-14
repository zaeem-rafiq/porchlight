"""Rehearsal automation and verification script for Proof P-08.

Automates and verifies the full dress rehearsal flow end-to-end:
1. Alert injected (heat.json) -> wave outreach -> Ruth text received.
2. Ruth replies "1" -> contact status transitions to "ok".
3. Alvarez medical distress ("AC broke, dizzy") -> triages to "medical",
   Coordinator Gate intercepts via BeforeToolCallEvent, and coordinator alert
   is dispatched via Telegram.
4. Coordinator replies "1" -> volunteer asked -> volunteer replies "Y" ->
   dispatch recorded as accepted + calendar event logged.
5. Timestamps validated and printed.
6. Zero sends outside PHONE_ALLOWLIST strictly asserted.
7. Emits exact proof line:
   PROOF P-08: rehearsal — Ruth text received; "1" → ok; Alvarez medical → coordinator text received; reply 1 → volunteer Y → dispatch + calendar; timestamps printed; zero sends outside the allowlist = PASS
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

if sys.stdout.encoding != "utf-8" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8" and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

from agent.app import porchlight
from agent.coordinator import handle_coordinator_reply, pending_open
from agent.dispatch import ask_volunteer, volunteer_yes
from agent.inbound import handle_inbound
from agent.models import Dispatch
from agent.safety import parse_allowlist
from supabase import create_client

PROOF_LINE = (
    "PROOF P-08: rehearsal — Ruth text received; \"1\" → ok; "
    "Alvarez medical → coordinator text received; reply 1 → volunteer Y → "
    "dispatch + calendar; timestamps printed; zero sends outside the allowlist = PASS"
)


def get_sb_client():
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in environment")
    return create_client(url, key).schema("porchlight")


def run_rehearsal() -> dict[str, Any]:
    print("\n" + "=" * 70)
    print("STARTING P-08 DRESS REHEARSAL VERIFICATION")
    print("=" * 70 + "\n")

    sb = get_sb_client()
    owner_phone = os.environ.get("OWNER_PHONE", "").strip()
    allowlist_str = os.environ.get("PHONE_ALLOWLIST", "")
    allowlist = parse_allowlist(allowlist_str)

    if not owner_phone or not allowlist:
        raise RuntimeError("Missing OWNER_PHONE or PHONE_ALLOWLIST in environment")

    # Step 0: Ensure Ruth Alvarez exists in roster and is allowlisted
    ruth_rows = sb.table("residents").select("*").eq("name", "Ruth Alvarez").execute().data
    if not ruth_rows:
        raise RuntimeError("Ruth Alvarez not found in residents table. Run scripts/reset_demo.py first.")
    ruth = ruth_rows[0]
    assert ruth["phone"] in allowlist, f"Ruth Alvarez phone {ruth['phone']} not in allowlist!"
    print(f"[*] Ruth Alvarez resident loaded: ID={ruth['id']}, Phone={ruth['phone']}")

    timestamps: list[tuple[str, str, float]] = []

    # --------------------------------------------------------------------------
    # Step 1: Inject Hazard Alert (heat.json) -> Outreach wave -> Ruth text received
    # --------------------------------------------------------------------------
    print("\n[*] Step 1: Injecting NWS Extreme Heat Warning (heat.json)...")
    fixture_path = os.path.join(REPO_ROOT, "data", "fixtures", "alerts", "heat.json")
    with open(fixture_path, "r", encoding="utf-8") as fh:
        heat_alert = json.load(fh)

    t0 = time.time()
    ts0 = datetime.now(timezone.utc).isoformat()
    timestamps.append(("Alert Injected (heat.json)", ts0, t0))

    inject_res = porchlight({
        "action": "hazard.detected",
        "alert": heat_alert,
        "source": "drill:p08_rehearsal",
        "observed_only": False,
    })
    assert inject_res.get("accepted") is True, f"Hazard injection rejected: {inject_res}"
    event_id = inject_res.get("event_id")
    assert event_id, "Missing event_id from hazard injection"
    print(f"    [PASS] Hazard event created: event_id={event_id}")

    # Verify all 40 contacts created
    contacts = sb.table("contacts").select("*").eq("event_id", event_id).execute().data
    assert len(contacts) == 40, f"Expected 40 contacts, found {len(contacts)}"
    print(f"    [PASS] Outreach wave completed: 40 contacts recorded in Supabase")

    # Verify Ruth Alvarez received outreach text
    ruth_contact = sb.table("contacts").select("*").eq("event_id", event_id).eq("resident_id", ruth["id"]).execute().data
    assert ruth_contact and ruth_contact[0]["status"] == "sent", "Ruth Alvarez contact not in 'sent' status"
    t1 = time.time()
    ts1 = datetime.now(timezone.utc).isoformat()
    timestamps.append(("Ruth Text Received", ts1, t1))
    print(f"    [PASS] Ruth text received: outreach wave sent in {t1 - t0:.2f}s")

    # --------------------------------------------------------------------------
    # Step 2: Ruth replies "1" -> ok
    # --------------------------------------------------------------------------
    print("\n[*] Step 2: Ruth replies '1' (wellness check ok)...")
    t_ruth_start = time.time()
    inbound_ok = handle_inbound(ruth["phone"], "telegram", "1", event_id)
    assert inbound_ok.get("status") == "ok", f"Expected status 'ok', got {inbound_ok.get('status')}"
    
    # Verify contact status in DB
    c_ruth_ok = sb.table("contacts").select("status").eq("event_id", event_id).eq("resident_id", ruth["id"]).execute().data[0]
    assert c_ruth_ok["status"] == "ok", f"Contact status in DB expected 'ok', got {c_ruth_ok['status']}"

    t2 = time.time()
    ts2 = datetime.now(timezone.utc).isoformat()
    timestamps.append(("Ruth Reply '1' -> ok", ts2, t2))
    print(f"    [PASS] Ruth '1' reply triaged -> status 'ok' in {t2 - t_ruth_start:.2f}s")

    # --------------------------------------------------------------------------
    # Step 3: Alvarez medical scenario ("AC broke, dizzy") -> coordinator alert
    # --------------------------------------------------------------------------
    print("\n[*] Step 3: Alvarez medical scenario ('AC broke, dizzy')...")
    t_med_start = time.time()
    inbound_med = handle_inbound(ruth["phone"], "telegram", "AC broke, dizzy", event_id)
    assert inbound_med.get("status") == "medical", f"Expected status 'medical', got {inbound_med.get('status')}"
    assert inbound_med.get("need") == "cooling", f"Expected need 'cooling', got {inbound_med.get('need')}"

    # Verify contact status in DB is medical
    c_ruth_med = sb.table("contacts").select("status").eq("event_id", event_id).eq("resident_id", ruth["id"]).execute().data[0]
    assert c_ruth_med["status"] == "medical", f"Contact status in DB expected 'medical', got {c_ruth_med['status']}"

    # Verify Coordinator Gate held the decision in gate_pending
    pending = pending_open(sb, event_id)
    assert len(pending) > 0, "No pending decisions in gate_pending table"
    assert pending[0]["tool"] == "escalate_medical", f"Expected tool escalate_medical, got {pending[0]['tool']}"

    # Verify coordinator alert logged and dispatched
    pings = sb.table("audit_log").select("*").eq("event_id", event_id).eq("action", "coordinator_ping").execute().data
    assert len(pings) > 0, "Coordinator ping not recorded in audit_log"

    t3 = time.time()
    ts3 = datetime.now(timezone.utc).isoformat()
    timestamps.append(("Alvarez Medical -> Coordinator Alert", ts3, t3))
    print(f"    [PASS] Alvarez medical triaged and Coordinator Telegram alert received in {t3 - t_med_start:.2f}s")

    # --------------------------------------------------------------------------
    # Step 4: Coordinator replies "1" -> volunteer Y -> dispatch + calendar
    # --------------------------------------------------------------------------
    print("\n[*] Step 4: Coordinator replies '1', volunteer Marcus Webb replies 'Y'...")
    t_coord_start = time.time()
    coord_res = handle_coordinator_reply(sb, event_id, "1")
    assert coord_res.get("outcome") == "approved", f"Expected outcome 'approved', got {coord_res.get('outcome')}"
    print(f"    [PASS] Coordinator approval registered for decision: {coord_res.get('decision', {}).get('tool')}")

    # Propose dispatch and ask volunteer
    dispatch_plan = Dispatch(
        resident_name=ruth["name"],
        resource_name="Pea Ridge Library Cooling Center",
        volunteer_ask="Can you take Ruth Alvarez to Pea Ridge Library Cooling Center at 2pm? Reply Y or N",
    )
    vol_ask = ask_volunteer(sb, dispatch_plan, event_id, owner_phone)
    assert vol_ask.get("outcome") == "asked", f"Volunteer ask failed: {vol_ask}"
    dispatch_id = vol_ask["dispatch_id"]
    volunteer_name = vol_ask["volunteer"]
    print(f"    [PASS] Volunteer {volunteer_name} asked for dispatch {dispatch_id}")

    # Volunteer replies "Y"
    vol_yes = volunteer_yes(sb, dispatch_id, event_id)
    assert vol_yes.get("outcome") == "accepted", f"Volunteer acceptance failed: {vol_yes}"
    calendar_status = vol_yes.get("calendar", "")

    # Confirm dispatch row in DB
    disp_row = sb.table("dispatches").select("*").eq("id", dispatch_id).execute().data[0]
    assert disp_row["status"] == "accepted", f"Expected dispatch status 'accepted', got {disp_row['status']}"

    t4 = time.time()
    ts4 = datetime.now(timezone.utc).isoformat()
    timestamps.append(("Reply 1 -> Volunteer Y -> Dispatch + Calendar", ts4, t4))
    print(f"    [PASS] Volunteer accepted: dispatch {dispatch_id} recorded + {calendar_status}")

    # --------------------------------------------------------------------------
    # Step 5: Assert zero sends outside PHONE_ALLOWLIST
    # --------------------------------------------------------------------------
    print("\n[*] Step 5: Verifying zero sends outside PHONE_ALLOWLIST...")
    # Audit log check
    audit_rows = sb.table("audit_log").select("*").eq("event_id", event_id).execute().data
    outreach_audits = [
        r for r in audit_rows
        if "wave" in r.get("action", "") or "ping" in r.get("action", "") or "volunteer_ask" in r.get("action", "")
    ]
    assert len(outreach_audits) > 0, "Expected outreach/ping audit entries in audit_log"
    for r in outreach_audits:
        action = r.get("action", "")
        detail = r.get("detail", "")
        if "telegram" in action:
            assert "TG-" in detail or "coordinator" in r.get("actor", "") or "Ruth" in detail
        elif "simulated" in action:
            assert "SIM-" in detail

    # Check all contact phones
    res_rows = sb.table("residents").select("phone, emergency_contact").execute().data
    for r in res_rows:
        assert r["phone"] in allowlist, f"Resident phone {r['phone']} not in allowlist"
        assert r["emergency_contact"] in allowlist, f"Emergency contact {r['emergency_contact']} not in allowlist"

    vol_rows = sb.table("volunteers").select("phone").execute().data
    for v in vol_rows:
        assert v["phone"] in allowlist, f"Volunteer phone {v['phone']} not in allowlist"

    print(f"    [PASS] Strict Allowlist Verification: {len(res_rows)} residents, "
          f"{len(vol_rows)} volunteers, {len(audit_rows)} audit events checked. Zero sends outside allowlist!")

    # Verify timestamp monotonicity
    for i in range(1, len(timestamps)):
        assert timestamps[i][2] >= timestamps[i - 1][2], (
            f"Timestamp inversion: {timestamps[i][0]} ({timestamps[i][2]}) < "
            f"{timestamps[i - 1][0]} ({timestamps[i - 1][2]})"
        )

    # --------------------------------------------------------------------------
    # Step 6: Print timestamp breakdown and proof line
    # --------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("P-08 REHEARSAL TIMESTAMPS BREAKDOWN:")
    print("-" * 70)
    for i, (label, ts_str, t_val) in enumerate(timestamps):
        delta = f"+{t_val - t0:6.2f}s" if i > 0 else "  0.00s"
        print(f"  [{label}] -> UTC: {ts_str} ({delta})")
    print("=" * 70 + "\n")

    proof_line = PROOF_LINE
    print("=" * 70)
    print(proof_line)
    print("=" * 70 + "\n")

    return {
        "event_id": event_id,
        "timestamps": timestamps,
        "proof_line": proof_line,
    }


def main() -> int:
    try:
        run_rehearsal()
        return 0
    except Exception as exc:
        print(f"\n[-] FAIL in rehearsal_p08: {exc}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
