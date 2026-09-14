"""
Enhanced slide generation core for Porchlight 1080p demo video.
Provides balanced subtitles, dynamic badge sizing, clean message mockups,
and crisp typography.
"""

import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
FONT_DIR = "C:/Windows/Fonts"

def get_fonts():
    return {
        "title": ImageFont.truetype(os.path.join(FONT_DIR, "segoeuib.ttf"), 46),
        "scene_hdr": ImageFont.truetype(os.path.join(FONT_DIR, "segoeuib.ttf"), 22),
        "h1": ImageFont.truetype(os.path.join(FONT_DIR, "segoeuib.ttf"), 36),
        "h2": ImageFont.truetype(os.path.join(FONT_DIR, "segoeuib.ttf"), 28),
        "body": ImageFont.truetype(os.path.join(FONT_DIR, "segoeui.ttf"), 22),
        "body_bold": ImageFont.truetype(os.path.join(FONT_DIR, "segoeuib.ttf"), 22),
        "small": ImageFont.truetype(os.path.join(FONT_DIR, "segoeui.ttf"), 18),
        "small_bold": ImageFont.truetype(os.path.join(FONT_DIR, "segoeuib.ttf"), 18),
        "tiny": ImageFont.truetype(os.path.join(FONT_DIR, "segoeui.ttf"), 15),
        "code": ImageFont.truetype(os.path.join(FONT_DIR, "consola.ttf"), 20),
        "code_bold": ImageFont.truetype(os.path.join(FONT_DIR, "consolab.ttf"), 20),
        "subtitle": ImageFont.truetype(os.path.join(FONT_DIR, "segoeui.ttf"), 23),
        "big_stat": ImageFont.truetype(os.path.join(FONT_DIR, "segoeuib.ttf"), 72),
        "huge_stat": ImageFont.truetype(os.path.join(FONT_DIR, "segoeuib.ttf"), 96),
    }

