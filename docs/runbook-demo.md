# Porchlight Demo Video Runbook (P-08)

This runbook specifies the exact take sequence, operator cues, screen recording setup, and contingency procedures for the Porchlight 3-minute video demonstration.

---

## 1. Setup & Pre-Flight Checklist

Before recording:

1. **Environment & Allowlist**:
   - Ensure `.env` is loaded with `ROSTER_MODE=synthetic`.
   - Confirm `PHONE_ALLOWLIST` includes `OWNER_PHONE` and Twilio/Telegram numbers.
   - Confirm `@porchlight_checkon_bot` is running on Telegram.
2. **Console Display**:
   - Open the Next.js Dispatch Board at `http://localhost:3000` (or the deployed AWS App Runner URL).
   - Verify viewport width is >= 1200px for desktop capture.
3. **Telegram Client**:
   - Open Telegram on phone or desktop logged into the account mapped to `TELEGRAM_OWNER_CHAT_ID` (`OWNER_PHONE`).
4. **Clean Baseline**:
   - Run the reset script to archive previous events and restore clean 40-resident state:

     ```bash
     python scripts/reset_demo.py
     ```

   - Confirm console shows 40 residents in `pending` status, 0 dispatches, and an empty active hazard banner.

---

## 2. Video Demo Take Sequence (3-Minute Script)

### Scene 1: Reset & System Overview (0:00 – 0:30)

- **Visual**: Screen recording of Porchlight Console dispatch board and terminal.
- **Action**:
  1. Operator shows terminal running `python scripts/reset_demo.py`.
  2. Proof output is displayed:
     `PROOF P-08: reset_demo ok runtime=READY lambdas=3/3 console=200 telegram=ok = PASS`
  3. Switch to browser: Console dispatch board displays 40 residents sorted by priority tiers (Tier 1: 11, Tier 2: 18, Tier 3: 11) under schema `porchlight` with read-only RLS.
- **Narration**: *"In extreme weather, the people who die are older, alone, and on somebody's list. Porchlight works the list automatically when NWS alerts trigger, checking on vulnerable neighbors and involving the human coordinator only for critical decisions."*

---

### Scene 2: NWS Alert Injection & Wave Outreach (0:30 – 1:00)

