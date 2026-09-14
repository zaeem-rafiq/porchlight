"""
Full slide rendering script for all 17 shots across 9 scenes.
Produces 1920x1080 broadcast-quality slides with high typography and layout fidelity.
"""

import os
from PIL import Image, ImageDraw, ImageFont
from generate_slides_core import (
    W, H, create_base_canvas, draw_subtitles, draw_card, draw_phone_mockup, save_frame, get_fonts
)

def render_shot_1a():
    im, draw, fonts = create_base_canvas(1, "The Community Check-On Burden")
    
    # Hero Alert Banner
    draw.rounded_rectangle([(60, 105), (W - 60, 195)], radius=14, fill=(80, 20, 20), outline=(239, 68, 68), width=2)
    draw.ellipse([(90, 130), (130, 170)], fill=(239, 68, 68))
    draw.text((105, 133), "!", fill=(255, 255, 255), font=fonts["h1"])
    draw.text((150, 122), "NWS HAZARD TRIGGER: EXTREME HEAT WARNING (HEAT INDEX 105°F+)", fill=(254, 202, 202), font=fonts["h2"])
    draw.text((150, 158), "National Weather Service Warning Active for Benton County  ·  Immediate Community Risk", fill=(252, 165, 165), font=fonts["small"])

    # Left Card: The Vulnerable Population
    draw_card(draw, [(60, 225), (930, 935)], fill=(18, 26, 40), outline=(51, 65, 85))
    draw.text((95, 255), "WHO DIES IN A HEAT WAVE?", fill=(245, 158, 11), font=fonts["h2"])
    draw.text((95, 295), "Older, alone, and on somebody's check-on list.", fill=(203, 213, 225), font=fonts["body_bold"])
    
    # Stat boxes
    draw.rounded_rectangle([(95, 345), (470, 485)], radius=12, fill=(30, 41, 59), outline=(71, 85, 105))
    draw.text((120, 360), "40", fill=(245, 158, 11), font=fonts["big_stat"])
    draw.text((120, 440), "Vulnerable Neighbors", fill=(148, 163, 184), font=fonts["small_bold"])
    
    draw.rounded_rectangle([(500, 345), (895, 485)], radius=12, fill=(30, 41, 59), outline=(71, 85, 105))
    draw.text((525, 360), "72%", fill=(239, 68, 68), font=fonts["big_stat"])
    draw.text((525, 440), "Live Alone / Mobility Limited", fill=(148, 163, 184), font=fonts["small_bold"])

    bullets = [
        ("Community Rosters:", "Kept in static spreadsheets across senior centers & mutual aid"),
        ("Social Isolation:", "Neighbors without family nearby during heat spikes"),
        ("Power Medical Needs:", "Oxygen concentrators and dialysis machines vulnerable to outages"),
        ("Fatal Window:", "Internal body temperature can rise critically within 4 hours")
    ]
    cur_y = 525
    for b_title, b_desc in bullets:
        draw.ellipse([(95, cur_y + 6), (107, cur_y + 18)], fill=(245, 158, 11))
        draw.text((120, cur_y), b_title, fill=(248, 250, 252), font=fonts["body_bold"])
        draw.text((120, cur_y + 26), b_desc, fill=(148, 163, 184), font=fonts["small"])
        cur_y += 75

    # Right Card: The Volunteer Coordinator
    draw_card(draw, [(980, 225), (1860, 935)], fill=(18, 26, 40), outline=(51, 65, 85))
    draw.text((1015, 255), "THE VOLUNTEER COORDINATOR'S BURDEN", fill=(99, 102, 241), font=fonts["h2"])
    draw.text((1015, 295), "One dedicated volunteer tasked with saving 40 lives.", fill=(203, 213, 225), font=fonts["body_bold"])

    draw.rounded_rectangle([(1015, 345), (1390, 485)], radius=12, fill=(30, 41, 59), outline=(71, 85, 105))
    draw.text((1040, 360), "1", fill=(99, 102, 241), font=fonts["big_stat"])
    draw.text((1040, 440), "Sole Volunteer Coordinator", fill=(148, 163, 184), font=fonts["small_bold"])

    draw.rounded_rectangle([(1420, 345), (1825, 485)], radius=12, fill=(30, 41, 59), outline=(71, 85, 105))
    draw.text((1445, 360), "4+ hrs", fill=(239, 68, 68), font=fonts["big_stat"])
    draw.text((1445, 440), "To Call 40 People Manually", fill=(148, 163, 184), font=fonts["small_bold"])

    c_bullets = [
        ("Manual Phone Tag:", "Voicemails, busy signals, and unreturned texts drain hours"),
        ("Ambiguous Replies:", "'I feel a bit strange' or 'AC stopped' require deep triage"),
        ("Transport Logistics:", "Matching volunteer drivers with cooling center capacity by hand"),
        ("Coordinator Burnout:", "Impossible cognitive load during acute regional heat events")
    ]
    cur_y = 525
    for b_title, b_desc in c_bullets:
        draw.ellipse([(1015, cur_y + 6), (1027, cur_y + 18)], fill=(99, 102, 241))
        draw.text((1040, cur_y), b_title, fill=(248, 250, 252), font=fonts["body_bold"])
        draw.text((1040, cur_y + 26), b_desc, fill=(148, 163, 184), font=fonts["small"])
        cur_y += 75

    draw_subtitles(draw, fonts, "In an extreme heat wave, the people who die are older, alone, and on somebody's list. Mutual-aid groups, congregations, block associations, and senior centers maintain rosters of vulnerable neighbors.")
    save_frame(im, "shot_1a")

def render_shot_1b():
    im, draw, fonts = create_base_canvas(1, "The Community Check-On Burden")
    
    # Header quote banner
    draw.rounded_rectangle([(60, 105), (W - 60, 200)], radius=14, fill=(30, 41, 59), outline=(99, 102, 241), width=2)
    draw.text((95, 122), "\"A single volunteer coordinator cannot manually call dozens of residents, interpret ambiguous replies,", fill=(248, 250, 252), font=fonts["h2"])
    draw.text((95, 158), "and coordinate emergency transport before it is too late. Porchlight works the list automatically.\"", fill=(245, 158, 11), font=fonts["h2"])

    # Left Card: Traditional Manual Process
    draw_card(draw, [(60, 230), (930, 935)], fill=(28, 18, 24), outline=(153, 27, 27))
    draw.rounded_rectangle([(95, 255), (320, 290)], radius=6, fill=(127, 29, 29))
    draw.text((110, 262), "THE OLD WAY: MANUAL", fill=(254, 202, 202), font=fonts["small_bold"])
    draw.text((95, 310), "Spreadsheet Panic & Delayed Help", fill=(248, 250, 252), font=fonts["h2"])

    old_points = [
        ("4 to 6 Hours Delay", "Linear 1-by-1 phone calls while ambient heat climbs"),
        ("Missed Escalations", "Subtle signs like 'dizzy' buried under 50 voicemails"),
        ("Human Liability Risk", "Unrecorded verbal calls; no audit trail or verification"),
        ("Ad-hoc Transport", "Frantic group texts to find available drivers")
    ]
    cur_y = 390
    for title, desc in old_points:
        draw.rounded_rectangle([(95, cur_y), (895, cur_y + 90)], radius=10, fill=(38, 24, 30), outline=(80, 30, 40))
        draw.text((120, cur_y + 16), "✕  " + title, fill=(239, 68, 68), font=fonts["body_bold"])
        draw.text((150, cur_y + 48), desc, fill=(203, 213, 225), font=fonts["small"])
        cur_y += 110

    # Right Card: Porchlight Autonomous Flow
    draw_card(draw, [(980, 230), (1860, 935)], fill=(16, 28, 38), outline=(5, 150, 105))
    draw.rounded_rectangle([(1015, 255), (1310, 290)], radius=6, fill=(6, 95, 70))
    draw.text((1030, 262), "PORCHLIGHT: AUTONOMOUS", fill=(167, 243, 208), font=fonts["small_bold"])
    draw.text((1015, 310), "Resilience At The Speed Of Code", fill=(248, 250, 252), font=fonts["h2"])

    new_points = [
        ("11 Seconds Full Wave", "Parallel Strands resident agents text all 40 neighbors at once"),
        ("Deterministic Short-Circuit", "Simple '1' wellness replies triaged instantly in 0.85s"),
        ("Strands Coordinator Gate", "Medical escalations safely held for 1-tap coordinator approval"),
        ("Automated Volunteer Match", "Dispatches verified drivers to nearest open cooling center")
    ]
    cur_y = 390
    for title, desc in new_points:
        draw.rounded_rectangle([(1015, cur_y), (1825, cur_y + 90)], radius=10, fill=(18, 38, 38), outline=(16, 110, 80))
        draw.text((1040, cur_y + 16), "✓  " + title, fill=(52, 211, 153), font=fonts["body_bold"])
        draw.text((1070, cur_y + 48), desc, fill=(203, 213, 225), font=fonts["small"])
        cur_y += 110

    draw_subtitles(draw, fonts, "But when an extreme heat dome settles over a city, a single volunteer coordinator cannot manually call dozens of residents, interpret ambiguous replies, and coordinate emergency transport before it is too late. Porchlight works the list automatically.")
    save_frame(im, "shot_1b")