def create_base_canvas(scene_num, scene_title):
    im = Image.new("RGB", (W, H), (11, 16, 26))
    draw = ImageDraw.Draw(im)
    
    # Smooth vertical gradient overlay
    for y in range(H):
        ratio = y / H
        r = int(10 * (1 - ratio) + 16 * ratio)
        g = int(14 * (1 - ratio) + 24 * ratio)
        b = int(24 * (1 - ratio) + 42 * ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Top Header Bar
    draw.rectangle([(0, 0), (W, 76)], fill=(15, 23, 42))
    draw.line([(0, 76), (W, 76)], fill=(38, 53, 77), width=2)
    
    fonts = get_fonts()
    
    # Logo / Brand
    draw.ellipse([(60, 24), (88, 52)], fill=(245, 158, 11))
    draw.text((102, 18), "PORCHLIGHT", fill=(245, 158, 11), font=fonts["scene_hdr"])
    draw.text((275, 20), "|  Extreme-Weather Wellness Agent  ·  AWS Bedrock & Strands", fill=(148, 163, 184), font=fonts["small"])
    
    # Scene pill badge on top right
    pill_text = f"SCENE {scene_num:02d} / 09 · {scene_title.upper()}"
    tw = draw.textlength(pill_text, font=fonts["small_bold"])
    pill_x1 = W - 60 - int(tw) - 36
    draw.rounded_rectangle([(pill_x1, 18), (W - 60, 56)], radius=19, fill=(30, 41, 59), outline=(99, 102, 241), width=2)
    draw.text((pill_x1 + 18, 24), pill_text, fill=(224, 231, 255), font=fonts["small_bold"])
    
    return im, draw, fonts

def balance_wrap(text, max_single_len=90, max_line_len=115):
    if len(text) <= max_single_len:
        return [text]
    words = text.split()
    best_diff = 9999
    best_split = len(words) // 2
    for i in range(1, len(words)):
        l1 = " ".join(words[:i])
        l2 = " ".join(words[i:])
        if len(l1) <= max_line_len and len(l2) <= max_line_len:
            diff = abs(len(l1) - len(l2))
            if diff < best_diff:
                best_diff = diff
                best_split = i
    l1 = " ".join(words[:best_split])
    l2 = " ".join(words[best_split:])
    return [l1, l2]

def wrap_text_multi(text, max_chars=45):
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        if len(cur + " " + w) <= max_chars:
            cur = (cur + " " + w).strip()
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def draw_subtitles(draw, fonts, text):
    box_x1, box_y1 = 60, 970
    box_x2, box_y2 = W - 60, 1055
    draw.rounded_rectangle([(box_x1, box_y1), (box_x2, box_y2)], radius=12, fill=(15, 23, 42), outline=(51, 65, 85), width=2)
    
    # CC icon
    draw.rounded_rectangle([(box_x1 + 16, box_y1 + 18), (box_x1 + 60, box_y1 + 50)], radius=6, fill=(99, 102, 241))
    draw.text((box_x1 + 24, box_y1 + 22), "VO", fill=(255, 255, 255), font=fonts["small_bold"])
    
    lines = balance_wrap(text)
    if len(lines) == 1:
        draw.text((box_x1 + 80, box_y1 + 27), lines[0], fill=(248, 250, 252), font=fonts["subtitle"])
    else:
        draw.text((box_x1 + 80, box_y1 + 14), lines[0], fill=(248, 250, 252), font=fonts["subtitle"])
        draw.text((box_x1 + 80, box_y1 + 46), lines[1], fill=(203, 213, 225), font=fonts["subtitle"])

def draw_card(draw, box, fill=(21, 30, 46), outline=(38, 53, 77), radius=16, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def draw_phone_mockup(draw, fonts, box, chat_title, messages):
    x1, y1, x2, y2 = box
    draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=24, fill=(18, 24, 38), outline=(51, 65, 85), width=3)
    
    # Phone header
    draw.rounded_rectangle([(x1, y1), (x2, y1 + 70)], radius=20, fill=(30, 41, 59))
    draw.rectangle([(x1, y1 + 50), (x2, y1 + 70)], fill=(30, 41, 59))
    draw.ellipse([(x1 + 24, y1 + 18), (x1 + 56, y1 + 50)], fill=(245, 158, 11))
    draw.text((x1 + 68, y1 + 15), chat_title, fill=(248, 250, 252), font=fonts["body_bold"])
    draw.text((x1 + 68, y1 + 42), "Telegram Bot  ·  Online", fill=(52, 211, 153), font=fonts["tiny"])
    
    # Render messages
    cur_y = y1 + 90
    for is_out, text, time_str, badge in messages:
        if is_out:
            bub_w = min(420, max(120, int(draw.textlength(text, font=fonts["body_bold"])) + 40))
            bx2 = x2 - 24
            bx1 = bx2 - bub_w
            draw.rounded_rectangle([(bx1, cur_y), (bx2, cur_y + 65)], radius=14, fill=(16, 110, 80), outline=(5, 150, 105), width=1)
            draw.text((bx1 + 16, cur_y + 12), text, fill=(255, 255, 255), font=fonts["body_bold"])
            status_text = f"{time_str} · Delivered"
            draw.text((bx1 + 16, cur_y + 38), status_text, fill=(167, 243, 208), font=fonts["tiny"])
            cur_y += 85
        else:
            lines = wrap_text_multi(text, max_chars=40)
            bub_h = len(lines) * 26 + 45
            bub_w = min(480, max(300, max(int(draw.textlength(l, font=fonts["body"])) for l in lines) + 40))
            bx1 = x1 + 24
            bx2 = bx1 + bub_w
            
            draw.rounded_rectangle([(bx1, cur_y), (bx2, cur_y + bub_h)], radius=14, fill=(30, 41, 59), outline=(71, 85, 105), width=1)
            for i, line in enumerate(lines):
                draw.text((bx1 + 16, cur_y + 12 + i * 26), line, fill=(241, 245, 249), font=fonts["body"])
            
            draw.text((bx1 + 16, cur_y + bub_h - 25), time_str, fill=(148, 163, 184), font=fonts["tiny"])
            if badge:
                draw.text((bx2 - 140, cur_y + bub_h - 25), badge, fill=(245, 158, 11), font=fonts["tiny"])
            cur_y += bub_h + 20

def save_frame(im, name):
    os.makedirs("build_media/frames", exist_ok=True)
    out_path = f"build_media/frames/{name}.png"
    im.save(out_path, quality=95)
    print(f"Saved frame {out_path}")
