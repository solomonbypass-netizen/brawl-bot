import os
import io
import re
import time
import shutil
import logging
import subprocess
import requests
from PIL import Image, ImageDraw, ImageFont

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
    return re.sub(r'[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50]', '', str(text)).strip()

def get_font(size):
    """Safely loads cross-platform bold/regular fonts with fallback."""
    for font_name in ["impact.ttf", "arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf", "calibrib.ttf", "segoeuib.ttf"]:
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

def create_slide_pil(base_img, headline, sub_text, price_text, cta_text):
    """
    Renders an individual high-converting vertical 9:16 frame as a PIL Image.
    Uses bold gaming typography with thick outlines (stroke) and zero missing glyphs.
    """
    canvas = Image.new("RGB", (WIDTH, HEIGHT), color=(15, 23, 42)) # Dark Navy
    draw = ImageDraw.Draw(canvas)

    # 1. Background blurred / tinted effect
    if base_img:
        bg_thumb = base_img.resize((WIDTH, HEIGHT))
        bg_dim = Image.new("RGB", (WIDTH, HEIGHT), (10, 15, 30))
        canvas = Image.blend(bg_thumb, bg_dim, 0.75)
        draw = ImageDraw.Draw(canvas)

    font_badge = get_font(26)
    font_hook = get_font(34)
    font_stats = get_font(30)
    font_price = get_font(44)
    font_cta = get_font(28)

    # 2. Top Header Pill
    draw.rounded_rectangle([(40, 45), (WIDTH - 40, 115)], radius=15, fill=(225, 29, 72)) # Crimson Red
    draw.text(
        (WIDTH // 2, 80), 
        "BRAWL STARS | СРОЧНЫЙ СЛИВ", 
        fill="white", 
        font=font_badge, 
        anchor="mm",
        stroke_width=2,
        stroke_fill="black"
    )

    # 3. Main Center Image Card
    if base_img:
        box_w, box_h = 650, 580
        thumb = base_img.copy()
        thumb.thumbnail((box_w, box_h), Image.Resampling.LANCZOS)
        
        offset_x = (WIDTH - thumb.width) // 2
        offset_y = 145 + (box_h - thumb.height) // 2
        
        # Gold neon border
        draw.rounded_rectangle(
            [(offset_x - 6, offset_y - 6), (offset_x + thumb.width + 6, offset_y + thumb.height + 6)],
            radius=12, fill=(245, 158, 11)
        )
        canvas.paste(thumb, (offset_x, offset_y))
    else:
        draw.rounded_rectangle([(40, 180), (WIDTH - 40, 720)], radius=20, fill=(30, 41, 59))
        draw.text((WIDTH // 2, 450), "ТОПОВЫЙ АККАУНТ", fill=(245, 158, 11), font=font_price, anchor="mm")

    # 4. Hook Banner (Middle) - No square glyphs, bold stroke
    clean_headline = strip_emojis(headline)
    draw.rounded_rectangle([(30, 765), (WIDTH - 30, 855)], radius=15, fill=(0, 0, 0))
    draw.text(
        (WIDTH // 2, 810), 
        clean_headline, 
        fill=(255, 230, 0), 
        font=font_hook, 
        anchor="mm",
        stroke_width=3,
        stroke_fill="black"
    )

    # 5. Stats / Subtitle
    clean_sub = strip_emojis(sub_text)
    if clean_sub:
        draw.text(
            (WIDTH // 2, 895), 
            clean_sub, 
            fill="white", 
            font=font_stats, 
            anchor="mm",
            stroke_width=2,
            stroke_fill="black"
        )

    # 6. Price Offer Box (Bottom) - Rounded rubles
    clean_price = strip_emojis(price_text)
    draw.rounded_rectangle([(30, 950), (WIDTH - 30, 1060)], radius=18, fill=(16, 185, 129)) # Vibrant Green
    draw.text(
        (WIDTH // 2, 1005), 
        clean_price, 
        fill="white", 
        font=font_price, 
        anchor="mm",
        stroke_width=3,
        stroke_fill="black"
    )

    # 7. Call To Action (Bottom Footer)
    clean_cta = strip_emojis(cta_text)
    draw.rounded_rectangle([(40, 1090), (WIDTH - 40, 1205)], radius=15, fill=(30, 41, 59))
    draw.text((WIDTH // 2, 1130), clean_cta, fill=(56, 189, 248), font=font_cta, anchor="mm")
    draw.text((WIDTH // 2, 1170), "Ссылка на канал в шапке профиля!", fill="white", font=get_font(22), anchor="mm")

    return canvas

def generate_ai_video_clip(lot, seller_contact="@твой_юзернейм", output_dir="."):
    """
    Next-Gen AI Video Factory:
      1. Generates viral storyline (drama/hook).
      2. Synthesizes energetic Russian AI Voiceover (ru-RU-DmitryNeural).
      3. Renders 3 dynamic 9:16 vertical motion slides.
      4. Merges Video + Voiceover into high-impact MP4.
    """
    start_t = time.time()
    offer_id = str(lot.get("offer_id", int(time.time())))
    story = craft_viral_story(lot, seller_contact=seller_contact)

    price = story["price"]
    est_price = story["est_price"]
    contact = story["contact"]
    trophies = lot.get("trophies", 0)
    brawlers = lot.get("brawlers", 0)
    primes = lot.get("primes", 0)

    screenshots = lot.get("screenshots", [])
    images = download_screenshot_images(screenshots, max_count=3)

    img_1 = images[0] if len(images) > 0 else None
    img_2 = images[1] if len(images) > 1 else img_1
    img_3 = images[2] if len(images) > 2 else img_1

    # Slide 1: Drama hook & Discovery
    slide_1 = create_slide_pil(
        img_1,
        headline=story["hook_headline"],
        sub_text=f"{trophies:,} кубков | {brawlers} бойцов",
        price_text=f"СЛИВАЮТ ЗА {price} РУБЛЕЙ!",
        cta_text=f"ЗАБИРАЙ В ТГ: {contact}"
    )

    # Slide 2: Proof & Valuation
    slide_2 = create_slide_pil(
        img_2,
        headline=f"{primes} ПРАЙМОВ 11 УРОВНЯ",
        sub_text=story["sub_text_2"],
        price_text=f"ОЦЕНКА ЭКСПЕРТА: ~{est_price} РУБ.",
        cta_text=f"ССЫЛКА В ШАПКЕ: {contact}"
    )

    # Slide 3: Urgent Call to action
    slide_3 = create_slide_pil(
        img_3,
        headline="КТО ПЕРВЫЙ НАПИШЕТ - ЗАБИРАЕТ!",
        sub_text="Родная почта | 100% гарантия",
        price_text=f"ВСЕГО {price} РУБЛЕЙ!",
        cta_text=f"ПИШИ В ТГ: {contact}"
    )

    s1_path = os.path.join(output_dir, f"tmp_s1_{offer_id}.jpg")
    s2_path = os.path.join(output_dir, f"tmp_s2_{offer_id}.jpg")
    s3_path = os.path.join(output_dir, f"tmp_s3_{offer_id}.jpg")
    raw_video = os.path.join(output_dir, f"raw_{offer_id}.mp4")
    voice_file = os.path.join(output_dir, f"voice_{offer_id}.mp3")
    final_output = os.path.join(output_dir, f"short_{offer_id}.mp4")
    out_gif = os.path.join(output_dir, f"short_{offer_id}.gif")

    slide_1.save(s1_path, format="JPEG", quality=85)
    slide_2.save(s2_path, format="JPEG", quality=85)
    slide_3.save(s3_path, format="JPEG", quality=85)

    # Step 1: Synthesize Russian AI Voiceover
    has_voice = generate_voiceover_audio(story["voice_script"], voice_file)

    # Step 2: Render Slides Video via FFmpeg
    ffmpeg_exe = shutil.which("ffmpeg")
    if not ffmpeg_exe:
        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            ffmpeg_exe = None

    video_ready = False
    if ffmpeg_exe:
        try:
            # Video slides duration adjusted to voiceover (~2.8s per slide = ~8.4s)
            cmd_v = [
                ffmpeg_exe, "-y",
                "-loop", "1", "-t", "2.8", "-i", s1_path,
                "-loop", "1", "-t", "2.8", "-i", s2_path,
                "-loop", "1", "-t", "3.0", "-i", s3_path,
                "-filter_complex", "[0:v][1:v][2:v]concat=n=3:v=1:a=0[outv]",
                "-map", "[outv]",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast",
                raw_video
            ]
            subprocess.run(cmd_v, capture_output=True, timeout=8)

            # Step 3: Merge Voiceover with Video
            if os.path.exists(raw_video) and os.path.getsize(raw_video) > 1000:
                if has_voice and os.path.exists(voice_file):
                    cmd_merge = [
                        ffmpeg_exe, "-y",
                        "-i", raw_video,
                        "-i", voice_file,
                        "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "128k",
                        "-shortest",
                        final_output
                    ]
                    res = subprocess.run(cmd_merge, capture_output=True, timeout=8)
                    if res.returncode == 0 and os.path.exists(final_output):
                        video_ready = True
                else:
                    # Voiceover unavailable, return raw video
                    shutil.move(raw_video, final_output)
                    video_ready = True
        except Exception as e:
            logger.warning(f"FFmpeg pipeline exception: {e}")

    # Fallback to Pillow if FFmpeg failed
    chosen_file = final_output
    if not video_ready:
        logger.info("Using Pillow animation fallback...")
        slide_1.save(
            out_gif,
            save_all=True,
            append_images=[slide_2, slide_3],
            duration=2400,
            loop=0
        )
        chosen_file = out_gif

    # Cleanup temporary assets
    for p in [s1_path, s2_path, s3_path, raw_video, voice_file]:
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass

    elapsed = round(time.time() - start_t, 2)
    logger.info(f"AI Story Video completed in {elapsed}s: {chosen_file}")
    return chosen_file
