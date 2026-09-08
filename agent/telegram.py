"""Telegram edge adapter (P-03, ADR-004): same copy, same handler, different wire.

The owner's Telegram chat binds 1:1 to the OWNER_PHONE identity; every
message from that chat enters handle_inbound as the owner. Owner outbound
goes over Telegram; placeholders stay simulated; Twilio SMS path untouched.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API = "https://api.telegram.org/bot{token}/{method}"


def _env() -> dict[str, str]:
    from dotenv import load_dotenv

    load_dotenv()
    return dict(os.environ)


def api(method: str, payload: dict | None = None) -> dict:
    env = _env()
    data = urllib.parse.urlencode(payload or {}).encode()
    req = urllib.request.Request(
        API.format(token=env.get("TELEGRAM_BOT_TOKEN", ""), method=method), data=data)
    with urllib.request.urlopen(req, timeout=40) as resp:
        return json.load(resp)


def send_message(chat_id: str, text: str) -> int:
    return int(api("sendMessage", {"chat_id": chat_id, "text": text}).get("result", {}).get("message_id", 0))


def get_updates(offset: int = 0, timeout: int = 30) -> tuple[list[dict], int]:
    res = api("getUpdates", {"offset": offset, "timeout": timeout})
    updates = res.get("result", [])
    nxt = max([u["update_id"] for u in updates], default=offset - 1) + 1
    return updates, nxt


def owner_chat_id() -> str:
    chat = (os.environ.get("TELEGRAM_OWNER_CHAT_ID", "") or "").strip()
    if chat:
        return chat
    return (_env().get("TELEGRAM_OWNER_CHAT_ID", "") or "").strip()


def bind_owner(chat_id: str) -> None:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, ".env")
    with open(path, encoding="utf-8") as fh:
        content = fh.read()
    if "TELEGRAM_OWNER_CHAT_ID" in content:
        import re

        content = re.sub(r"^TELEGRAM_OWNER_CHAT_ID=.*$", f"TELEGRAM_OWNER_CHAT_ID={chat_id}",
                         content, flags=re.MULTILINE)
    else:
        content += f"\nTELEGRAM_OWNER_CHAT_ID={chat_id}\n"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    print(f"owner_chat_bound=True chat=...{chat_id[-4:]}")
