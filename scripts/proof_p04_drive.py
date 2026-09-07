"""P-04 live proof driver. Phase A: triage Mabel, dispatch proposal, gate hold, ping.
Phase B (after owner replies): approve, volunteer ask + Y, silence ladder, audit."""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

EVENT_ID = "9a0dff21-aec1-4eba-bc61-e40f6d93df0e"


class _GateEvent:
    def __init__(self, name, tool_input):
        self.tool_name = name
        self.tool_input = tool_input
        self.interrupted = None

    def interrupt(self, token):
        self.interrupted = token


def main() -> int:
    from dotenv import load_dotenv
    from supabase import create_client

    load_dotenv()
    sb = create_client(os.environ["SUPABASE_URL"].rstrip("/"),
                       os.environ["SUPABASE_SERVICE_KEY"]).schema("porchlight")
    from agent import coordinator as coord
    from agent.dispatch import ask_volunteer, propose_dispatch, volunteer_yes
    from agent.inbound import handle_inbound
    from agent.triage import triage_reply

    phase = sys.argv[1] if len(sys.argv) > 1 else "--phase-a"
    if phase == "--phase-a":
        mabel = sb.table("residents").select("*").eq("name", "Mabel Thornton").execute().data[0]
        out = handle_inbound(mabel["phone"], os.environ["TWILIO_NUMBER_B"].strip(),
                             "The power keeps flickering and mom is confused.", EVENT_ID)
        print(f"mabel triage: {out.get('status')}/{out.get('need')}")
        triage, _ = triage_reply("The power keeps flickering and mom is confused.", mabel)
        dispatch = propose_dispatch(mabel, triage, EVENT_ID)
        print(f"dispatch proposal: {dispatch.resource_name[:60]}")
        gate = coord.CoordinatorGate(sb, EVENT_ID)
        ev = _GateEvent("escalate_medical", {"resident_name": "Mabel Thornton"})
        gate.on_before_tool_call(ev)
        print(f"gate interrupt={ev.interrupted} pending={len(coord.pending)}")
        ping = coord.maybe_ping(sb, EVENT_ID, "Elm St heat warning", time.time() / 60)
        print(f"ping: {ping}")
        return 0

    # Phase B
    from agent.telegram import get_updates, owner_chat_id

    from agent.inbound import handle_inbound as route

    oc = owner_chat_id()
    ups, _ = get_updates(timeout=5)
    mine = [u.get("message", {}) for u in ups
            if str(u.get("message", {}).get("chat", {}).get("id", "")) == oc
            and not u.get("message", {}).get("text", "").startswith("/")]
    text = mine[-1].get("text", "") if mine else ""
    print("coordinator reply text=" + text)
    out = route(os.environ["OWNER_PHONE"], os.environ["TWILIO_NUMBER_B"].strip(), text, EVENT_ID)
    print(out)
    if out.get("outcome") == "approved":
        mabel = sb.table("residents").select("*").eq("name", "Mabel Thornton").execute().data[0]
        triage, _ = triage_reply("The power keeps flickering and mom is confused.", mabel)
        from agent.models import Dispatch as D

        vol = ask_volunteer(sb, D(resident_name="Mabel Thornton",
                                  resource_name="Pea Ridge Library Cooling Center"),
                            EVENT_ID, os.environ["OWNER_PHONE"])
        print(vol)
        print(volunteer_yes(sb, vol["dispatch_id"], EVENT_ID))
    contact = sb.table("contacts").select("*").eq("event_id", EVENT_ID).eq(
        "status", "medical").limit(1).execute().data[0]
    sil = coord.silence_check(sb, EVENT_ID, contact, age_min=2.0, limit_min=1.0)
    print(f"silence ladder: {sil}")
    rows = sb.table("audit_log").select("action").eq("event_id", EVENT_ID).execute().data
    acts = sorted({r["action"] for r in rows})
    print(f"audit actions={len(rows)} distinct={acts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
