# An Alert Is Not a Trigger Until It's Tiered: NWS Alerts, Deterministic Scoring, and a Model That Only Judges the Edges

During heat waves, public agencies broadcast blanket emergency alerts. But when a community volunteer group or congregation manages a check-on roster of older adults, blanket blasting every neighbor at the exact same minute creates chaos.

Volunteers are overwhelmed by a flood of simultaneous replies, phone networks throttle SMS gateways, and neighbors who need immediate cooling transport get lost behind dozens of healthy people saying *"I'm good"*.

In [Porchlight](https://github.com/zaeem-rmzk/porchlight), an external alert is not a trigger until it is tiered. The system pairs authoritative weather data with deterministic risk scoring, reserving generative AI strictly for the ambiguous edges where human judgment is needed most.

![Porchlight Operator Dispatch Board](https://raw.githubusercontent.com/zaeem-rmzk/porchlight/main/docs/media/console-board.png)

---

## Ingesting the Hazard: api.weather.gov

Porchlight runs an AWS EventBridge poller every 15 minutes that queries the National Weather Service API (`api.weather.gov/alerts/active?zone={DEMO_ZONE}`) with compliant User-Agent headers. When an `Extreme Heat Warning` or `Heat Advisory` is detected, the raw CAP alert is normalized into an immutable `HazardEvent` in Supabase:

```json
{
  "event_id": "nws-2026-heat-benton",
  "hazard_type": "extreme_heat",
  "severity": "warning",
  "headline": "Extreme Heat Warning: Benton County (Heat Index 105°F+)",
  "effective": "2026-09-14T12:00:00Z",
  "expires": "2026-09-15T20:00:00Z"
}
```

---

## Deterministic Scoring: Prioritizing Vulnerability

Instead of messaging all 40 residents simultaneously, Porchlight's tiering engine scores each resident against deterministic vulnerability criteria:

- **Tier 1 (High Priority)**: Age $\ge$ 80, living alone, mobility-impaired, powered medical equipment, or no working AC. Fired in wave 1 (0 to 15 seconds).
- **Tier 2 (Moderate Priority)**: Age 65–79, living with family or partial AC. Fired in wave 2 (after Tier 1 wave completes).
- **Tier 3 (Standard Check)**: Self-sufficient neighbors and backup emergency contacts.

By pacing outreach, high-risk residents are contacted first, ensuring volunteers have capacity to intervene before peak heat hours.

---

## The 0.85s Deterministic Short-Circuit

The vast majority of residents in any wellness check simply reply with *"1"*, *"OK"*, or *"I'm fine"*. Routing unambiguous replies through a frontier large language model burns unnecessary latency and budget.

Porchlight implements a deterministic short-circuit in `agent/triage.py`:

```python
# agent/triage.py: Instant deterministic short-circuit
DETERMINISTIC_OK_PATTERN = r"^(1|ok|okay|fine|bien|all good|im ok)$"

if re.match(DETERMINISTIC_OK_PATTERN, raw_reply.strip().lower()):
    return TriageResult(
        status="ok",
        need="none",
        confidence=1.0,
        quote=raw_reply.strip(),
        rationale="Deterministic regex match: wellness confirmed."
    )
```

When Ruth Alvarez texts back *"1"*, her check-in finishes in **0.85 seconds** with **$0.00 in LLM token fees**. Her badge on the Next.js operator board instantly turns green.

---

## Reserving Claude 3.5 Sonnet for the Complex Edges

LLMs are invoked only when a reply cannot be classified deterministically—for instance, when Mrs. Alvarez texts:
> *"AC broke, dizzy"*

Here, Claude 3.5 Sonnet on AWS Bedrock evaluates the reply against a strict Pydantic schema:

- `status`: `medical`
- `need`: `cooling`
- `quote`: `"AC broke, dizzy"` (100% verbatim extract required for liability audit)
- `confidence`: `0.98`

---

## The Coordinator Human Gate

In emergency operations, autonomous agents must never dispatch physical volunteers or escalate emergency contacts without human confirmation.

Porchlight enforces this boundary using the Strands `BeforeToolCallEvent` hook. When the triage agent attempts to invoke `escalate_medical()`, execution is intercepted:

```python
# agent/dispatch.py: Intercepting autonomous dispatch
@agent.hook("BeforeToolCallEvent")
def intercept_emergency_actions(event: BeforeToolCallEvent):
    if event.tool_name in ["escalate_medical", "dispatch_volunteer"]:
        event.cancel()  # Halt autonomous execution
        persist_gate_pending(event.resident_id, event.tool_args)
        send_coordinator_telegram_alert(event.resident_id, event.tool_args)
```

The coordinator's phone buzzes on Telegram with a single consolidated alert:
> *"Porchlight Alert: Ruth Alvarez (Elm St) reports 'AC broke, dizzy'. Nearest cooling center: Pea Ridge Library (0.8 mi). Reply 1 to dispatch volunteer Marcus Webb, or 2 to call emergency contact."*

The coordinator texts back *"1"*. Marcus receives the dispatch ping, accepts with *"Y"*, and a ride is confirmed in under two minutes—combining the speed of automated tiering with the safety of human oversight.

---

*Inspect the code and try the simulation yourself on GitHub: [https://github.com/zaeem-rmzk/porchlight](https://github.com/zaeem-rmzk/porchlight)*
