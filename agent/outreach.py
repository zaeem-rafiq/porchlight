"""Outreach wave (P-03): tier-1 then tier-2 via Telegram.

Copy: org name, hazard in plain words, first name, reply 1/2 prompt.
First contact to a number carries 'Reply STOP to opt out'. Plain words,
no jargon, no exclamation marks. Spanish template gets one model review
pass (cached), not machine-literal.

Routing: the owner's real phone sends via Telegram for real. Placeholder
numbers (fictional 555 range) cannot receive messages, so they are recorded
through the same path as sent/simulated — the console's simulated-reply
path answers for them later. Never the reverse: owner replies are never
simulated.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ORG = "Porchlight Neighbors"

TEMPLATES = {
    "en": ("{org}: Hi {name}, extreme heat through tomorrow, hottest afternoon. "
           "Reply 1 if you're OK, 2 if you need help, or just tell me."),
    "es": ("{org}: Hola {name}, calor extremo hasta mañana, lo peor en la tarde. "
           "Responde 1 si estás bien, 2 si necesitas ayuda, o cuéntame."),
}
STOP_LINE = {"en": "Reply STOP to opt out.", "es": "Responde STOP para no recibir más mensajes."}

_reviewed: dict[str, str] = {}


def compose(resident: dict, hazard_plain: dict[str, str], first_contact: bool) -> str:
    lang = resident.get("language", "en") if resident.get("language") in TEMPLATES else "en"
    template = reviewed_template(lang)
    text = template.format(org=ORG, name=resident["name"].split()[0])
    text += " " + hazard_plain.get(lang, hazard_plain["en"])
    if first_contact:
        text += " " + STOP_LINE[lang]
    return text


def reviewed_template(lang: str) -> str:
    if lang in _reviewed:
        return _reviewed[lang]
    if lang == "en":
        _reviewed[lang] = TEMPLATES[lang]
        return _reviewed[lang]
    try:
        from strands import Agent
        from strands.models import BedrockModel

        agent = Agent(
            model=BedrockModel(model_id=os.environ.get("BEDROCK_MODEL_ID", ""),
                               region_name=os.environ.get("AWS_REGION", "") or None),
            system_prompt=("You review SMS copy for elderly Spanish speakers. Keep it short, "
                           "warm, plain words, no jargon, no exclamation marks. Keep the "
                           "{org} and {name} slots exactly. Reply with the revised text only."),
        )
        result = agent(f"Review this heat outreach text: {TEMPLATES[lang]}")
        _reviewed[lang] = str(result).strip() or TEMPLATES[lang]
    except Exception:
        _reviewed[lang] = TEMPLATES[lang]
    return _reviewed[lang]


def is_real_phone(phone: str, owner_phone: str) -> bool:
    return phone == owner_phone


def send_one(sb, to_phone: str, from_number: str, body: str, owner_phone: str) -> tuple[str, str]:
    """Returns (sid, channel). Real Telegram send for the owner; recorded simulated send otherwise."""
    if is_real_phone(to_phone, owner_phone):
        from agent.telegram import owner_chat_id, send_message

        chat = owner_chat_id()
        try:
            mid = send_message(chat, body) if chat else 0
        except Exception as exc:
            sys.stderr.write(f"telegram_send_error in send_one: {exc}\n")
            mid = 0
        return f"TG-{mid}", "telegram"
    return f"SIM-{abs(hash((to_phone, body))) % 10**8:08d}", "simulated"


def send_wave(event_id: str, tier_map: dict[str, int], tiers: tuple[int, ...] = (1, 2, 3)) -> dict:
    from datetime import datetime, timezone

    from dotenv import load_dotenv
    from supabase import create_client

    load_dotenv()
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    owner = os.environ.get("OWNER_PHONE", "").strip()
    from_number = os.environ.get("TELEGRAM_BOT_USERNAME", "telegram")
    sb = create_client(url, key).schema("porchlight")

    residents = sb.table("residents").select("*").eq("opted_out", False).execute().data
    hazard_plain = {"en": "Highs near 105, drink water, stay cool.",
                    "es": "Máximas cerca de 105, toma agua, mantente fresco."}
    now = datetime.now(timezone.utc).isoformat()
    sent, simulated, real = 0, 0, 0
    for tier in sorted(tiers):
        batch = [r for r in residents if tier_map.get(r["id"], 3) == tier]
        for r in batch:
            prior = sb.table("contacts").select("id").eq("resident_id", r["id"]).limit(1).execute().data
            body = compose(r, hazard_plain, first_contact=not prior)
            sid, channel = send_one(sb, r["phone"], from_number, body, owner)
            sb.table("contacts").upsert({
                "event_id": event_id, "resident_id": r["id"], "tier": tier,
                "attempts": 1, "status": "sent",
                "last_outbound": now,
            }, on_conflict="event_id,resident_id").execute()
            sb.table("audit_log").insert({
                "event_id": event_id, "actor": "outreach",
                "action": f"wave tier{tier} {channel}",
                "detail": f"{r['name']} sid={sid}",
            }).execute()
            sent += 1
            simulated += channel == "simulated"
            real += channel == "telegram"
    return {"sent": sent, "simulated": simulated, "real": real}
