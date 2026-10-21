import re
import io
import logging
import urllib.parse
from PIL import Image, ImageEnhance, ImageOps
import numpy as np

logger = logging.getLogger("OcrExtractor")

_ocr_engine = None

def get_ocr():
    global _ocr_engine
    if _ocr_engine is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
            _ocr_engine = RapidOCR()
            logger.info("RapidOCR engine initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize RapidOCR: {e}")
            _ocr_engine = False
    return _ocr_engine

# Brawl Stars tag regex: starts with #, characters 0289PYLQGRJCUV, length 4-12
TAG_REGEX = re.compile(r"#[0289PYLQGRJCUVa-zA-Z]{4,12}")
# Valid Brawl Stars tag characters
BS_VALID_CHARS = set("0289PYLQGRJCUV")

def preprocess_for_tag(img):
    """
    Upscales and contrast-enhances an image region to make small in-game tags legible.
    """
    w, h = img.size
    up = img.resize((w * 3, h * 3), Image.LANCZOS)
    enhancer = ImageEnhance.Contrast(up)
    return enhancer.enhance(2.0)

def extract_brawl_meta_from_image(image_bytes_or_path):
    """
    Performs deep OCR scanning on screenshot:
    1. Scans full image
    2. Scans zoomed top-left quadrant (where player profile card and tag # reside in Brawl Stars)
    3. Extracts: player_tag, nickname, trophies, clean ocr_text
    """
    engine = get_ocr()
    if not engine:
        return None, None, None, ""

    try:
        if isinstance(image_bytes_or_path, (bytes, bytearray)):
            img = Image.open(io.BytesIO(image_bytes_or_path))
        else:
            img = Image.open(image_bytes_or_path)
    except Exception as e:
        logger.warning(f"Error opening image for OCR: {e}")
        return None, None, None, ""

    w, h = img.size

    # 1. Full Image Scan
    results = []
    try:
        res_full, _ = engine(np.array(img))
        if res_full:
            results.extend(res_full)
    except Exception as e:
        logger.warning(f"Full OCR pass error: {e}")

    # 2. Targeted Scan: Top-Left Profile Area (Avatar + Tag + Nickname)
    try:
        # Top-left quadrant in Brawl Stars profile screen
        crop_profile = img.crop((0, 0, int(w * 0.55), int(h * 0.45)))
        enhanced_crop = preprocess_for_tag(crop_profile)
        res_crop, _ = engine(np.array(enhanced_crop))
        if res_crop:
            results.extend(res_crop)
    except Exception as e:
        logger.warning(f"Targeted profile OCR pass error: {e}")

    detected_tag = None
    detected_nick = None
    detected_trophies = None
    all_texts = []

    for item in results:
        text = str(item[1]).strip()
        all_texts.append(text)

        # Direct # tag check
        if "#" in text:
            m = TAG_REGEX.search(text)
            if m:
                clean = m.group(0).upper()
                if len(clean) >= 5:
                    detected_tag = clean

        # Also check if text has tag-like token without #
        tokens = text.split()
        for tok in tokens:
            tok_clean = re.sub(r"[^A-Za-z0-9]", "", tok).upper()
            if 7 <= len(tok_clean) <= 10:
                bs_match_ratio = sum(1 for c in tok_clean if c in BS_VALID_CHARS) / len(tok_clean)
                if bs_match_ratio >= 0.85 and not detected_tag:
                    detected_tag = f"#{tok_clean}"

        # Trophy extraction
        troph_match = re.search(r"\b(\d{4,5})\b", text.replace(" ", "").replace(",", ""))
        if troph_match and not detected_trophies:
            val = int(troph_match.group(1))
            if 5000 <= val <= 95000:
                detected_trophies = val

    # Candidate Nickname detection
    for text in all_texts:
        cleaned_nick = text.strip()
        if re.match(r"^[a-zA-Zа-яА-Я0-9_♦★]{3,15}$", cleaned_nick):
            low = cleaned_nick.lower()
            if not any(k in low for k in ["brawl", "pass", "tier", "lvl", "болев", "бойц", "куб", "not", "club", "god", "snipe"]):
                if not detected_nick:
                    detected_nick = cleaned_nick

    full_ocr = " ".join(all_texts)
    return detected_tag, detected_nick, detected_trophies, full_ocr