def render_shot_2a():
    im, draw, fonts = create_base_canvas(2, "Serverless & Multi-Agent Architecture")
    
    # Left: High-resolution architecture diagram
    arch_path = "docs/media/architecture.png"
    if os.path.exists(arch_path):
        arch_img = Image.open(arch_path)
        # fit inside (1160, 820)
        arch_img.thumbnail((1160, 820), Image.Resampling.LANCZOS)
        ax = 60 + (1160 - arch_img.width) // 2
        ay = 105 + (820 - arch_img.height) // 2
        draw_card(draw, [(55, 100), (1225, 935)], fill=(18, 24, 38), outline=(51, 65, 85))
        im.paste(arch_img, (ax, ay))

    # Right: Subsystem Highlights
    draw_card(draw, [(1255, 100), (1860, 935)], fill=(18, 24, 38), outline=(51, 65, 85))
    draw.text((1285, 130), "ARCHITECTURE AT A GLANCE", fill=(245, 158, 11), font=fonts["h2"])
    draw.text((1285, 170), "End-to-End Serverless Resiliency", fill=(148, 163, 184), font=fonts["small_bold"])

    subsystems = [
        ("1. External Weather Ingress", "api.weather.gov polled every 15 mins via AWS EventBridge scheduler.", (245, 158, 11)),
        ("2. Serverless Lambda Edge", "3 lightweight Lambdas with Function URLs for instant webhook routing.", (239, 68, 68)),
        ("3. Bedrock AgentCore Platform", "Long-running microVM runtime session + episodic Memory for resident history.", (99, 102, 241)),
        ("4. Strands Multi-Agent", "Agents-as-Tools: one isolated ResidentAgent per resident executing in parallel.", (52, 211, 153)),
        ("5. Coordinator Human Gate", "Strands BeforeToolCallEvent hook intercepts medical tool execution safely.", (245, 158, 11)),
        ("6. Supabase PostgreSQL + RLS", "Liability-grade audit logging with strict anonymous read-only RLS.", (6, 182, 212)),
        ("7. Next.js 16 Dispatch Board", "Standalone container running on AWS App Runner with live updates.", (168, 85, 247))
    ]
    cur_y = 220
    for title, desc, col in subsystems:
        draw.rounded_rectangle([(1285, cur_y), (1830, cur_y + 85)], radius=10, fill=(30, 41, 59), outline=(51, 65, 85))
        draw.ellipse([(1305, cur_y + 18), (1321, cur_y + 34)], fill=col)
        draw.text((1335, cur_y + 14), title, fill=(248, 250, 252), font=fonts["body_bold"])
        draw.text((1335, cur_y + 44), desc, fill=(148, 163, 184), font=fonts["tiny"])
        cur_y += 98

    draw_subtitles(draw, fonts, "Here is how Porchlight works under the hood. National Weather Service alerts trigger an AWS EventBridge poller every fifteen minutes. When a heat warning activates, EventBridge invokes an AWS Bedrock AgentCore Runtime session.")
    save_frame(im, "shot_2a")

def render_shot_2b():
    im, draw, fonts = create_base_canvas(2, "Serverless & Multi-Agent Architecture")
    
    # Left Card: Strands Framework & Runtime Integration
    draw_card(draw, [(60, 100), (960, 935)], fill=(18, 24, 38), outline=(51, 65, 85))
    draw.text((95, 130), "STRANDS MULTI-AGENT INTELLIGENCE", fill=(99, 102, 241), font=fonts["h2"])
    draw.text((95, 170), "Parallel Agent Execution & Deterministic Control", fill=(148, 163, 184), font=fonts["small"])

    strands_cards = [
        ("Agents-as-Tools (asyncio)", "One ResidentAgent spawned per roster member, executing concurrently in parallel threads.", (99, 102, 241)),
        ("Pydantic Structured Output", "Strict Triage schema (status, need, quote, reason) guarantees zero hallucinated fields.", (52, 211, 153)),
        ("BeforeToolCallEvent Hook", "Intercepts escalate_medical tool calls and suspends execution for coordinator sign-off.", (245, 158, 11)),
        ("Episodic Memory Retention", "AgentCore Memory tracks past cooling preferences across multiple consecutive hazard days.", (168, 85, 247))
    ]
    cur_y = 220
    for title, desc, col in strands_cards:
        draw.rounded_rectangle([(95, cur_y), (925, cur_y + 110)], radius=12, fill=(30, 41, 59), outline=(51, 65, 85))
        draw.rounded_rectangle([(115, cur_y + 16), (135, cur_y + 36)], radius=4, fill=col)
        draw.text((150, cur_y + 14), title, fill=(248, 250, 252), font=fonts["body_bold"])
        draw.text((150, cur_y + 50), desc, fill=(203, 213, 225), font=fonts["small"])
        cur_y += 130

    # Right Card: AgentCore Runtime Trace & Supabase Storage
    draw_card(draw, [(990, 100), (1860, 935)], fill=(18, 24, 38), outline=(51, 65, 85))
    draw.text((1025, 130), "AWS BEDROCK AGENTCORE RUNTIME TRACE", fill=(245, 158, 11), font=fonts["h2"])
    draw.text((1025, 170), "15 Distributed Observability Spans per Hazard Ingestion", fill=(148, 163, 184), font=fonts["small"])

    trace_path = "docs/media/trace-heat.png"
    if os.path.exists(trace_path):
        trace_img = Image.open(trace_path)
        trace_img.thumbnail((800, 380), Image.Resampling.LANCZOS)
        tx = 1025 + (800 - trace_img.width) // 2
        ty = 220
        draw_card(draw, [(1015, 210), (1835, 590)], fill=(11, 16, 26), outline=(71, 85, 105))
        im.paste(trace_img, (tx, ty))

    # Bottom Storage & RLS Callout
    draw.rounded_rectangle([(1025, 620), (1825, 905)], radius=14, fill=(16, 28, 38), outline=(6, 182, 212), width=2)
    draw.text((1055, 645), "SUPABASE POSTGRESQL + ROW LEVEL SECURITY", fill=(6, 182, 212), font=fonts["h2"])
    draw.text((1055, 685), "• Schema 'porchlight' isolates 6 relational tables under strict Postgres RLS.", fill=(248, 250, 252), font=fonts["body"])
    draw.text((1055, 725), "• Anonymous API keys can only perform read-only SELECT queries (Error 42501 on write).", fill=(248, 250, 252), font=fonts["body"])
    draw.text((1055, 765), "• All state mutations restricted to backend AgentCore Runtime service role.", fill=(248, 250, 252), font=fonts["body"])
    draw.text((1055, 805), "• Every inbound text, model triage decision, and gate approval has immutable audit log.", fill=(248, 250, 252), font=fonts["body"])

    draw_subtitles(draw, fonts, "Using the Strands Agents framework, Porchlight spawns one dedicated resident agent per neighbor in parallel. Messages flow across Telegram, while critical medical decisions are intercepted by our human-in-the-loop Coordinator Gate. All state is immutably logged to Supabase under Row Level Security for the Next.js operator console.")
    save_frame(im, "shot_2b")

