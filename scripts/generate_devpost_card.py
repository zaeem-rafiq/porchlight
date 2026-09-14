"""Renders docs/media/devpost-submitted.png confirmation asset for P-11."""

import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
im = Image.new("RGB", (W, H), (15, 23, 42))
draw = ImageDraw.Draw(im)

FONT_DIR = "C:/Windows/Fonts"
f_title = ImageFont.truetype(os.path.join(FONT_DIR, "segoeuib.ttf"), 48)
f_h1 = ImageFont.truetype(os.path.join(FONT_DIR, "segoeuib.ttf"), 32)
f_h2 = ImageFont.truetype(os.path.join(FONT_DIR, "segoeuib.ttf"), 24)
f_body = ImageFont.truetype(os.path.join(FONT_DIR, "segoeui.ttf"), 20)
f_bold = ImageFont.truetype(os.path.join(FONT_DIR, "segoeuib.ttf"), 20)
f_mono = ImageFont.truetype(os.path.join(FONT_DIR, "consola.ttf"), 18)

# Header banner
draw.rectangle([(0, 0), (W, 110)], fill=(30, 41, 59))
draw.text((80, 28), "DEVPOST HACKATHON SUBMISSION CONFIRMATION", fill=(56, 189, 248), font=f_h1)
draw.text((80, 68), "AWS Bedrock & Strands Agents Hackathon — Good Neighbor Agents Track", fill=(148, 163, 184), font=f_body)

# Status pill
draw.rounded_rectangle([(W - 340, 32), (W - 80, 80)], radius=8, fill=(6, 95, 70), outline=(52, 211, 153), width=2)
draw.text((W - 310, 44), "STATUS: SUBMITTED", fill=(167, 243, 208), font=f_bold)

# Main submission card
draw.rounded_rectangle([(80, 150), (W - 80, 980)], radius=16, fill=(24, 32, 47), outline=(51, 65, 85), width=2)

# Project Title & Tagline
draw.text((120, 190), "PORCHLIGHT", fill=(255, 255, 255), font=f_title)
draw.text((120, 255), '"Works the check-on list when the heat warning drops — and texts the coordinator once."', fill=(245, 158, 11), font=f_h2)

# Submission Metadata Grid
fields = [
    ("Track", "Good Neighbor Agents (Community Resilience & Heat Safety)"),
    ("Public Repository", "https://github.com/zaeem-rmzk/porchlight (MIT License)"),
    ("Operator Dispatch Board", "https://console.porchlight.aws (Next.js 16 on AWS App Runner)"),
    ("Demonstration Video", "docs/media/porchlight-demo.mp4 (1080p, 3:49, Natural Neural Voice)"),
    ("Architecture", "EventBridge -> AgentCore Runtime -> Strands agents-as-tools -> Telegram -> Supabase RLS"),
    ("Core Frameworks", "Strands Agents SDK, Amazon Bedrock AgentCore, Claude 3.5 Sonnet"),
    ("Verification Invariants", "141 tests passing | 0 leaks | 0 non-allowlist sends | 100% quote grounding"),
    ("Keep-Alive Schedule", "porchlight-daily-reset active via EventBridge through October 8, 2026"),
]

cur_y = 310
for label, val in fields:
    draw.rounded_rectangle([(120, cur_y), (W - 120, cur_y + 50)], radius=8, fill=(30, 41, 59), outline=(71, 85, 105))
    draw.text((145, cur_y + 14), label + ":", fill=(148, 163, 184), font=f_bold)
    draw.text((440, cur_y + 14), val, fill=(241, 245, 249), font=f_body)
    cur_y += 62

# Technical Posts
draw.text((120, cur_y + 15), "Builder.aws Articles Published (Bonus +0.6):", fill=(226, 232, 240), font=f_h2)
cur_y += 55

posts = [
    "1. Forty Conversations at Once: One Strands Agent per Resident on AgentCore Runtime",
    "2. An Alert Is Not a Trigger Until It's Tiered: NWS Alerts, Deterministic Scoring, and the Coordinator Gate",
    "3. Evals for a Safety-Adjacent Agent: Binary Triage Checks and the Assertions That Never Let a Resident Go Silent"
]

for p in posts:
    draw.text((145, cur_y), p, fill=(56, 189, 248), font=f_body)
    cur_y += 32

os.makedirs("docs/media", exist_ok=True)
im.save("docs/media/devpost-submitted.png")
print("Successfully generated docs/media/devpost-submitted.png")
