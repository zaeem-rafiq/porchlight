"""Route the latest owner Telegram message through the inbound handler (P-03 proofs)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

EVENT_ID = "9a0dff21-aec1-4eba-bc61-e40f6d93df0e"


def main() -> int:
    from agent.inbound import handle_inbound
    from agent.telegram import get_updates, owner_chat_id

    oc = owner_chat_id()
    ups, _ = get_updates(timeout=5)
    mine = [u.get("message", {}) for u in ups
            if str(u.get("message", {}).get("chat", {}).get("id", "")) == oc
            and not u.get("message", {}).get("text", "").startswith("/")]
    if not mine:
        print("poll=EMPTY no owner messages")
        return 2
    text = mine[-1].get("text", "")
    print("inbound_text=" + text)
    out = handle_inbound(os.environ.get("OWNER_PHONE", ""),
                         os.environ.get("TWILIO_NUMBER_B", "").strip(),
                         text, EVENT_ID)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