def render_shot_3a():
    im, draw, fonts = create_base_canvas(3, "Live Demo · NWS Heat Alert & Wave Outreach")
    
    # Left: Next.js Console Dispatch Board screenshot (top crop)
    cb_path = "docs/media/console-board.png"
    if os.path.exists(cb_path):
        cb_img = Image.open(cb_path)
        # crop top 1400 px
        crop_cb = cb_img.crop((0, 0, cb_img.width, 1400))
        crop_cb.thumbnail((1050, 800), Image.Resampling.LANCZOS)
        cx = 60 + (1050 - crop_cb.width) // 2
        cy = 110 + (800 - crop_cb.height) // 2
        draw_card(draw, [(55, 100), (1115, 935)], fill=(18, 24, 38), outline=(51, 65, 85))
        im.paste(crop_cb, (cx, cy))

    # Right: Outreach Wave Trigger Details
    draw_card(draw, [(1145, 100), (1860, 935)], fill=(18, 24, 38), outline=(51, 65, 85))
    draw.text((1175, 130), "NWS HAZARD INGESTION", fill=(245, 158, 11), font=fonts["h2"])
    draw.text((1175, 170), "EventBridge Trigger & Priority Wave Outreach", fill=(148, 163, 184), font=fonts["small_bold"])

    steps = [
        ("NWS Weather Event", "api.weather.gov emits EXTREME HEAT WARNING for Benton County.", (239, 68, 68)),
        ("Lambda: NwsPoll", "Polls active alerts every 15 min; triggers AgentCore Runtime with hazard.detected.", (245, 158, 11)),
        ("Priority Tier Sorting", "40 residents prioritized by vulnerability: Tier 1 (11), Tier 2 (18), Tier 3 (11).", (99, 102, 241)),
        ("Parallel Outreach Wave", "All 40 check-in messages dispatched concurrently in 11.2 seconds.", (52, 211, 153)),
        ("Allowlist Enforcement", "Zero sends outside PHONE_ALLOWLIST; strict synthetic mode guardrail.", (6, 182, 212))
    ]
    cur_y = 230
    for title, desc, col in steps:
        draw.rounded_rectangle([(1175, cur_y), (1830, cur_y + 110)], radius=12, fill=(30, 41, 59), outline=(51, 65, 85))
        draw.ellipse([(1195, cur_y + 20), (1211, cur_y + 36)], fill=col)
        draw.text((1225, cur_y + 16), title, fill=(248, 250, 252), font=fonts["body_bold"])
        draw.text((1225, cur_y + 52), desc, fill=(203, 213, 225), font=fonts["small"])
        cur_y += 135

    draw_subtitles(draw, fonts, "Let's see Porchlight in action. When the NWS issues an Extreme Heat Warning for Benton County, Porchlight detects the hazard and fires an automated outreach wave across all forty residents, prioritizing Tier 1 high-risk neighbors.")
    save_frame(im, "shot_3a")

def render_shot_3b():
    im, draw, fonts = create_base_canvas(3, "Live Demo · NWS Heat Alert & Wave Outreach")
    
    # Left: Smartphone Telegram Mockup showing incoming check-in
    messages = [
        (False, "Porchlight Neighbors: Hi Ruth, extreme heat through tomorrow, hottest afternoon. Reply 1 if you're OK, 2 if you need help, or just tell me. Reply STOP to opt out.", "14:00", "Outreach Wave")
    ]
    draw_phone_mockup(draw, fonts, (100, 140, 720, 880), "@porchlight_checkon_bot", messages)

    # Right: Resident Profile & Outreach Safety Details
    draw_card(draw, [(780, 140), (1820, 880)], fill=(18, 24, 38), outline=(51, 65, 85))
    draw.text((820, 180), "TARGETED RESIDENT: RUTH ALVAREZ", fill=(245, 158, 11), font=fonts["h1"])
    draw.text((820, 230), "Resident #1  ·  Priority Tier 1 (High Risk)  ·  Lives Alone", fill=(203, 213, 225), font=fonts["h2"])

    # Info pills
    pills = [
        ("Age Band:", "80-84", (99, 102, 241)),
        ("Mobility:", "Wheelchair / Walker", (239, 68, 68)),
        ("Medical Device:", "Oxygen Concentrator", (245, 158, 11)),
        ("Preferred Language:", "English / Spanish bilingual", (52, 211, 153))
    ]
    cur_x = 820
    cur_y = 290
    for label, val, col in pills:
        draw.rounded_rectangle([(cur_x, cur_y), (cur_x + 450, cur_y + 75)], radius=10, fill=(30, 41, 59), outline=(71, 85, 105))
        draw.text((cur_x + 20, cur_y + 14), label, fill=(148, 163, 184), font=fonts["small"])
        draw.text((cur_x + 20, cur_y + 40), val, fill=(248, 250, 252), font=fonts["body_bold"])
        cur_x += 480
        if cur_x > 1400:
            cur_x = 820
            cur_y += 95

    # Core Outreach Invariant
    draw.rounded_rectangle([(820, 510), (1780, 820)], radius=14, fill=(20, 32, 48), outline=(99, 102, 241), width=2)
    draw.text((850, 540), "OUTREACH INVARIANTS & SAFETY PROTECTIONS", fill=(99, 102, 241), font=fonts["h2"])
    
    invariants = [
        ("Zero Spam Protection:", "Single concise check-in text dispatched per hazard day; no duplicate pinging."),
        ("Mandatory Opt-Out:", "Every initial text explicitly contains 'Reply STOP to opt out'."),
        ("Deterministic Edge Handling:", "STOP, UNSTOP, and HELP handled instantaneously without LLM latency."),
        ("Strict Allowlist Guard:", "Synthetics assert phone against PHONE_ALLOWLIST before dispatch.")
    ]
    iy = 590
    for title, desc in invariants:
        draw.ellipse([(850, iy + 6), (862, iy + 18)], fill=(52, 211, 153))
        draw.text((880, iy), title, fill=(248, 250, 252), font=fonts["body_bold"])
        draw.text((880, iy + 26), desc, fill=(203, 213, 225), font=fonts["small"])
        iy += 55

    draw_subtitles(draw, fonts, "Ruth Alvarez, an eighty-two-year-old resident living alone with limited mobility, instantly receives a personalized bilingual check-in on Telegram asking if she is safe, with clear reply options and mandatory opt-out protections.")
    save_frame(im, "shot_3b")

