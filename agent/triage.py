"""Triage of inbound replies (P-03).

"1" -> ok and "2" -> needs_help short-circuit without a model call.
Everything else goes to Agent(structured_output_model=Triage) with the
resident's roster context. Returns (Triage, used_model_call: bool).
"""

from __future__ import annotations

import os

from agent.models import Triage


def short_circuit(body: str) -> Triage | None:
    text = body.strip().lower()
    if text == "1":
        return Triage(status="ok", need="none", confidence=1.0,
                      reason="explicit OK short-circuit", quote=body.strip())
    if text == "2":
        return Triage(status="needs_help", need="other", confidence=1.0,
                      reason="explicit help short-circuit, no detail yet", quote=body.strip())
    return None


def triage_reply(body: str, resident: dict) -> tuple[Triage, bool]:
    hit = short_circuit(body)
    if hit is not None:
        return hit, False
    from strands import Agent
    from strands.models import BedrockModel

    agent = Agent(
        model=BedrockModel(model_id=os.environ.get("BEDROCK_MODEL_ID", ""),
                           region_name=os.environ.get("AWS_REGION", "") or None),
        structured_output_model=Triage,
        system_prompt=(
            "You triage wellness check-in replies from vulnerable neighbors. "
            "Classify status as ok, needs_help, medical, or unclear. "
            "Medical means possible danger to health or safety (dizziness, chest pain, "
            "no power for a medical device, fall, confusion). "
            "Set need to cooling, transport, power, wellness_check, other, or none. "
            "Quote the exact words that decided it. Write the reason field in the "
            "resident's own language. Reply with the Triage structure only."
        ),
    )
    ctx = (f"Resident {resident.get('name')}, language {resident.get('language')}, "
           f"notes: {resident.get('notes', '')}. Reply: {body}")
    result = agent(f"Triage this reply: {ctx}")
    return result.structured_output, True
