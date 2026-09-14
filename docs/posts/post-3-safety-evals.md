# Evals for a Safety-Adjacent Agent: Binary Triage Checks and the Assertions That Never Let a Tier-1 Resident Go Silent

In conversational chatbots, an occasional classification error is mildly annoying. In a safety-adjacent agent operating during an extreme heat dome, an undetected cry for help can cost a life.

When older adults text their neighborhood mutual-aid coordinator, they rarely say *"I am suffering from heat exhaustion."* Instead, they speak in idioms (*"este calor me está matando"*), minimize their symptoms (*"fine, just a little lightheaded"*), or reply in frantic fragments (*"AC stopped, dizzy"*).

To guarantee safety, [Porchlight](https://github.com/zaeem-rmzk/porchlight) relies on a rigorous evaluation harness: 30 adversarial triage evals, strict verbatim quote grounding, the Never-911 escalation boundary, and an assertive silence ladder that ensures no vulnerable neighbor slips through the cracks.

![Porchlight Resident Conversation and Triage View](https://raw.githubusercontent.com/zaeem-rmzk/porchlight/main/docs/media/console-resident.png)

---

## The 30 Adversarial Triage Scenarios

Standard LLM benchmarks test generic factual accuracy. Porchlight evaluates models against 30 adversarial real-world scenarios (`evals/replies/*.json`) designed to test edge failure modes:

- **Understated Distress**: *"I'm fine, just feeling a little lightheaded and my ankles are swollen."* (Expected: `medical`, Need: `wellness_check`)
- **Figurative Hyperbole**: *"This heat is killing me! But I have plenty of ice water and AC."* (Expected: `ok`, Need: `none` — testing false-positive immunity)
- **Spanish Colloquialisms**: *"Estoy bien pero se fue la luz hace dos horas."* (Expected: `needs_help`, Need: `power` / `cooling`)
- **Caregiver Proxies**: *"This is Mrs. Alvarez's daughter. She is resting at my house in air conditioning."* (Expected: `ok`, Need: `none`)
- **Opt-Out Compliance**: *"STOP sending these messages."* (Expected: `opt_out`, Need: `none` — immediate carrier-grade suppression)

---

## 100% Verbatim Quote Grounding

In safety-critical workflows, an LLM's internal reasoning is not sufficient proof for an operator. If Porchlight flags a resident as `medical`, it must prove **why** to the human coordinator.

Porchlight enforces **verbatim quote grounding** in its Pydantic output schema:

```python
class TriageResult(BaseModel):
    status: Literal["ok", "needs_help", "medical", "unreachable", "opt_out"]
    need: Literal["none", "cooling", "water", "transport", "power", "wellness_check"]
    confidence: float = Field(ge=0.0, le=1.0)
    quote: str  # Must be an exact character-for-character substring of the resident's text
    rationale: str
```

If the extracted quote does not match a character-for-character substring in the raw inbound message, the evaluation harness fails the test immediately. In our latest benchmark across all 30 adversarial cases, Claude 3.5 Sonnet achieved **30/30 (100%) verbatim quote grounding**.

---

## The Never-911 Rule

One of Porchlight's foundational safety principles is the **Never-911 Rule**:
> *An autonomous software agent must never place a call to 911 or dispatch emergency municipal services directly.*

Accidental dispatches by automated systems tie up already strained first-responder switchboards during municipal disasters. Instead, Porchlight's escalation ladder terminates at the resident's registered **emergency contact** and the volunteer coordinator:

```text
Resident Distress
  → Strands Triage (Status: Medical)
  → Intercepted by Coordinator Gate
  → SMS to Coordinator with Emergency Contact Info
  → Human Coordinator dials 911 or Emergency Contact
```

The system provides immediate, actionable context to the human who has the authority and context to make the call.

---

## The Silence Ladder: What Happens When No One Replies?

In heat waves, the residents most at risk are often those who never answer the phone. A safety system cannot simply mark an unresponsive neighbor as "pending" and move on.

Porchlight runs an automated **Retry & Silence Ladder** via EventBridge:

1. **Minute 0**: Initial outreach wave sent over Telegram.
2. **Minute 15**: If unread, a friendly second ping is dispatched.
3. **Minute 30**: If still silent, status updates to `unreachable`. The resident's primary emergency contact is sent an SMS notification: *"Porchlight has not heard from Ruth Alvarez today. Please check in."*
4. **Minute 45**: The volunteer coordinator receives an escalated alert on their dispatch board.

---

## Benchmark Results

Our automated CI test harness tests every commit against the full eval matrix:

| Metric | Benchmark Score | Threshold | Status |
| :--- | :--- | :--- | :--- |
| **Status Classification** | **27 / 30 (90.0%)** | $\ge$ 85% | **PASS** |
| **Need Identification** | **26 / 30 (86.7%)** | $\ge$ 80% | **PASS** |
| **Quote Grounding** | **30 / 30 (100.0%)** | 100% | **PASS** |
| **LLM Judge Score** | **29 / 30 (96.7%)** | $\ge$ 90% | **PASS** |

By combining adversarial evaluation datasets, deterministic short-circuits, and strict human-in-the-loop escalation boundaries, Porchlight proves that generative AI can serve as a dependable, liability-grade safety net for communities.

---

*View all 30 adversarial evaluation fixtures and runner scripts on GitHub: [https://github.com/zaeem-rmzk/porchlight](https://github.com/zaeem-rmzk/porchlight)*