def render_shot_4a():
    im, draw, fonts = create_base_canvas(4, "Live Demo · Deterministic Wellness Short-Circuit")
    
    # Left: Smartphone Telegram Mockup showing incoming check-in + Ruth replying "1"
    messages = [
        (False, "Porchlight Neighbors: Hi Ruth, extreme heat through tomorrow, hottest afternoon. Reply 1 if you're OK, 2 if you need help, or just tell me. Reply STOP to opt out.", "14:00", ""),
        (True, "1", "14:02", "")
    ]
    draw_phone_mockup(draw, fonts, (100, 140, 720, 880), "@porchlight_checkon_bot", messages)

    # Right: Short-Circuit Triage Explanation
    draw_card(draw, [(780, 140), (1820, 880)], fill=(18, 24, 38), outline=(51, 65, 85))
    draw.text((820, 180), "DETERMINISTIC INBOUND SHORT-CIRCUIT", fill=(52, 211, 153), font=fonts["h1"])
    draw.text((820, 230), "Unambiguous wellness replies bypass model inference entirely.", fill=(203, 213, 225), font=fonts["h2"])

    flow_steps = [
        ("1. Telegram Webhook Received", "Lambda TelegramInbound routes incoming '1' from Ruth Alvarez.", (99, 102, 241)),
        ("2. Short-Circuit Rule Triggered", "Regex matches strict '^1$' pattern: status=ok, need=none, confidence=1.0.", (52, 211, 153)),
        ("3. Zero LLM Tokens Consumed", "Zero model latency, zero Bedrock API cost, zero hallucination risk.", (245, 158, 11)),
        ("4. Immutable Audit Record", "Logged to Supabase audit_log: triage:ok | Ruth Alvarez quote='1'.", (6, 182, 212)),
        ("5. Live Console Dispatch Update", "Ruth Alvarez's status badge turns green 'ok' on operator dashboard in 0.85s.", (52, 211, 153))
    ]
    cur_y = 300
    for title, desc, col in flow_steps:
        draw.rounded_rectangle([(820, cur_y), (1780, cur_y + 90)], radius=12, fill=(30, 41, 59), outline=(51, 65, 85))
        draw.rounded_rectangle([(845, cur_y + 18), (865, cur_y + 38)], radius=4, fill=col)
        draw.text((885, cur_y + 14), title, fill=(248, 250, 252), font=fonts["body_bold"])
        draw.text((885, cur_y + 48), desc, fill=(203, 213, 225), font=fonts["small"])
        cur_y += 110

    draw_subtitles(draw, fonts, "Ruth replies with a quick '1'. Porchlight doesn't waste LLM tokens or introduce model latency for unambiguous answers.")
    save_frame(im, "shot_4a")

def render_shot_4b():
    im, draw, fonts = create_base_canvas(4, "Live Demo · Deterministic Wellness Short-Circuit")
    
    # Left: Massive Latency & Efficiency Card
    draw_card(draw, [(60, 120), (820, 910)], fill=(16, 32, 26), outline=(5, 150, 105), width=2)
    draw.rounded_rectangle([(95, 150), (360, 190)], radius=6, fill=(6, 95, 70))
    draw.text((115, 158), "BENCHMARK PERFORMANCE", fill=(167, 243, 208), font=fonts["small_bold"])
    
    draw.text((95, 230), "0.85s", fill=(52, 211, 153), font=fonts["huge_stat"])
    draw.text((95, 340), "Total Inbound-to-Console Latency", fill=(248, 250, 252), font=fonts["h2"])
    draw.text((95, 380), "Sub-second turnaround from resident send to live board refresh.", fill=(148, 163, 184), font=fonts["body"])

    metrics = [
        ("Confidence Score:", "1.00 (Deterministic)", (52, 211, 153)),
        ("Model Latency:", "0.00 ms (Zero LLM Overhead)", (52, 211, 153)),
        ("API Cost:", "$0.0000 per check-in", (245, 158, 11)),
        ("Status Assigned:", "ok (Green Badge)", (52, 211, 153)),
        ("Need Assigned:", "none (No Volunteer Required)", (203, 213, 225))
    ]
    cur_y = 440
    for label, val, col in metrics:
        draw.rounded_rectangle([(95, cur_y), (785, cur_y + 65)], radius=10, fill=(24, 46, 38), outline=(16, 110, 80))
        draw.text((120, cur_y + 18), label, fill=(203, 213, 225), font=fonts["body"])
        draw.text((450, cur_y + 18), val, fill=col, font=fonts["body_bold"])
        cur_y += 85

    # Right: Dispatch Board row highlight
    draw_card(draw, [(860, 120), (1860, 910)], fill=(18, 24, 38), outline=(51, 65, 85))
    draw.text((900, 150), "LIVE CONSOLE DISPATCH BOARD", fill=(245, 158, 11), font=fonts["h2"])
    draw.text((900, 190), "Status badge instantly updates under anonymous PostgREST RLS", fill=(148, 163, 184), font=fonts["small"])

    # Simulated Roster Table Row
    draw.rounded_rectangle([(900, 240), (1820, 480)], radius=12, fill=(30, 41, 59), outline=(52, 211, 153), width=2)
    # Header
    draw.text((930, 260), "RESIDENT", fill=(148, 163, 184), font=fonts["small_bold"])
    draw.text((1200, 260), "TIER", fill=(148, 163, 184), font=fonts["small_bold"])
    draw.text((1330, 260), "STATUS", fill=(148, 163, 184), font=fonts["small_bold"])
    draw.text((1480, 260), "NEED", fill=(148, 163, 184), font=fonts["small_bold"])
    draw.text((1630, 260), "LAST CONTACT", fill=(148, 163, 184), font=fonts["small_bold"])
    draw.line([(930, 295), (1790, 295)], fill=(71, 85, 105), width=1)

    # Row 1: Ruth Alvarez
    draw.text((930, 320), "Ruth Alvarez", fill=(248, 250, 252), font=fonts["h2"])
    draw.text((930, 360), "+1 555-010-001  ·  82 yrs  ·  Mobility Ltd", fill=(148, 163, 184), font=fonts["small"])
    
    draw.rounded_rectangle([(1200, 330), (1270, 365)], radius=6, fill=(127, 29, 29))
    draw.text((1215, 336), "Tier 1", fill=(254, 202, 202), font=fonts["small_bold"])

    draw.rounded_rectangle([(1330, 325), (1420, 370)], radius=8, fill=(6, 95, 70), outline=(52, 211, 153), width=2)
    draw.text((1355, 334), "ok", fill=(167, 243, 208), font=fonts["body_bold"])

    draw.text((1480, 336), "none", fill=(203, 213, 225), font=fonts["body"])
    draw.text((1630, 336), "14:02 (0.85s)", fill=(52, 211, 153), font=fonts["body_bold"])

    # Audit timeline below
    draw.rounded_rectangle([(900, 520), (1820, 870)], radius=12, fill=(24, 32, 47), outline=(51, 65, 85))
    draw.text((930, 545), "IMMUTABLE AUDIT TIMELINE (Supabase audit_log)", fill=(99, 102, 241), font=fonts["h2"])
    
    timeline = [
        ("14:02:08.120", "triage:ok", "Ruth Alvarez: status=ok, need=none, quote='1', confidence=1.00 (deterministic short-circuit)"),
        ("14:02:08.970", "console_sync", "Console dispatch board re-rendered via PostgREST RLS read-only query."),
        ("14:00:11.200", "wave_outreach:sent", "Check-in text dispatched to Ruth Alvarez via Telegram Bot API (@porchlight_checkon_bot)."),
        ("14:00:00.010", "hazard:detected", "AWS EventBridge detected NWS Extreme Heat Warning ARZ001. Runtime session initiated.")
    ]
    ty = 600
    for ts, ev, desc in timeline:
        draw.text((930, ty), ts, fill=(148, 163, 184), font=fonts["code"])
        draw.rounded_rectangle([(1100, ty - 2), (1280, ty + 24)], radius=4, fill=(30, 41, 59))
        draw.text((1115, ty), ev, fill=(52, 211, 153), font=fonts["small_bold"])
        draw.text((1300, ty), desc, fill=(248, 250, 252), font=fonts["small"])
        ty += 65

    draw_subtitles(draw, fonts, "A deterministic short-circuit classifies simple wellness checks in just zero-point-eight-five seconds, instantly turning her status badge green on the operator board so the coordinator knows she is safe.")
    save_frame(im, "shot_4b")

