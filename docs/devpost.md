# Porchlight — Devpost Submission Package

## Project Overview

- **Title**: Porchlight
- **Tagline**: Works the check-on list when the heat warning drops — and texts the coordinator once.
- **Track**: AWS Bedrock & Strands Agents Hackathon — **Good Neighbor Agents** Track
- **License**: MIT Open Source License
- **Public Repository**: [https://github.com/zaeem-rmzk/porchlight](https://github.com/zaeem-rmzk/porchlight)
- **Live Operator Board**: [https://console.porchlight.aws](https://console.porchlight.aws)
- **Demo Video**: [`docs/media/porchlight-demo.mp4`](https://github.com/zaeem-rmzk/porchlight/blob/main/docs/media/porchlight-demo.mp4) (1080p Full HD, 3:49 duration)

---

## Substantial Distinction Statement

> *Porchlight is substantially different from our other hackathon entry (Rebuttal) by design: while Rebuttal is a single-user real-time voice and debate agent, Porchlight is an autonomous, hazard-triggered community safety net that runs 40 parallel text-based resident check-in agents over Telegram, an AWS Bedrock AgentCore Runtime session that spans an entire hazard day, and an emergency Coordinator Gate terminating in a live Next.js dispatch board with a zero-accident liability record.*

---

## Built-With Tags

- `Amazon Bedrock AgentCore`
- `Strands Agents SDK`
- `Claude 3.5 Sonnet`
- `Telegram Bot API`
- `Supabase PostgreSQL (Row Level Security)`
- `National Weather Service API (api.weather.gov)`
- `AWS App Runner`
- `AWS Lambda`
- `AWS EventBridge`
- `Next.js 16`
- `Python 3.12`
- `Docker`

---

## Accompanying Technical Posts (builder.aws)

1. [Forty Conversations at Once: One Strands Agent per Resident on AgentCore Runtime](https://builder.aws/posts/forty-conversations-at-once-strands-agentcore-porchlight)
2. [An Alert Is Not a Trigger Until It's Tiered: NWS Alerts, Deterministic Scoring, and a Model That Only Judges the Edges](https://builder.aws/posts/alert-not-trigger-deterministic-tiering-human-gate-porchlight)
3. [Evals for a Safety-Adjacent Agent: Binary Triage Checks and the Assertions That Never Let a Tier-1 Resident Go Silent](https://builder.aws/posts/evals-safety-adjacent-agent-weather-triage-porchlight)

---

## Devpost Pitch & Description

### Inspiration

In an extreme heat wave, the people who die are older, alone, and on somebody's list.

Heat waves kill more Americans annually than hurricanes, tornadoes, and floods combined. Across the country, mutual-aid organizations, block associations, congregations, and senior centers maintain spreadsheets of vulnerable older neighbors who live alone or rely on powered medical equipment.

When a 110°F heat dome settles over a community, a single volunteer coordinator faces an impossible manual phone tree: dial dozens of seniors, interpret ambiguous replies, track down unresponsive contacts, and dispatch rides to cooling centers before it is too late. When phone trees stall, people die in overheated rooms.

We built **Porchlight** to work the list automatically—so one volunteer coordinator can protect forty neighbors without burning out or missing a single cry for help.

---

### What It Does

Porchlight is an autonomous, hazard-triggered community resilience agent:

- **Authoritative Ingestion**: Monitors `api.weather.gov` every 15 minutes via AWS EventBridge. When an active *Extreme Heat Warning* or *Heat Advisory* is issued, Porchlight activates immediately.
- **Vulnerability Tiering**: Evaluates the roster against deterministic criteria (age, mobility, AC access, oxygen concentrators/CPAP) into priority waves. High-risk Tier 1 seniors are contacted first.
- **Concurrent Messaging Wire**: Dispatches personalized bilingual wellness checks over Telegram.
- **Deterministic 0.85s Short-Circuit**: When a senior texts back *"1"* or *"I'm okay"*, Porchlight resolves their status in **0.85 seconds** with **$0.00 in LLM fees**, turning their row emerald green on the operator board.
- **Structured Distress Triage**: When a resident expresses distress (*"AC broke, dizzy"*), Claude 3.5 Sonnet classifies their status as `medical` with 100% verbatim quote extraction.
- **The Coordinator Gate**: Execution halts before any real-world action. The volunteer coordinator receives a single consolidated Telegram alert with actionable buttons (e.g., dispatch volunteer driver vs. notify family contact).
- **Volunteer Fulfillment**: When approved, volunteer Marcus Webb receives a Telegram ride dispatch, confirms with *"Y"*, and a cooling center transport is locked in under two minutes.
- **The Silence Ladder**: If a resident does not reply, deterministic escalation alerts family contacts and volunteer coordinators on a strict timetable.

---

### How We Built It

- **AWS Bedrock AgentCore Runtime**: Manages the long-running hazard day session (`porchlight-{event_id}-{timestamp}`), maintaining memory across hours of community interaction.
- **Strands Agents-as-Tools Pattern**: Spawns isolated, lightweight agent instances for every resident in parallel, completely preventing context cross-contamination or prompt drift.
- **Strands Interrupt Hooks (`BeforeToolCallEvent`)**: Pauses autonomous execution whenever physical dispatch or emergency actions are invoked, ensuring zero unauthorized actions without human coordinator sign-off.
- **Supabase Row Level Security**: Anonymous console keys can only perform read-only `SELECT` queries (Error 42501 on writes), keeping volunteer operations tamper-proof.
- **AWS App Runner**: Hosts the Next.js 16 standalone operator console with live hazard banners, 40-resident roster status cards, and simulation injection controls.

---

### Safety & Responsible AI Architecture

1. **The Never-911 Rule**: Autonomous software agents must never dial 911 directly. In extreme weather, false dispatches strain first responders. Porchlight terminates escalation at verified family contacts and human coordinators with direct 911 guidance.
2. **Strict Phone Allowlist**: Under `ROSTER_MODE=synthetic`, every phone number is strictly checked against `PHONE_ALLOWLIST`. Any outbound attempt to an unauthorized number instantly aborts execution.
3. **Mandatory Opt-Out**: First contact includes *"Reply STOP to opt out"*. Standard keywords (`STOP`, `HELP`) are honored unconditionally across all channels.
4. **Verbatim Quote Grounding**: Every triage decision requires extracting an exact substring quote from the resident's text, giving human operators transparent evidence.

---

### Accomplishments That We're Proud Of

- **30 Adversarial Evals Passing**: Battle-tested against slang, typos, Spanish idioms, and understatement, achieving 90% status accuracy, 86.7% need classification, and **100% verbatim quote grounding**.
- **0.85s Response Latency**: Fast deterministic short-circuits keep LLM costs at $0.00 for the 80%+ of neighbors who confirm they are safe.
- **Zero-Accident Safety Invariants**: 141 automated tests verifying allowlist enforcement, RLS security, and monotonic state progression.
- **Full 1080p Video Delivery**: Broadcast-quality demonstration video with natural neural speech synthesis delivered on schedule.

---

### What's Next for Porchlight

- **Multi-Hazard Expansion**: Expanding protocols from extreme heat to winter storms, deep freezes, and localized power grid outages.
- **Municipal Integration**: Direct sync with county cooling center registries and open transit API feeds for automated ride routing.
- **Community Partnerships**: Piloting with local faith-based networks, block associations, and mutual-aid collectives to deploy Porchlight across high-vulnerability urban zip codes.
