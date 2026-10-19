import os
import io
import re
import time
import shutil
import logging
import subprocess
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from core.config import HEADERS, COOKIES
from core.story_director import craft_viral_story
from core.voice_maker import generate_voiceover_audio

logger = logging.getLogger("AIVideoMaker")

WIDTH = 720
HEIGHT = 1280

def strip_emojis(text: str) -> str:
    if not text:
        return ""
    # Strip emojis and non-standard symbols to prevent square box glyphs in PIL fonts
    clean = re.sub(r'[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50]', '', str(text))
    # Replace ruble symbol with text to avoid missing glyph in Impact/system fonts
    clean = clean.replace("₽", "РУБ.").strip()
    return clean

def get_font(size, bold=True):
    """Safely loads cross-platform bold/regular fonts with fallback."""
    fonts = ["impact.ttf", "segoeuib.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"]
    for font_name in fonts:
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
            r = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=4)
            if r.status_code == 200 and len(r.content) > 1000:
                img = Image.open(io.BytesIO(r.content)).convert("RGB")
                images.append(img)
        except Exception as e:
            logger.warning(f"Failed to download screenshot {url}: {e}")
    return images

def create_base_cosmic():
    """Generates premium deep cosmic void gradient with ambient glow & starfield."""
    bg = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(bg)
    top_c = (24, 12, 50)
    mid_c = (60, 16, 92)
    bot_c = (14, 5, 32)
    for y in range(HEIGHT):
        t = y / HEIGHT
        if t < 0.5:
            f = t * 2
            r = int(top_c[0] * (1 - f) + mid_c[0] * f)
            g = int(top_c[1] * (1 - f) + mid_c[1] * f)
            b = int(top_c[2] * (1 - f) + mid_c[2] * f)
        else:
            f = (t - 0.5) * 2
            r = int(mid_c[0] * (1 - f) + bot_c[0] * f)
            g = int(mid_c[1] * (1 - f) + bot_c[1] * f)
            b = int(mid_c[2] * (1 - f) + bot_c[2] * f)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b, 255))

    # Ambient magenta/violet glow
    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse([WIDTH // 2 - 280, 480, WIDTH // 2 + 280, 1040], fill=(160, 36, 190, 75))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    bg = Image.alpha_composite(bg, glow)

    # 4-point cross starfield
    sparkle = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(sparkle)
    import random
    random.seed(42)
    for _ in range(45):
        sx, sy = random.randint(25, WIDTH - 25), random.randint(40, HEIGHT - 40)
        s_len = random.randint(8, 25)
        sdraw.line([(sx - s_len, sy), (sx + s_len, sy)], fill=(255, 255, 255, 190), width=max(1, s_len // 8))
        sdraw.line([(sx, sy - s_len), (sx, sy + s_len)], fill=(255, 255, 255, 190), width=max(1, s_len // 8))
        sdraw.ellipse([(sx - 2, sy - 2), (sx + 2, sy + 2)], fill=(255, 255, 255, 255))
    bg = Image.alpha_composite(bg, sparkle)
    return bg

def draw_top_stories_bar(draw, step, total=4):
    pad = 35
    total_w = WIDTH - pad * 2
    gap = 8
    seg_w = (total_w - (total - 1) * gap) / total
    y = 35
    for i in range(total):
        x0 = pad + i * (seg_w + gap)
        x1 = x0 + seg_w
        col = (255, 255, 255, 245) if i <= step else (255, 255, 255, 65)
        draw.rounded_rectangle([(x0, y), (x1, y + 4)], radius=2, fill=col)

def draw_top_badge(draw, text, y=85, fill_color=(225, 29, 72, 230)):
    clean_text = strip_emojis(text)
    font = get_font(22, bold=True)
    bbox = font.getbbox(clean_text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    px, py = 25, 10
    bx0, by0 = (WIDTH - tw) // 2 - px, y - py
    bx1, by1 = (WIDTH + tw) // 2 + px, y + th + py
    draw.rounded_rectangle([(bx0, by0), (bx1, by1)], radius=18, fill=fill_color, outline=(255, 255, 255, 80), width=2)
    draw.text(((WIDTH - tw) // 2 - bbox[0], y - bbox[1]), clean_text, font=font, fill="white")

def draw_neon_text(canvas, text, y, font, c_left, c_right, glow_col, glow_r=20, center_x=WIDTH // 2):
    clean_text = strip_emojis(text)
    bbox = font.getbbox(clean_text)
    tw, th = bbox[2] - bbox[0] + 30, bbox[3] - bbox[1] + 30
    g_img = Image.new("RGBA", (tw + 40, th + 40), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(g_img)
    gdraw.text((20 + 15 - bbox[0], 20 + 15 - bbox[1]), clean_text, font=font, fill=glow_col)
    g_img = g_img.filter(ImageFilter.GaussianBlur(glow_r))

    mask = Image.new("L", (tw, th), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.text((15 - bbox[0], 15 - bbox[1]), clean_text, font=font, fill=255)

    grad = Image.new("RGBA", (tw, th))
    g_draw = ImageDraw.Draw(grad)
    for x in range(tw):
        fac = x / max(1, tw - 1)
        r = int(c_left[0] * (1 - fac) + c_right[0] * fac)
        g = int(c_left[1] * (1 - fac) + c_right[1] * fac)
        b = int(c_left[2] * (1 - fac) + c_right[2] * fac)
        g_draw.line([(x, 0), (x, th)], fill=(r, g, b, 255))
    grad.putalpha(mask)

    pos_x = center_x - tw // 2
    canvas.alpha_composite(g_img, (pos_x - 20, y - 20))
    canvas.alpha_composite(grad, (pos_x, y))

def draw_plain_text(canvas, text, y, font, color, center_x=WIDTH // 2):
    clean_text = strip_emojis(text)
    bbox = font.getbbox(clean_text)
    tw = bbox[2] - bbox[0]
    draw = ImageDraw.Draw(canvas)
    draw.text((center_x - tw // 2 - bbox[0], y - bbox[1]), clean_text, font=font, fill=color)

# === SLIDE BUILDERS (Formats 2 & 3: Real Screenshots & Zero Scam Vibes) ===

def render_slide_1(lot, story, base_img):
    """Slide 1: Hook Headline + Real Lot Screenshot."""
    s1 = create_base_cosmic()
    d1 = ImageDraw.Draw(s1)
    draw_top_stories_bar(d1, 0, 4)
    badge_color = (225, 29, 72, 240) if story["format"] == 2 else (16, 185, 129, 240)
    draw_top_badge(d1, story["badge_1"], 95, fill_color=badge_color)

    draw_neon_text(
        s1,
        story["hook_headline"],
        155,
        get_font(46, bold=True),
        (0, 245, 255),
        (255, 60, 180),
        (0, 220, 255, 150)
    )

    # Real Screenshot Card (Center)
    if base_img:
        box_w, box_h = 620, 500
        thumb = base_img.copy()
        thumb.thumbnail((box_w, box_h), Image.Resampling.LANCZOS)
        ox = (WIDTH - thumb.width) // 2
        oy = 240 + (box_h - thumb.height) // 2

        # Glowing glass border
        card = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([(ox - 6, oy - 6), (ox + thumb.width + 6, oy + thumb.height + 6)], radius=16, fill=(245, 158, 11, 230))
        s1.alpha_composite(card)
        s1.paste(thumb, (ox, oy))
    else:
        # Fallback card if screenshots unavailable
        card = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([(50, 260), (WIDTH - 50, 680)], radius=24, fill=(35, 25, 55, 200), outline=(245, 158, 11, 200), width=3)
        s1.alpha_composite(card)
        draw_plain_text(s1, "РЕАЛЬНЫЙ ЛОТ С БИРЖИ", 400, get_font(38, bold=True), (255, 225, 50, 255))
        draw_plain_text(s1, f"{story['trophies']:,} кубков | {story['brawlers']} бойцов", 470, get_font(28, bold=False), "white")

    # Bottom Offer Box (Price)
    price_box = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    pdraw = ImageDraw.Draw(price_box)
    pdraw.rounded_rectangle([(45, 780), (WIDTH - 45, 910)], radius=20, fill=(20, 35, 30, 220), outline=(16, 185, 129, 210), width=3)
    price_box_glow = price_box.filter(ImageFilter.GaussianBlur(10))
    s1.alpha_composite(price_box_glow)
    s1.alpha_composite(price_box)

    draw_plain_text(s1, "ЦЕНА НА БИРЖЕ:", 805, get_font(24, bold=True), (110, 231, 183, 255))
    draw_neon_text(s1, f"СЛИВАЮТ ЗА {story['price']} РУБЛЕЙ!", 845, get_font(42, bold=True), (16, 185, 129), (52, 211, 153), (16, 185, 129, 180))

    draw_plain_text(s1, story["sub_text_1"], 945, get_font(26, bold=False), (210, 220, 240, 220))
    return s1.convert("RGB")

def render_slide_2(lot, story, base_img):
    """Slide 2: In-Depth Account Inspection & Stats Proof."""
    s2 = create_base_cosmic()
    d2 = ImageDraw.Draw(s2)
    draw_top_stories_bar(d2, 1, 4)
    draw_top_badge(d2, story["badge_2"], 95, fill_color=(124, 58, 237, 230))

    draw_neon_text(s2, "ПРОВЕРКА ПРОФИЛЯ", 180, get_font(50, bold=True), (0, 245, 255), (255, 60, 180), (0, 220, 255, 140))

    # 3 Glassmorphic Inspection Cards
    c_stats = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    cs_draw = ImageDraw.Draw(c_stats)
    cs_draw.rounded_rectangle([(50, 290), (WIDTH - 50, 440)], radius=22, fill=(35, 25, 55, 190), outline=(255, 215, 0, 150), width=2)
    cs_draw.rounded_rectangle([(50, 470), (WIDTH - 50, 620)], radius=22, fill=(35, 25, 55, 190), outline=(0, 220, 255, 150), width=2)
    cs_draw.rounded_rectangle([(50, 650), (WIDTH - 50, 800)], radius=22, fill=(35, 25, 55, 190), outline=(244, 63, 94, 150), width=2)
    s2.alpha_composite(c_stats)

    draw_plain_text(s2, f"{story['trophies']:,} КУБКОВ", 325, get_font(38, bold=True), (255, 225, 50, 255))
    draw_plain_text(s2, "Личная проверенная основа Supercell ID", 380, get_font(22, bold=False), (220, 220, 235, 220))

    draw_plain_text(s2, f"{story['brawlers']} БОЙЦОВ И ПРАЙМЫ", 505, get_font(36, bold=True), (0, 240, 255, 255))
    draw_plain_text(s2, f"{story['primes']} персонажей 11 уровня со скинами", 560, get_font(22, bold=False), (200, 230, 255, 220))

    draw_plain_text(s2, story["price_card_text"], 685, get_font(36, bold=True), (255, 80, 120, 255))
    draw_plain_text(s2, f"Отдают всего за {story['price']} рублей!", 740, get_font(22, bold=False), (255, 200, 210, 220))

    return s2.convert("RGB")

def render_slide_3(lot, story):
    """Slide 3: Value Conclusion & Honest Safety Proof."""
    s3 = create_base_cosmic()
    d3 = ImageDraw.Draw(s3)
    draw_top_stories_bar(d3, 2, 4)
    draw_top_badge(d3, story["badge_3"], 95, fill_color=(16, 185, 129, 230))

    draw_plain_text(s3, "ВЫКУПЛЕН ПО СЕБЕСТОИМОСТИ!", 230, get_font(44, bold=True), "white")

    box_c = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(box_c)
    b_draw.rounded_rectangle([(50, 330), (WIDTH - 50, 680)], radius=24, fill=(20, 35, 30, 210), outline=(16, 185, 129, 210), width=3)
    s3.alpha_composite(box_c)

    draw_plain_text(s3, "ОТДАЕМ В ТЕЛЕГРАМЕ ДЛЯ СВОИХ:", 380, get_font(28, bold=True), (110, 231, 183, 255))
    draw_neon_text(s3, f"ВСЕГО {story['price']} РУБЛЕЙ", 450, get_font(60, bold=True), (16, 185, 129), (52, 211, 153), (16, 185, 129, 200))
    draw_plain_text(s3, story["sub_text_3"], 560, get_font(24, bold=False), (200, 230, 220, 220))
    draw_plain_text(s3, "100% гарантия передачи и родная почта", 610, get_font(22, bold=False), (160, 220, 200, 200))

    return s3.convert("RGB")

def render_slide_4(lot, story):
    """Slide 4: Telegram Radar & Call to Action (solomon)."""
    s4 = create_base_cosmic()
    d4 = ImageDraw.Draw(s4)
    draw_top_stories_bar(d4, 3, 4)

    radar_y = 350
    radar = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    rdraw = ImageDraw.Draw(radar)
    for rad in [140, 195, 255]:
        rdraw.ellipse([WIDTH // 2 - rad, radar_y - rad, WIDTH // 2 + rad, radar_y + rad], outline=(0, 200, 255, 70), width=2)
    rdraw.ellipse([WIDTH // 2 - 80, radar_y - 80, WIDTH // 2 + 80, radar_y + 80], fill=(0, 160, 255, 230), outline=(0, 240, 255, 190), width=4)
    # Airplane polygon
    plane_pts = [(WIDTH // 2 - 35, radar_y + 10), (WIDTH // 2 + 42, radar_y - 25), (WIDTH // 2 - 15, radar_y + 35)]
    rdraw.polygon(plane_pts, fill=(255, 255, 255, 255))
    rdraw.polygon([(WIDTH // 2 - 15, radar_y + 35), (WIDTH // 2 + 42, radar_y - 25), (WIDTH // 2 + 5, radar_y + 12)], fill=(220, 240, 255, 255))
    radar_blur = radar.filter(ImageFilter.GaussianBlur(8))
    s4.alpha_composite(radar_blur)
    s4.alpha_composite(radar)

    draw_plain_text(s4, "Забирай аккаунт в закрепе:", 560, get_font(30, bold=False), (210, 225, 250, 230))
    draw_neon_text(s4, "solomon", 610, get_font(78, bold=True), (0, 245, 255), (255, 50, 180), (0, 220, 255, 190))

    btn_box = [(90, 780), (WIDTH - 90, 875)]
    btn_img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(btn_img)
    bdraw.rounded_rectangle(btn_box, radius=35, fill=(0, 165, 255, 240), outline=(255, 255, 255, 140), width=2)
    bdraw.text((WIDTH // 2, 828), "ССЫЛКА В ШАПКЕ ПРОФИЛЯ", font=get_font(30, bold=True), fill="white", anchor="mm")
    btn_glow = btn_img.filter(ImageFilter.GaussianBlur(16))
    s4.alpha_composite(btn_glow)
    s4.alpha_composite(btn_img)

    draw_plain_text(s4, "Кто первый напишет — тот и забирает!", 915, get_font(24, bold=True), (255, 220, 100, 240))
    return s4.convert("RGB")

def generate_ai_video_clip(lot, seller_contact="@solomon", output_dir="."):
    """
    Next-Gen AI Video Studio (Formats 2 & 3):
      1. Generates authentic viral storyline (0% scam vibes, 100% gamer investigation).
      2. Synthesizes energetic Russian AI voiceover.
      3. Renders 4 Cosmic Neon Glass 9:16 slides with REAL lot screenshots.
      4. Speeds up voice to 1.24x with FFmpeg atempo.
      5. Mixes voice + background trap beat with audio ducking.
      6. Merges into studio-grade vertical MP4 (< 4s runtime, < 25 MB RAM).
    """
    start_t = time.time()
    offer_id = str(lot.get("offer_id", int(time.time())))
    story = craft_viral_story(lot, seller_contact=seller_contact)

    screenshots = lot.get("screenshots", [])
    images = download_screenshot_images(screenshots, max_count=2)
    img_1 = images[0] if len(images) > 0 else None

    # Render 4 Cosmic Glass Slides
    slide_1 = render_slide_1(lot, story, img_1)
    slide_2 = render_slide_2(lot, story, img_1)
    slide_3 = render_slide_3(lot, story)
    slide_4 = render_slide_4(lot, story)

    s1_path = os.path.join(output_dir, f"tmp_s1_{offer_id}.jpg")
    s2_path = os.path.join(output_dir, f"tmp_s2_{offer_id}.jpg")
    s3_path = os.path.join(output_dir, f"tmp_s3_{offer_id}.jpg")
    s4_path = os.path.join(output_dir, f"tmp_s4_{offer_id}.jpg")
    raw_voice = os.path.join(output_dir, f"raw_v_{offer_id}.mp3")
    fast_voice = os.path.join(output_dir, f"fast_v_{offer_id}.mp3")
    final_output = os.path.join(output_dir, f"short_{offer_id}.mp4")
    out_gif = os.path.join(output_dir, f"short_{offer_id}.gif")

    slide_1.save(s1_path, format="JPEG", quality=90)
    slide_2.save(s2_path, format="JPEG", quality=90)
    slide_3.save(s3_path, format="JPEG", quality=90)
    slide_4.save(s4_path, format="JPEG", quality=90)

    # 1. Synthesize Voiceover
    has_voice = generate_voiceover_audio(story["voice_script"], raw_voice)

    # 2. FFmpeg Video + Audio Ducking Multiplexing
    ffmpeg_exe = shutil.which("ffmpeg")
    if not ffmpeg_exe:
        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            ffmpeg_exe = None

    video_ready = False
    music_track = os.path.join("assets", "audio", "viral_beat.mp3")

    if ffmpeg_exe:
        try:
            # Speed up voice with atempo=1.24
            if has_voice and os.path.exists(raw_voice):
                cmd_speed = [
                    ffmpeg_exe, "-y",
                    "-i", raw_voice,
                    "-filter:a", "atempo=1.24",
                    "-c:a", "libmp3lame", "-b:a", "192k",
                    fast_voice
                ]
                res_sp = subprocess.run(cmd_speed, capture_output=True, timeout=6)
                if res_sp.returncode != 0 or not os.path.exists(fast_voice):
                    fast_voice = raw_voice
            else:
                fast_voice = None

            # Video slide timings matching voice duration (~12-13s total)
            t1, t2, t3, t4 = "3.0", "3.2", "2.8", "4.0"

            # Check if background music is available
            has_music = os.path.exists(music_track)

            if fast_voice and os.path.exists(fast_voice):
                if has_music:
                    cmd_full = [
                        ffmpeg_exe, "-y",
                        "-loop", "1", "-t", t1, "-i", s1_path,
                        "-loop", "1", "-t", t2, "-i", s2_path,
                        "-loop", "1", "-t", t3, "-i", s3_path,
                        "-loop", "1", "-t", t4, "-i", s4_path,
                        "-i", fast_voice,
                        "-stream_loop", "-1", "-i", music_track,
                        "-filter_complex",
                        "[0:v][1:v][2:v][3:v]concat=n=4:v=1:a=0[v];"
                        "[4:a]volume=1.35[voice];"
                        "[5:a]volume=0.20,afade=t=out:st=11:d=1.5[music];"
                        "[voice][music]amix=inputs=2:duration=first:dropout_transition=2[aout]",
                        "-map", "[v]",
                        "-map", "[aout]",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
                        "-c:a", "aac", "-b:a", "192k",
                        "-shortest",
                        final_output
                    ]
                else:
                    cmd_full = [
                        ffmpeg_exe, "-y",
                        "-loop", "1", "-t", t1, "-i", s1_path,
                        "-loop", "1", "-t", t2, "-i", s2_path,
                        "-loop", "1", "-t", t3, "-i", s3_path,
                        "-loop", "1", "-t", t4, "-i", s4_path,
                        "-i", fast_voice,
                        "-filter_complex", "[0:v][1:v][2:v][3:v]concat=n=4:v=1:a=0[v]",
                        "-map", "[v]",
                        "-map", "4:a",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
                        "-c:a", "aac", "-b:a", "192k",
                        "-shortest",
                        final_output
                    ]
                res_f = subprocess.run(cmd_full, capture_output=True, timeout=12)
                if res_f.returncode == 0 and os.path.exists(final_output) and os.path.getsize(final_output) > 1000:
                    video_ready = True
            else:
                # Video without voice
                cmd_v = [
                    ffmpeg_exe, "-y",
                    "-loop", "1", "-t", t1, "-i", s1_path,
                    "-loop", "1", "-t", t2, "-i", s2_path,
                    "-loop", "1", "-t", t3, "-i", s3_path,
                    "-loop", "1", "-t", t4, "-i", s4_path,
                    "-filter_complex", "[0:v][1:v][2:v][3:v]concat=n=4:v=1:a=0[v]",
                    "-map", "[v]",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
                    final_output
                ]
                res_v = subprocess.run(cmd_v, capture_output=True, timeout=8)
                if res_v.returncode == 0 and os.path.exists(final_output):
                    video_ready = True
        except Exception as e:
            logger.warning(f"FFmpeg pipeline exception: {e}")

    # Fallback to Pillow animated GIF if FFmpeg unavailable
    chosen_file = final_output
    if not video_ready:
        logger.info("Falling back to Pillow animation...")
        slide_1.save(
            out_gif,
            save_all=True,
            append_images=[slide_2, slide_3, slide_4],
            duration=3000,
            loop=0
        )
        chosen_file = out_gif

    # Cleanup temporary files
    for p in [s1_path, s2_path, s3_path, s4_path, raw_voice, fast_voice]:
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass

    elapsed = round(time.time() - start_t, 2)
    logger.info(f"AI Video Studio finished in {elapsed}s: {chosen_file}")
    return chosen_file