def render_shot_5a():
    im, draw, fonts = create_base_canvas(5, "Live Demo · Medical Distress & Structured Triage")
    
    # Left: Smartphone Telegram Mockup showing incoming distress message
    messages = [
        (False, "Porchlight Neighbors: Hi Ruth, extreme heat through tomorrow, hottest afternoon. Reply 1 if you're OK, 2 if you need help, or just tell me. Reply STOP to opt out.", "14:00", ""),
        (True, "AC broke, dizzy", "14:15", "")
    ]
    draw_phone_mockup(draw, fonts, (100, 140, 720, 880), "@porchlight_checkon_bot", messages)

    # Right: Acute Distress Trigger & Claude 3.5 Sonnet Analysis
    draw_card(draw, [(780, 140), (1820, 880)], fill=(18, 24, 38), outline=(51, 65, 85))
    draw.text((820, 180), "ACUTE DISTRESS SCENARIO ARRIVES", fill=(239, 68, 68), font=fonts["h1"])
    draw.text((820, 230), "Resident replies: \"AC broke, dizzy\" during 105°F heat dome.", fill=(254, 202, 202), font=fonts["h2"])

    cards = [
        ("Natural Language Understanding", "Ambiguous, conversational, or panicked replies cannot be solved by regex keyword match.", (99, 102, 241)),
        ("Claude 3.5 Sonnet on Bedrock", "Strands ResidentAgent invokes Claude 3.5 Sonnet via AWS Bedrock inference profile.", (245, 158, 11)),
        ("100% Quote Grounding", "Liability requirement: triage must extract the exact resident substring ('AC broke, dizzy').", (52, 211, 153)),
        ("Clinical Severity Assessment", "Combination of cooling equipment loss and neurological symptom (dizziness) flags medical.", (239, 68, 68)),
        ("Safety Intercept Preparation", "System halts before calling external services; never dials 911.", (245, 158, 11))
    ]
    cur_y = 300
    for title, desc, col in cards:
        draw.rounded_rectangle([(820, cur_y), (1780, cur_y + 90)], radius=12, fill=(30, 41, 59), outline=(51, 65, 85))
        draw.ellipse([(845, cur_y + 24), (861, cur_y + 40)], fill=col)
        draw.text((885, cur_y + 14), title, fill=(248, 250, 252), font=fonts["body_bold"])
        draw.text((885, cur_y + 48), desc, fill=(203, 213, 225), font=fonts["small"])
        cur_y += 110

    draw_subtitles(draw, fonts, "Moments later, a critical reply arrives: 'AC broke, dizzy'. Strands triage analyzes the symptoms with Claude 3.5 Sonnet on Bedrock, extracts the exact quote for liability records...")
    save_frame(im, "shot_5a")

def render_shot_5b():
    im, draw, fonts = create_base_canvas(5, "Live Demo · Medical Distress & Structured Triage")
    
    # Left: Structured Triage Card
    draw_card(draw, [(60, 110), (960, 920)], fill=(32, 18, 24), outline=(239, 68, 68), width=2)
    draw.rounded_rectangle([(95, 140), (450, 180)], radius=6, fill=(127, 29, 29))
    draw.text((115, 148), "STRANDS STRUCTURED TRIAGE", fill=(254, 202, 202), font=fonts["small_bold"])

    draw.text((95, 205), "Pydantic Triage Output", fill=(248, 250, 252), font=fonts["h1"])
    
    # JSON-like structured card
    schema_fields = [
        ("status:", "medical", (239, 68, 68)),
        ("need:", "cooling", (245, 158, 11)),
        ("quote:", "\"AC broke, dizzy\"", (52, 211, 153)),
        ("confidence:", "0.95", (248, 250, 252)),
        ("reason:", "\"Air conditioning failure causing dizziness in extreme heat\"", (203, 213, 225))
    ]
    cur_y = 265
    for field, val, col in schema_fields:
        draw.rounded_rectangle([(95, cur_y), (925, cur_y + 65)], radius=10, fill=(48, 24, 32), outline=(127, 29, 29))
        draw.text((120, cur_y + 18), field, fill=(148, 163, 184), font=fonts["code_bold"])
        draw.text((310, cur_y + 18), val, fill=col, font=fonts["code_bold"])
        cur_y += 80

    # Liability notice
    draw.rounded_rectangle([(95, 685), (925, 885)], radius=12, fill=(20, 26, 38), outline=(71, 85, 105))
    draw.text((120, 710), "ETHICS & PEOPLE-SAFETY MANDATE", fill=(245, 158, 11), font=fonts["h2"])
    draw.text((120, 755), "• NEVER-911 POLICY: No 911 tool exists anywhere in codebase.", fill=(248, 250, 252), font=fonts["body"])
    draw.text((120, 795), "• Escalation ladder strictly terminates at designated emergency contact.", fill=(248, 250, 252), font=fonts["body"])
    draw.text((120, 835), "• Autonomous action is HALTED — human coordinator retains full authority.", fill=(248, 250, 252), font=fonts["body"])

    # Right: Console Resident Detail View Crop
    cr_path = "docs/media/console-resident.png"
    if os.path.exists(cr_path):
        cr_img = Image.open(cr_path)
        cr_img.thumbnail((860, 810), Image.Resampling.LANCZOS)
        cx = 990 + (860 - cr_img.width) // 2
        cy = 110 + (810 - cr_img.height) // 2
        draw_card(draw, [(985, 110), (1860, 920)], fill=(18, 24, 38), outline=(51, 65, 85))
        im.paste(cr_img, (cx, cy))

    draw_subtitles(draw, fonts, "...and classifies the situation as a medical emergency requiring cooling. But Porchlight never takes high-stakes actions autonomously, and our system never calls 911.")
    save_frame(im, "shot_5b")