- **Visual**: Console simulate panel and Telegram chat side-by-side.
- **Action**:
  1. On the Simulate Panel, click **"Inject Heat Warning"** (or select `heat.json`).
  2. Inbound route `POST /api/simulate/inject` sends the alert to the AgentCore Runtime.
  3. The outreach wave fires across all 40 residents:
     - 39 synthetic residents receive simulated outreach (`SIM-...`).
     - Ruth Alvarez (resident #1, mapped to `OWNER_PHONE`) receives a real Telegram text from `@porchlight_checkon_bot`:
       > *"Porchlight Neighbors: Hi Ruth, extreme heat through tomorrow, hottest afternoon. Reply 1 if you're OK, 2 if you need help, or just tell me. Reply STOP to opt out."*
  4. Console board status stamps transition from `pending` to `sent`.
- **Narration**: *"When NWS issued an Extreme Heat Warning for Benton County, Porchlight's EventBridge poller detected the event. The outreach engine prioritized Tier 1 residents and dispatched personalized bilingual check-ins within seconds."*

---

### Scene 3: Ruth Replies "1" (Wellness Check OK) (1:00 – 1:25)

- **Visual**: Telegram chat on phone/desktop.
- **Action**:
  1. Ruth types and sends: `1`
  2. Inbound handler executes deterministic short-circuit triage (no model latency, 1.0 confidence).
  3. Console dispatch board refreshes: Ruth Alvarez's status badge turns green `ok`.
  4. Audit timeline logs: `triage:ok | Ruth Alvarez need=none quote=1`.
- **Narration**: *"Ruth replies with a quick '1'. Porchlight's deterministic short-circuit handles unambiguous wellness checks instantly without LLM overhead, marking her safe on the dispatch board."*

---

### Scene 4: Distress Scenario — "AC broke, dizzy" (1:25 – 1:55)

- **Visual**: Telegram chat or Simulate Panel.
- **Action**:
  1. Send distress reply: `"AC broke, dizzy"`
  2. Strands triage agent (powered by Bedrock Claude 3.5 Sonnet / deterministic guardrail) classifies:
     - `status`: **`medical`**
     - `need`: **`cooling`**
     - `quote`: `"AC broke, dizzy"`
  3. **Strands Coordinator Gate Intercept**:
     - `BeforeToolCallEvent` hook intercepts `escalate_medical`.
     - Decision is persisted in Supabase `porchlight.gate_pending` with status `open`.
     - Automated action is safely held.
  4. Console board updates: Ruth Alvarez status turns red `medical`.
- **Narration**: *"Moments later, a distress reply arrives: 'AC broke, dizzy'. Strands analyzes the symptoms, extracts the exact quote, and classifies it as a medical emergency needing cooling. But Porchlight never acts autonomously on medical escalations or dials 911—our Strands BeforeToolCall hook intercepts the tool call and alerts the human coordinator."*

---

### Scene 5: Coordinator Receives Alert & Approves (1:55 – 2:25)

- **Visual**: Telegram coordinator alert message.
- **Action**:
  1. Coordinator Telegram receives consolidated alert:
     > *"[Coordinator] Porchlight - Extreme Heat Warning: 1 OK out of 40 checked. Medical-sounding (Ruth Alvarez). 1 send volunteer to Alvarez / 2 I'll handle it Reply 1 / 2"*
  2. Coordinator replies: `1` (or `COORD 1`).
  3. `handle_coordinator_reply` marks the decision in `gate_pending` as `approved`.
  4. Audit timeline logs: `coordinator_approved:escalate_medical`.
- **Narration**: *"The coordinator receives a concise, batched notification summarizing the situation and presenting numbered decision options. By replying '1', the coordinator approves dispatching an available neighborhood volunteer."*

---

### Scene 6: Volunteer Match & Dispatch Acceptance (2:25 – 2:45)

- **Visual**: Console Dispatches section and Audit Timeline.
- **Action**:
  1. Strands Dispatcher matches nearest cooling resource (*Pea Ridge Library Cooling Center*) and selects opted-in volunteer *Marcus Webb*.
  2. Volunteer ask is generated:
     > *"Porchlight: can you take Ruth Alvarez to Pea Ridge Library Cooling Center at 2pm? Reply Y or N"*
  3. Volunteer replies `Y` (via Telegram or console simulation).
  4. Status updates:
     - Dispatch row updates to `accepted`.
     - Google Calendar event logged (`calendar=skipped`).
     - Timeline records `volunteer_accepted`.
- **Narration**: *"Porchlight matches the nearest open cooling center, contacts verified volunteer Marcus Webb, and records the confirmed dispatch with calendar scheduling—closing the loop in under two minutes."*

---

### Scene 7: Console Resident Detail & Freeze Wrap-up (2:45 – 3:00)

- **Visual**: Click into `/event/[id]/resident/[rid]` detail page.
- **Action**:
  1. Click Ruth Alvarez's row on the dispatch board.
  2. Show resident detail view: demographics, age band, mobility, power medical device indicator, triage blockquote (`"AC broke, dizzy"`), and full chronological conversation trail.
  3. Return to main dispatch board showing complete triage breakdown.
- **Narration**: *"Every text, status change, and coordinator approval is immutably logged under Supabase RLS. Porchlight transforms an overwhelming spreadsheet into an intelligent, liability-grade safety net for neighborhood resilience."*

---

## 3. "If X Fails, Do Y" Contingency Table

| Issue / Failure Mode | Root Cause | Immediate Operator Fix (Do Y) |
| --- | --- | --- |
| **Telegram message not delivered to phone** | Network latency or Telegram Bot API temporary delay. | 1. Check bot status via `python -c "from agent.telegram import api; print(api('getMe'))"`.<br>2. Run `scripts/telegram_poll_once.py` or check console simulate panel.<br>3. In Simulate Panel, trigger the action directly via `api/simulate/resident`. |
| **Console board shows stale data** | Browser caching or background polling paused. | 1. Hard refresh browser (`Ctrl+F5` or `Cmd+Shift+R`).<br>2. Verify `refresh.tsx` 5-second interval is active.<br>3. Check developer console for Supabase anon RLS errors. |
| **Console server not running on port 3000** | Node process terminated. | 1. Run `python scripts/start_console.py` or `node console/.next/standalone/server.js`.<br>2. If not built, run `cd console && npm run build`. |
| **Triage model returns timeout / Bedrock rate limit** | Bedrock API throttle or session credential issue. | Fallback keyword triage in `agent/triage.py` automatically detects `"dizzy"`, `"confused"`, `"chest pain"` and assigns `medical` / `cooling` deterministically with zero model delay. |
| **Coordinator reply '1' is ignored** | Format mismatch or missing open gate record. | 1. Verify `gate_pending` has an open record: `sb.table('gate_pending').select('*').eq('status','open')`.<br>2. Send `COORD 1` instead of bare `1`.<br>3. Or use simulate panel: `POST /api/simulate/coordinator` with `{"text": "1"}`. |
| **Simulate panel returns HTTP 429** | 10-second route handler rate limit window. | Wait 10 seconds between button clicks on the simulation panel. |
| **Volunteer reply 'Y' not updating dispatch** | Dispatch ID mismatch or channel error. | Call `porchlight({"action": "inbound.volunteer", "dispatch_id": "<id>", "body": "Y", "event_id": "<id>"})` via Python or Simulate Panel. |
| **Supabase rejects anonymous INSERT** | Intended behavior (read-only RLS active). | All demo simulations must route through `/api/simulate/[op]` with server-side `x-console-key`. Never write directly from client-side anon key. |
| **AWS SSO / STS credential expired** | AWS CLI session expired. | The entire rehearsal, simulation drill, and console dispatch board run fully decoupled from active AWS SSO using local bridge or verified AgentCore / Lambda configurations. |

---

## 4. Rehearsal Execution Sign-off

Automated verification of this entire sequence is executed by:

```bash
python scripts/rehearsal_p08.py
```

Expected output:

```text
PROOF P-08: rehearsal — Ruth text received; "1" → ok; Alvarez medical → coordinator text received; reply 1 → volunteer Y → dispatch + calendar; timestamps printed; zero sends outside the allowlist = PASS
```
