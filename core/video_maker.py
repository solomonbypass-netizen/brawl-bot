import os
import io
import time
import logging
import requests
import numpy as np
import imageio
from PIL import Image, ImageDraw, ImageFont

from core.config import HEADERS, COOKIES

logger = logging.getLogger("AIVideoMaker")

# Resolution: Vertical 9:16 (Standard for TikTok, Shorts, Reels)
WIDTH = 720
HEIGHT = 1280

def get_font(size):
    """Safely loads cross-platform bold/regular fonts with fallback."""
    for font_name in ["arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf", "calibrib.ttf", "segoeuib.ttf"]:
        try:
            return ImageFont.truetype(font_name, size)
        except Exception:
            pass
    return ImageFont.load_default()

def download_screenshot_images(screenshot_urls, max_count=3):
    """Downloads up to max_count screenshots as PIL Images."""
    images = []
    for url in screenshot_urls[:max_count]:
        try:
            r = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=5)
            if r.status_code == 200 and len(r.content) > 1000:
                img = Image.open(io.BytesIO(r.content)).convert("RGB")
                images.append(img)
        except Exception as e:
            logger.warning(f"Failed to download screenshot {url}: {e}")
    return images

def create_slide_frame(base_img, hook_text, sub_text, price_text, cta_text, slide_index=1):
    """
    Renders an individual high-converting vertical 9:16 video frame.
    """
    canvas = Image.new("RGB", (WIDTH, HEIGHT), color=(15, 23, 42)) # Dark Navy
    draw = ImageDraw.Draw(canvas)

    # 1. Background blurred / tinted effect if base_img exists
    if base_img:
        bg_thumb = base_img.resize((WIDTH, HEIGHT))
        # Dim background
        bg_dim = Image.new("RGB", (WIDTH, HEIGHT), (10, 15, 30))
        canvas = Image.blend(bg_thumb, bg_dim, 0.75)
        draw = ImageDraw.Draw(canvas)

    font_badge = get_font(26)
    font_hook = get_font(34)
    font_stats = get_font(30)
    font_price = get_font(42)
    font_cta = get_font(28)

    # 2. Top Header Pill
    draw.rounded_rectangle([(40, 50), (WIDTH - 40, 115)], radius=15, fill=(225, 29, 72)) # Crimson Red
    draw.text((WIDTH // 2, 82), "🔥 BRAWL STARS | СРОЧНЫЙ СЛИВ 🔥", fill="white", font=font_badge, anchor="mm")

    # 3. Main Center Image Card
    if base_img:
        # Fit image neatly inside center box (width ~640, height ~600)
        box_w, box_h = 640, 580
        thumb = base_img.copy()
        thumb.thumbnail((box_w, box_h), Image.Resampling.LANCZOS)
        
        offset_x = (WIDTH - thumb.width) // 2
        offset_y = 150 + (box_h - thumb.height) // 2
        
        # Border
        draw.rounded_rectangle(
            [(offset_x - 6, offset_y - 6), (offset_x + thumb.width + 6, offset_y + thumb.height + 6)],
            radius=12, fill=(245, 158, 11) # Gold
        )
        canvas.paste(thumb, (offset_x, offset_y))
    else:
        # Graphic placeholder if no screenshots
        draw.rounded_rectangle([(40, 180), (WIDTH - 40, 720)], radius=20, fill=(30, 41, 59))
        draw.text((WIDTH // 2, 450), "⭐ ТОПОВЫЙ АККАУНТ ⭐", fill=(245, 158, 11), font=font_price, anchor="mm")

    # 4. Hook Banner (Middle)
    draw.rounded_rectangle([(30, 770), (WIDTH - 30, 860)], radius=15, fill=(0, 0, 0, 220))
    draw.text((WIDTH // 2, 815), hook_text, fill=(255, 230, 0), font=font_hook, anchor="mm")

    # 5. Stats / Subtitle
    if sub_text:
        draw.text((WIDTH // 2, 900), sub_text, fill="white", font=font_stats, anchor="mm")

    # 6. Price Offer Box (Bottom)
    draw.rounded_rectangle([(30, 960), (WIDTH - 30, 1070)], radius=18, fill=(16, 185, 129)) # Vibrant Green
    draw.text((WIDTH // 2, 1015), price_text, fill="white", font=font_price, anchor="mm")

    # 7. Call To Action (Bottom Footer)
    draw.rounded_rectangle([(40, 1100), (WIDTH - 40, 1210)], radius=15, fill=(30, 41, 59))
    draw.text((WIDTH // 2, 1135), cta_text, fill=(56, 189, 248), font=font_cta, anchor="mm")
    draw.text((WIDTH // 2, 1175), "🔗 Ссылка на канал в шапке профиля!", fill="white", font=get_font(22), anchor="mm")

    return np.array(canvas)

def generate_ai_video_clip(lot, seller_contact="@твой_юзернейм", output_dir="."):
    """
    Fully automated AI Montage:
    Produces a ready-to-publish MP4 vertical video (720x1280) for TikTok, Shorts, and Reels.
    Returns: file path to the generated MP4.
    """
    start_t = time.time()
    offer_id = str(lot.get("offer_id", int(time.time())))
    price = lot.get("price", 200)
    trophies = lot.get("trophies", 0)
    brawlers = lot.get("brawlers", 0)
    primes = lot.get("primes", 0)
    est_price = lot.get("est_tg_price", round(price * 2.2))
    contact = seller_contact if seller_contact.startswith("@") else f"@{seller_contact}"

    screenshots = lot.get("screenshots", [])
    images = download_screenshot_images(screenshots, max_count=3)

    img_1 = images[0] if len(images) > 0 else None
    img_2 = images[1] if len(images) > 1 else img_1
    img_3 = images[2] if len(images) > 2 else img_1

    # 3 Distinct Video Slides
    # Slide 1: The Hook & Discovery
    hook_1 = "ВЛАДЕЛЕЦ НЕ ЗНАЛ ЦЕНУ... 💀"
    sub_1 = f"🏆 {trophies:,} кубков | 👤 {brawlers} бойцов"
    price_1 = f"💵 СЛИВАЮТ ЗА {price:g} ₽!"
    cta_1 = f"👉 ЗАБИРАЙ В ТГ: {contact}"
    frame_1 = create_slide_frame(img_1, hook_1, sub_1, price_1, cta_1, slide_index=1)

    # Slide 2: Perks & Fair Valuation
    hook_2 = f"⚡ {primes} ПРАЙМОВ (11 LVL) И СКИНЫ"
    sub_2 = f"Оценка Оценщика: ~{est_price} ₽"
    price_2 = f"🔥 ОТДАЮТ ЗА {price:g} ₽"
    cta_2 = f"📩 ССЫЛКА НА ТГ: {contact}"
    frame_2 = create_slide_frame(img_2, hook_2, sub_2, price_2, cta_2, slide_index=2)

    # Slide 3: Final Urgent Call to Action
    hook_3 = "КТО ПЕРВЫЙ НАПИШЕТ — ЗАБИРАЕТ! ⚡"
    sub_3 = "🔒 Родная почта | 100% гарантия"
    price_3 = f"💵 ВСЕГО {price:g} ₽ (ВМЕСТО {est_price} ₽)"
    cta_3 = f"🚀 ПИШИ В ТГ: {contact}"
    frame_3 = create_slide_frame(img_3, hook_3, sub_3, price_3, cta_3, slide_index=3)

    out_file = os.path.join(output_dir, f"short_{offer_id}.mp4")

    # 24 FPS, ~2 seconds per slide = ~6 seconds total (ultra dynamic for TikTok retention)
    fps = 24
    frames_per_slide = 48  # 2.0 seconds

    writer = imageio.get_writer(out_file, fps=fps, codec="libx264", pixelformat="yuv420p")
    for _ in range(frames_per_slide):
        writer.append_data(frame_1)
    for _ in range(frames_per_slide):
        writer.append_data(frame_2)
    for _ in range(frames_per_slide):
        writer.append_data(frame_3)
    writer.close()

    elapsed = round(time.time() - start_t, 2)
    logger.info(f"AI Video generated: {out_file} in {elapsed}s, size: {os.path.getsize(out_file)} bytes")
    return out_file