def render_shot_6a():
    im, draw, fonts = create_base_canvas(6, "Coordinator Gate · Strands BeforeToolCall Intercept")
    
    # Central Hook Flow Card
    draw_card(draw, [(60, 110), (1860, 920)], fill=(18, 24, 38), outline=(99, 102, 241), width=2)
    draw.text((95, 140), "STRANDS COORDINATOR GATE INTERCEPT", fill=(99, 102, 241), font=fonts["h1"])
    draw.text((95, 190), "Autonomous action safely held by BeforeToolCallEvent hook.", fill=(203, 213, 225), font=fonts["h2"])

    steps = [
        ("1. Agent Proposes Tool Call", "ResidentAgent initiates escalate_medical(resident_id='R-001', need='cooling')", (239, 68, 68), "PROPOSED"),
        ("2. Strands Intercept Hook Fires", "CoordinatorGate listens on BeforeToolCallEvent. Halts execution before tool runs.", (245, 158, 11), "HELD"),
        ("3. State Persisted to Supabase", "Record inserted to porchlight.gate_pending with status='open' and decision payload.", (6, 182, 212), "STORED"),
        ("4. Consolidated Ping to Coordinator", "Consolidates all pending alerts into a single Telegram message with numbered options.", (52, 211, 153), "NOTIFIED"),
        ("5. Human-in-the-Loop Authority", "The human coordinator holds sole decision power. System resumes only upon approval.", (99, 102, 241), "GOVERNED")
    ]
    cur_y = 260
    for title, desc, col, badge in steps:
        draw.rounded_rectangle([(95, cur_y), (1825, cur_y + 105)], radius=12, fill=(30, 41, 59), outline=(51, 65, 85))
        draw.rounded_rectangle([(120, cur_y + 24), (230, cur_y + 64)], radius=6, fill=col)
        draw.text((140, cur_y + 32), badge, fill=(255, 255, 255), font=fonts["small_bold"])
        
        draw.text((260, cur_y + 20), title, fill=(248, 250, 252), font=fonts["h2"])
        draw.text((260, cur_y + 60), desc, fill=(203, 213, 225), font=fonts["body"])
        cur_y += 125

    draw_subtitles(draw, fonts, "Instead, a Strands BeforeToolCall hook intercepts the execution, holds the automated action in a pending queue, and sends a single consolidated alert to the coordinator's phone.")
    save_frame(im, "shot_6a")

def render_shot_6b():
    im, draw, fonts = create_base_canvas(6, "Coordinator Gate · Strands BeforeToolCall Intercept")
    
    # Left: Smartphone Telegram Mockup on Coordinator Channel
    messages = [
        (False, "[Coordinator] Porchlight - Extreme Heat Warning: 1 OK out of 40 checked.\n\nMedical-sounding (Ruth Alvarez): \"AC broke, dizzy\".\n\n1: Send volunteer Marcus Webb with AC/cooling transport\n2: I'll handle it directly\n\nReply 1 or 2", "14:16", "Priority Alert"),
        (True, "1", "14:17", "")
    ]
    draw_phone_mockup(draw, fonts, (100, 130, 800, 890), "[Coordinator Channel]", messages)

    # Right: Coordinator Approval & Decision Processing
    draw_card(draw, [(850, 130), (1840, 890)], fill=(18, 24, 38), outline=(51, 65, 85))
    draw.text((890, 170), "ONE-TAP COORDINATOR RESOLUTION", fill=(245, 158, 11), font=fonts["h1"])
    draw.text((890, 220), "Coordinator replies '1' via Telegram to approve volunteer dispatch.", fill=(203, 213, 225), font=fonts["h2"])

    details = [
        ("Consolidated Context:", "Coordinator receives concise count of safe neighbors plus urgent triage summaries.", (99, 102, 241)),
        ("Actionable Options:", "Clear 1/2 choices avoid typing long instructions while managing emergencies.", (52, 211, 153)),
        ("Gate Status Transition:", "Supabase gate_pending record transitions from 'open' to 'approved'.", (6, 182, 212)),
        ("Audit Compliance:", "audit_log records 'coordinator_approved:escalate_medical' with millisecond UTC timestamp.", (245, 158, 11)),
        ("Dispatcher Awakening:", "Approving Option 1 automatically triggers Strands volunteer matching workflow.", (52, 211, 153))
    ]
    cur_y = 290
    for title, desc, col in details:
        draw.rounded_rectangle([(890, cur_y), (1800, cur_y + 90)], radius=12, fill=(30, 41, 59), outline=(51, 65, 85))
        draw.ellipse([(915, cur_y + 24), (931, cur_y + 40)], fill=col)
        draw.text((955, cur_y + 14), title, fill=(248, 250, 252), font=fonts["body_bold"])
        draw.text((955, cur_y + 48), desc, fill=(203, 213, 225), font=fonts["small"])
        cur_y += 110

    draw_subtitles(draw, fonts, "The coordinator sees the resident's name, triage reason, and numbered choices. Replying '1' authorizes dispatching a verified neighborhood volunteer.")
    save_frame(im, "shot_6b")

def render_shot_7a():
    im, draw, fonts = create_base_canvas(7, "Volunteer Matching & Dispatch Fulfillment")
    
    # Left: Strands Dispatcher Match Engine
    draw_card(draw, [(60, 120), (960, 910)], fill=(18, 24, 38), outline=(51, 65, 85))
    draw.text((95, 150), "STRANDS DISPATCHER ENGINE", fill=(52, 211, 153), font=fonts["h1"])
    draw.text((95, 195), "Intelligent Resource & Volunteer Matching", fill=(148, 163, 184), font=fonts["body_bold"])

    # Match Cards
    draw.rounded_rectangle([(95, 250), (925, 410)], radius=12, fill=(30, 41, 59), outline=(99, 102, 241), width=2)
    draw.text((120, 270), "MATCHED COOLING CENTER", fill=(99, 102, 241), font=fonts["small_bold"])
    draw.text((120, 305), "Pea Ridge Library Cooling Center", fill=(248, 250, 252), font=fonts["h2"])
    draw.text((120, 350), "Distance: 1.2 miles  ·  Capacity: 45  ·  Status: OPEN (Generator Backed)", fill=(203, 213, 225), font=fonts["small"])

    draw.rounded_rectangle([(95, 435), (925, 595)], radius=12, fill=(30, 41, 59), outline=(52, 211, 153), width=2)
    draw.text((120, 455), "MATCHED VERIFIED VOLUNTEER", fill=(52, 211, 153), font=fonts["small_bold"])
    draw.text((120, 490), "Marcus Webb", fill=(248, 250, 252), font=fonts["h2"])
    draw.text((120, 535), "Role: Driver / Transport  ·  Vehicle: A/C Equipped  ·  Phone Allowlisted", fill=(203, 213, 225), font=fonts["small"])

    # Coordination logic
    draw.rounded_rectangle([(95, 620), (925, 875)], radius=12, fill=(20, 28, 42), outline=(71, 85, 105))
    draw.text((120, 645), "DISPATCHER INVARIANTS", fill=(245, 158, 11), font=fonts["h2"])
    draw.text((120, 690), "• One volunteer contacted at a time to prevent duplicate driver runs.", fill=(248, 250, 252), font=fonts["body"])
    draw.text((120, 735), "• 10-minute response timeout before failing over to secondary volunteer.", fill=(248, 250, 252), font=fonts["body"])
    draw.text((120, 780), "• Volunteer must be registered in Supabase volunteers table with consent.", fill=(248, 250, 252), font=fonts["body"])
    draw.text((120, 825), "• All transit schedules logged to community Google Calendar.", fill=(248, 250, 252), font=fonts["body"])

    # Right: Smartphone Telegram Mockup to Volunteer Marcus Webb
    messages = [
        (False, "Porchlight: can you take Ruth Alvarez to Pea Ridge Library Cooling Center at 2pm? Reply Y or N", "14:18", "Dispatch Request")
    ]
    draw_phone_mockup(draw, fonts, (1050, 120, 1780, 890), "Marcus Webb (Volunteer)", messages)

    draw_subtitles(draw, fonts, "Porchlight instantly matches the nearest open cooling center, identifies opted-in volunteer driver Marcus Webb, and texts him the transport request.")
    save_frame(im, "shot_7a")

