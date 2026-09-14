# Forty Conversations at Once: One Strands Agent per Resident on AgentCore Runtime

When an extreme weather emergency strikes—whether an 115°F heat dome or a sub-zero winter storm—community check-on rosters face an immediate concurrency bottleneck. A typical neighborhood mutual aid group, congregation, or senior living community maintains a roster of 40 to 100 vulnerable residents. But there is usually only one volunteer coordinator.

Calling or texting forty seniors individually, interpreting ambiguous answers, and dispatching assistance takes hours a coordinator does not have. In extreme heat, that delay can be fatal.

To solve this, [Porchlight](https://github.com/zaeem-rmzk/porchlight) architecture decouples the event coordinator from one-on-one message handling. Instead of running a single monolithic chat loop, Porchlight orchestrates a multi-agent hierarchy: a long-running event session on **AWS Bedrock AgentCore Runtime** that spawns dedicated, isolated **Strands agents** for every single resident in parallel.

![Porchlight Serverless Architecture](https://raw.githubusercontent.com/zaeem-rmzk/porchlight/main/docs/media/architecture.png)

---

## The Agents-as-Tools Pattern

In traditional conversational systems, an orchestrator passes all messages into a shared context window. With forty residents texting simultaneously, shared context degrades rapidly: token costs skyrocket, latency spikes, and hallucinations cross-contaminate resident medical histories.

Porchlight implements the **Strands `agents-as-tools` pattern**. The top-level orchestrator does not converse with residents directly. Instead, each resident profile in Supabase is encapsulated inside their own isolated `ResidentAgent`:

```python
# agent/app.py: Spawning isolated Strands resident agents
from strands_agents import Agent, Tool
from agent.triage import evaluate_resident_reply

def create_resident_agent(resident: dict) -> Agent:
    return Agent(
        name=f"resident-{resident['id']}",
        system_prompt=build_resident_prompt(resident),
        tools=[
            Tool.from_function(record_triage_result),
            Tool.from_function(request_coordinator_gate),
        ],
        model="anthropic.claude-3-5-sonnet-20241022-v2:0",
    )
```

Each resident agent has strict operational boundaries:

- **Isolated Context**: The agent only sees the conversation history and medical risk factors (e.g., mobility limitations, powered medical equipment, lack of air conditioning) for that specific individual.
- **Deterministic Boundaries**: It cannot unilaterally take irreversible real-world actions. All emergency actions terminate in a coordinator review gate.
- **Multi-Language Persona**: Spanish-speaking residents are paired with bilingual prompts that preserve conversational empathy while strictly enforcing English-structured JSON outputs.

---

## Orchestrating Event Sessions on Bedrock AgentCore Runtime

While each resident interacts with an isolated agent, extreme weather emergencies are community-wide events that span hours or days. Porchlight coordinates these conversations using a long-running **AWS Bedrock AgentCore Runtime** session:

- **Session Lifecycle**: When the National Weather Service (NWS) poller detects an active `Extreme Heat Warning`, an EventBridge rule spins up a runtime session keyed by hazard ID: `runtimeSessionId = f"porchlight-{event_id}-{timestamp}"`.
- **Parallel Fan-Out**: The runtime session initiates parallel async tasks for all 40 residents. Priority Tier 1 residents (older adults living alone without cooling) receive outreach within the first 15 seconds, followed by Tier 2 and Tier 3.
- **Inbound Telegram Routing**: Inbound webhook payloads from Telegram arrive at an AWS Lambda function URL and route directly to the active AgentCore Runtime session via `app.entrypoint("inbound.resident")`.

Because each resident has their own isolated session state backed by AgentCore Memory, forty simultaneous inbound messages never block or race one another.

---

## Observability Across Concurrent Spans

Running forty concurrent agent conversations requires liability-grade observability. Porchlight instruments every phase of execution with OpenTelemetry spans exported to CloudWatch:

- `nws.alert_polled` (detects hazard severity and geographic zone)
- `runtime.session_start` (initializes event container on Bedrock AgentCore)
- `resident.outreach_fanout` (dispatches 40 concurrent Telegram messages)
- `resident.reply_received` (captures inbound webhook timestamp)
- `resident.triage_eval` (measures LLM vs. deterministic classification latency)
- `coordinator.gate_held` (records human-in-the-loop intercept duration)

When Ruth Alvarez replies *"1"* to confirm she is safe, her check-in short-circuits deterministically in **0.85 seconds** without invoking an LLM. When Mrs. Alvarez replies *"AC broke, dizzy"*, her dedicated Strands agent flags acute distress, classifies her status as `medical`, and halts execution at the coordinator gate in **1.42 seconds**.

By separating community-level orchestration on AWS Bedrock AgentCore Runtime from individual resident reasoning via Strands agents-as-tools, Porchlight ensures that no vulnerable neighbor is delayed in an emergency.

---

*Explore the full open-source codebase and architecture on GitHub: [https://github.com/zaeem-rmzk/porchlight](https://github.com/zaeem-rmzk/porchlight)*
