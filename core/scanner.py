import os
import re
import json
import logging
import threading
import requests
from bs4 import BeautifulSoup
from core.config import FUNPAY_URL, HEADERS, COOKIES, SEEN_FILE, MAX_SEEN_CACHE
from core.analyzer import (
    PATTERN_STATS, SPAM_KEYWORDS, extract_exact_rub_price, analyze_lot_liquidity
)

logger = logging.getLogger("FunPayScanner")
cache_lock = threading.Lock()

def load_seen_offers():
    with cache_lock:
        if os.path.exists(SEEN_FILE):
            try:
                with open(SEEN_FILE, "r", encoding="utf-8") as f:
                    return set(json.load(f))
            except Exception as e:
                logger.error(f"Error loading seen cache: {e}")
                return set()
        return set()

def save_seen_offers(seen_set):
    with cache_lock:
        try:
            items = list(seen_set)[-MAX_SEEN_CACHE:]
            with open(SEEN_FILE, "w", encoding="utf-8") as f:
                json.dump(items, f)
        except Exception as e:
            logger.error(f"Error saving seen cache: {e}")

def fetch_lots(min_price=100, max_price=450):
    """
    Fetches and parses FunPay lots with strict validation and liquidity scoring.
    """
    try:
        resp = requests.get(FUNPAY_URL, headers=HEADERS, cookies=COOKIES, timeout=15)
        if resp.status_code != 200:
            logger.warning(f"FunPay HTTP returned status {resp.status_code}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        lot_elements = soup.find_all("a", class_="tc-item")

        parsed_lots = []
        for lot in lot_elements:
            href = lot.get("href", "")
            if not href:
                continue
            if not href.startswith("http"):
                href = "https://funpay.com" + href

            offer_id_match = re.search(r"id=(\d+)", href)
            offer_id = offer_id_match.group(1) if offer_id_match else href

            desc_el = lot.find("div", class_="tc-desc-text")
            price_el = lot.find("div", class_="tc-price")
            user_el = lot.find("div", class_="media-user-name")
            rating_el = lot.find("span", class_="rating-mini-count")

            if not desc_el or not price_el:
                continue

            desc = desc_el.get_text(strip=True)
            price = extract_exact_rub_price(price_el)
            seller = user_el.get_text(strip=True) if user_el else "Неизвестен"
            reviews = int(rating_el.get_text(strip=True)) if rating_el else 0

            if price < min_price or price > max_price:
                continue

            desc_lower = desc.lower()
            if any(kw in desc_lower for kw in SPAM_KEYWORDS):
                continue

            match = PATTERN_STATS.search(desc)
            trophies = int(match.group(1)) if match else 0
            brawlers = int(match.group(2)) if match and match.group(2) else 0
            primes = int(match.group(3)) if match and match.group(3) else 0

            has_firstmail = any(k in desc_lower for k in [
                "firstmail", "родная почта", "родная", "с почтой", "отдам почту", "чистая почта"
            ])

            lot_raw = {
                "offer_id": offer_id,
                "href": href,
                "price": price,
                "trophies": trophies,
                "brawlers": brawlers,
                "primes": primes,
                "seller": seller,
                "reviews": reviews,
                "desc": desc,
                "has_firstmail": has_firstmail
            }

            is_liquid, triggers, est_tg_price, profit = analyze_lot_liquidity(lot_raw)

            if is_liquid:
                lot_raw["triggers"] = triggers
                lot_raw["est_tg_price"] = est_tg_price
                lot_raw["profit"] = profit
                parsed_lots.append(lot_raw)

        return parsed_lots
    except Exception as e:
        logger.error(f"Error in fetch_lots: {e}")
        return []