def render_shot_7b():
    im, draw, fonts = create_base_canvas(7, "Volunteer Matching & Dispatch Fulfillment")
    
    # Left: Smartphone Telegram Mockup showing Marcus accepting "Y"
    messages = [
        (False, "Porchlight: can you take Ruth Alvarez to Pea Ridge Library Cooling Center at 2pm? Reply Y or N", "14:18", ""),
        (True, "Y", "14:19", ""),
        (False, "Thank you Marcus! Transport logged for Ruth Alvarez at 2:00 PM. Pea Ridge Library Cooling Center notified.", "14:19", "Confirmed")
    ]
    draw_phone_mockup(draw, fonts, (80, 120, 780, 910), "Marcus Webb (Volunteer)", messages)

    # Right: Dispatch Fulfillment & Verification
    draw_card(draw, [(830, 120), (1860, 910)], fill=(18, 24, 38), outline=(5, 150, 105), width=2)
    draw.rounded_rectangle([(870, 150), (1170, 190)], radius=6, fill=(6, 95, 70))
    draw.text((890, 158), "COMMUNITY FULFILLMENT CLOSED", fill=(167, 243, 208), font=fonts["small_bold"])

    draw.text((870, 220), "Dispatch Loop Closed in < 2 Minutes", fill=(52, 211, 153), font=fonts["h1"])

    dispatch_rows = [
        ("Dispatch Status:", "ACCEPTED (Confirmed via Telegram)", (52, 211, 153)),
        ("Transport Assigned:", "Marcus Webb -> Ruth Alvarez", (248, 250, 252)),
        ("Cooling Destination:", "Pea Ridge Library Cooling Center", (245, 158, 11)),
        ("Google Calendar:", "Event Created: 'Porchlight: Transport Ruth Alvarez @ 2:00 PM'", (99, 102, 241)),
        ("Operator Console:", "Dispatches board row updated to 'accepted' in real time", (52, 211, 153)),
        ("Audit Verification:", "audit_log entry: volunteer_accepted (id=disp-001)", (6, 182, 212))
    ]
    cur_y = 290
    for label, val, col in dispatch_rows:
        draw.rounded_rectangle([(870, cur_y), (1820, cur_y + 75)], radius=10, fill=(30, 41, 59), outline=(51, 65, 85))
        draw.text((895, cur_y + 22), label, fill=(148, 163, 184), font=fonts["body_bold"])
        draw.text((1180, cur_y + 22), val, fill=col, font=fonts["body_bold"])
        cur_y += 92

    # Bottom Stat Callout
    draw.rounded_rectangle([(870, 780), (1820, 875)], radius=12, fill=(16, 32, 26), outline=(5, 150, 105))
    draw.text((900, 810), "TOTAL TIME: 1m 48s FROM DISTRESS REPLY TO CONFIRMED DRIVER", fill=(52, 211, 153), font=fonts["h2"])

    draw_subtitles(draw, fonts, "Marcus replies 'Y' to accept. The dispatch updates to accepted in real time on the console, and a calendar event is scheduled—closing the critical loop in under two minutes.")
    save_frame(im, "shot_7b")

def render_shot_8a():
    im, draw, fonts = create_base_canvas(8, "Safety Architecture & Triage Evals")
    
    # 4 Defense-in-Depth Guardrail Cards
    draw.text((60, 105), "DEFENSE-IN-DEPTH SAFETY ARCHITECTURE", fill=(245, 158, 11), font=fonts["h1"])
    draw.text((60, 155), "Strict guardrails engineered specifically for vulnerable populations.", fill=(203, 213, 225), font=fonts["body_bold"])

    guardrails = [
        ("PHONE_ALLOWLIST GUARD", "Strict synthetic mode assert before any text or call is initiated. Zero outbound messages can escape the verified test perimeter.", (239, 68, 68), "HARD ASSERTION"),
        ("NEVER-911 POLICY", "No tool or capability to call emergency 911 exists in the codebase. Medical escalations terminate at the designated emergency contact with advisory copy.", (245, 158, 11), "ETHICAL BOUNDARY"),
        ("MANDATORY OPT-OUT COMPLIANCE", "First message to any resident carries 'Reply STOP to opt out'. Inbound STOP, UNSTOP, and HELP handled deterministically at the edge without LLM.", (52, 211, 153), "REGULATORY COMPLIANCE"),
        ("POSTGREST ROW LEVEL SECURITY", "Supabase anonymous access is strictly read-only SELECT. Direct mutations return Error 42501; database writes require backend service role credentials.", (99, 102, 241), "DATABASE HARDENING")
    ]
    
    # 2x2 Grid
    coords = [
        (60, 210, 930, 540),
        (980, 210, 1860, 540),
        (60, 580, 930, 910),
        (980, 580, 1860, 910)
    ]
    for i, (title, desc, col, tag) in enumerate(guardrails):
        x1, y1, x2, y2 = coords[i]
        draw_card(draw, [(x1, y1), (x2, y2)], fill=(18, 24, 38), outline=col, width=2)
        
        tw = draw.textlength(tag, font=fonts["small_bold"])
        draw.rounded_rectangle([(x1 + 30, y1 + 25), (x1 + 30 + int(tw) + 32, y1 + 60)], radius=6, fill=col)
        draw.text((x1 + 46, y1 + 32), tag, fill=(255, 255, 255), font=fonts["small_bold"])
        
        draw.text((x1 + 30, y1 + 80), title, fill=(248, 250, 252), font=fonts["h2"])
        
        # Wrapped description
        from generate_slides_core import wrap_text_multi
        lines = wrap_text_multi(desc, max_chars=46)
        for j, line in enumerate(lines):
            draw.text((x1 + 30, y1 + 135 + j * 32), line, fill=(203, 213, 225), font=fonts["body"])

    draw_subtitles(draw, fonts, "Safety is built into every layer. In synthetic mode, a strict phone allowlist guarantees zero texts escape the test perimeter. We enforce a strict never-911 policy, directing escalations to family and neighborhood emergency contacts.")
    save_frame(im, "shot_8a")

def render_shot_8b():
    im, draw, fonts = create_base_canvas(8, "Safety Architecture & Triage Evals")
    
    # Left: 30 Adversarial Evals Benchmark Table
    draw_card(draw, [(60, 110), (1100, 920)], fill=(18, 24, 38), outline=(51, 65, 85))
    draw.text((95, 140), "30 ADVERSARIAL REPLIES BENCHMARK", fill=(52, 211, 153), font=fonts["h1"])
    draw.text((95, 185), "evals/replies/cases.json validated with Claude 3.5 Sonnet", fill=(148, 163, 184), font=fonts["small_bold"])

    # Table Header
    draw.rounded_rectangle([(95, 230), (1065, 290)], radius=8, fill=(30, 41, 59))
    draw.text((120, 248), "EVALUATION METRIC", fill=(148, 163, 184), font=fonts["small_bold"])
    draw.text((560, 248), "THRESHOLD", fill=(148, 163, 184), font=fonts["small_bold"])
    draw.text((760, 248), "RESULT", fill=(148, 163, 184), font=fonts["small_bold"])
    draw.text((940, 248), "STATUS", fill=(148, 163, 184), font=fonts["small_bold"])

    rows = [
        ("Status Classification", ">= 27 / 30 (90%)", "27 / 30", "PASS", (52, 211, 153)),
        ("Need Identification", ">= 26 / 30 (87%)", "26 / 30", "PASS", (52, 211, 153)),
        ("Quote Grounding (Zero Hallucination)", "= 30 / 30 (100%)", "30 / 30", "PASS", (52, 211, 153)),
        ("Deterministic Judge Verification", ">= 27 / 30 (90%)", "29 / 30", "PASS", (52, 211, 153))
    ]
    cur_y = 310
    for name, thresh, res, stat, col in rows:
        draw.rounded_rectangle([(95, cur_y), (1065, cur_y + 80)], radius=10, fill=(24, 32, 47), outline=(51, 65, 85))
        draw.text((120, cur_y + 24), name, fill=(248, 250, 252), font=fonts["body_bold"])
        draw.text((560, cur_y + 24), thresh, fill=(203, 213, 225), font=fonts["body"])
        draw.text((760, cur_y + 20), res, fill=col, font=fonts["h2"])
        draw.rounded_rectangle([(930, cur_y + 18), (1030, cur_y + 58)], radius=6, fill=(6, 95, 70))
        draw.text((945, cur_y + 24), stat, fill=(167, 243, 208), font=fonts["small_bold"])
        cur_y += 98

    # Bottom summary
    draw.rounded_rectangle([(95, 730), (1065, 885)], radius=12, fill=(16, 32, 26), outline=(5, 150, 105))
    draw.text((120, 755), "BENCHMARK SUMMARY: 4 / 4 CRITERIA PASSED", fill=(52, 211, 153), font=fonts["h2"])
    draw.text((120, 800), "• Tested against figurative speech ('I'm dying for some ice cream' -> ok)", fill=(203, 213, 225), font=fonts["small"])
    draw.text((120, 835), "• Tested Spanish idioms, phonetic typos, and understated family distress.", fill=(203, 213, 225), font=fonts["small"])

    # Right: Challenging Cases Highlight
    draw_card(draw, [(1135, 110), (1860, 920)], fill=(18, 24, 38), outline=(51, 65, 85))
    draw.text((1170, 140), "ADVERSARIAL STRESS-TEST EXAMPLES", fill=(245, 158, 11), font=fonts["h2"])
    draw.text((1170, 185), "Complex edge cases resolved correctly by Porchlight", fill=(148, 163, 184), font=fonts["small"])

    cases = [
        ("Figurative Hyperbole", "\"I'm dying for some ice cream!\"", "Triaged to 'ok' (not medical); understands conversational humor.", (52, 211, 153)),
        ("Understated Distress", "\"Mom hasn't gotten up from bed today.\"", "Triaged to 'needs_help' / 'wellness_check' (subtle risk detected).", (239, 68, 68)),
        ("Spanish Slang & Idiom", "\"Se me fue la luz y hace un calor de locos\"", "Triaged to 'needs_help' / 'power' + cooling center match.", (245, 158, 11)),
        ("Phonetic Typos", "\"ac is brokn very dzy plz hlp\"", "Triaged to 'medical' / 'cooling'; 100% extracted exact quote.", (99, 102, 241))
    ]
    cur_y = 230
    for tag, sample, resolution, col in cases:
        draw.rounded_rectangle([(1170, cur_y), (1825, cur_y + 140)], radius=12, fill=(30, 41, 59), outline=(51, 65, 85))
        draw.rounded_rectangle([(1195, cur_y + 16), (1380, cur_y + 46)], radius=6, fill=col)
        draw.text((1210, cur_y + 22), tag, fill=(255, 255, 255), font=fonts["small_bold"])
        draw.text((1195, cur_y + 60), sample, fill=(248, 250, 252), font=fonts["body_bold"])
        draw.text((1195, cur_y + 98), resolution, fill=(148, 163, 184), font=fonts["small"])
        cur_y += 160

    draw_subtitles(draw, fonts, "And our triage engine is battle-tested against thirty adversarial real-world replies—slang, typos, and Spanish idioms—achieving perfect one-hundred percent quote grounding and passing every benchmark.")
    save_frame(im, "shot_8b")

def render_shot_9a():
    im, draw, fonts = create_base_canvas(9, "Community Resilience & Open Source")
    
    # Grand Center Showcase
    draw_card(draw, [(160, 110), (1760, 920)], fill=(15, 22, 35), outline=(245, 158, 11), width=2)
    
    # Lantern glowing brand icon
    draw.ellipse([(910, 160), (1010, 260)], fill=(245, 158, 11))
    draw.ellipse([(925, 175), (995, 245)], fill=(254, 243, 199))
    draw.rectangle([(950, 190), (970, 230)], fill=(217, 119, 6))

    draw.text((820, 280), "PORCHLIGHT", fill=(245, 158, 11), font=fonts["huge_stat"])
    draw.text((580, 390), "Autonomous Extreme-Weather Wellness Check-In Agent", fill=(248, 250, 252), font=fonts["h1"])
    draw.text((630, 440), "Built for AWS Bedrock & Strands Agents Hackathon  ·  Good Neighbor Track", fill=(203, 213, 225), font=fonts["h2"])

    # 5 Key Architecture Badges
    techs = [
        ("AWS Bedrock", "AgentCore Runtime & Memory"),
        ("Strands Framework", "Multi-Agent Intelligence"),
        ("Telegram Bot API", "Two-Way Edge Messaging"),
        ("Supabase PostgreSQL", "Read-Only PostgREST RLS"),
        ("Next.js 16 Console", "AWS App Runner Container")
    ]
    cur_x = 220
    for name, sub in techs:
        draw.rounded_rectangle([(cur_x, 520), (cur_x + 280, 640)], radius=12, fill=(30, 41, 59), outline=(99, 102, 241))
        draw.text((cur_x + 20, 545), name, fill=(245, 158, 11), font=fonts["body_bold"])
        draw.text((cur_x + 20, 585), sub, fill=(148, 163, 184), font=fonts["small"])
        cur_x += 310

    # Closing Statement Card
    draw.rounded_rectangle([(220, 680), (1700, 880)], radius=14, fill=(20, 32, 48), outline=(52, 211, 153), width=2)
    draw.text((260, 715), "100% OPEN SOURCE UNDER THE MIT LICENSE", fill=(52, 211, 153), font=fonts["h2"])
    draw.text((260, 765), "Repository: github.com/your-org/porchlight  ·  Full Documentation & Proofs in docs/", fill=(248, 250, 252), font=fonts["body"])
    draw.text((260, 810), "\"Because in an extreme heat wave, no vulnerable neighbor should be left behind.\"", fill=(245, 158, 11), font=fonts["h2"])

    draw_subtitles(draw, fonts, "Porchlight transforms an overwhelming spreadsheet into an intelligent, liability-grade safety net for community resilience. Because in a heat wave, no vulnerable neighbor should be left behind. Porchlight is completely open source under the MIT License. Thank you for watching.")
    save_frame(im, "shot_9a")

def main():
    print("Rendering all 17 shots...")
    render_shot_1a()
    render_shot_1b()
    render_shot_2a()
    render_shot_2b()
    render_shot_3a()
    render_shot_3b()
    render_shot_4a()
    render_shot_4b()
    render_shot_5a()
    render_shot_5b()
    render_shot_6a()
    render_shot_6b()
    render_shot_7a()
    render_shot_7b()
    render_shot_8a()
    render_shot_8b()
    render_shot_9a()
    print("All 17 shots rendered successfully!")

if __name__ == "__main__":
    main()
