import os
import re
import sys
import time
import json
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from bs4 import BeautifulSoup
import telebot
from telebot import types

# ---------------- CONFIGURATION ----------------
BOT_TOKEN = "8645936875:AAF3vd-v31W7GEfb3FhClr_quCDKaFSMggU"
TARGET_CHAT_ID = 6985905211
FUNPAY_URL = "https://funpay.com/lots/436/"
SEEN_FILE = "seen_offers.json"
CHECK_INTERVAL_SECONDS = 40  # Fast scan loop

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("FunPayBot")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}

COOKIES = {
    "cy": "rub"
}

# ---------------- HTTP HEALTH CHECK FOR RENDER ----------------
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"FunPay Bot is Alive and Running 24/7!")

    def log_message(self, format, *args):
        pass

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# ---------------- STORAGE ----------------
def load_seen_offers():
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_seen_offers(seen_set):
    try:
        items = list(seen_set)[-10000:]
        with open(SEEN_FILE, "w", encoding="utf-8") as f:
            json.dump(items, f)
    except Exception as e:
        logger.error(f"Error saving seen offers: {e}")

seen_offers = load_seen_offers()
bot_stats = {
    "start_time": time.time(),
    "scans_count": 0,
    "last_scan_time": "Еще не проводился",
    "alerts_sent": 0
}

# ---------------- TARGET LIQUIDITY TRIGGERS ----------------
OG_SKINS = [
    "звездная шелли", "star shelly", "шелли 2018", "2018", "2019", "корсар кольт",
    "рикошет", "вирус 8-бит", "вирус", "ведьма шелли", "оборотень леон",
    "торговец гейл", "паладин вольт", "майк портье", "хэллоуин", "олд акк"
]

SPAM_KEYWORDS = [
    "договорная", "цена в лс", "писать в лс", "в лс", "не покупать", 
    "куплю", "обмен", "тест", "витрина", "предлагайте", "предлагать", 
    "цена договор", "договор", "отзыв", "пустышка", "минус", "-гем", "отрицательн"
]

GEMS_REGEX = re.compile(r"(\d{2,4})\s*(?:гем|gem)", re.IGNORECASE)
BP_REGEX = re.compile(r"(?:бп\+|brawl\s*pass\+|бравл\s*пасс\+|куплен\s*бп)", re.IGNORECASE)
SKINS_COUNT_REGEX = re.compile(r"(\d{2,3})\s*скин", re.IGNORECASE)
PATTERN_STATS = re.compile(r"(\d+)\s*кубк\w*,\s*(\d+)\s*бравлер\w*(?:,\s*(\d+)\s*прайм\w*)?", re.IGNORECASE)

def extract_exact_rub_price(price_el):
    if not price_el:
        return 0.0
    data_s = price_el.get("data-s")
    if data_s:
        try:
            val = float(data_s)
            if val > 0:
                return round(val, 2)
        except ValueError:
            pass

    text = price_el.get_text(strip=True)
    cleaned = re.sub(r"[^\d.]", "", text.replace(" ", "").replace(",", "."))
    try:
        val = float(cleaned)
    except ValueError:
        return 0.0

    if "$" in text or "usd" in text.lower():
        return round(val * 95.0, 2)
    elif "€" in text or "eur" in text.lower():
        return round(val * 105.0, 2)

    return round(val, 2)

def analyze_lot_liquidity(lot_dict):
    """
    Evaluates real market liquidity and profit margin in Telegram resale.
    Returns: (is_liquid, triggers_list, est_tg_price, profit)
    """
    price = lot_dict["price"]
    desc_lower = lot_dict["desc"].lower()
    brawlers = lot_dict["brawlers"]
    primes = lot_dict["primes"]
    trophies = lot_dict["trophies"]

    # Filter out scam negative gems (e.g. -4554 гемов)
    if any(k in desc_lower for k in ["-гем", "минус", "отрицательн", "долг"]):
        return False, [], 0, 0

    triggers = []
    est_tg_price = 0

    # 1. OG / Exclusive Skins check
    found_og = [s for s in OG_SKINS if s in desc_lower]
    if found_og and price <= 450:
        triggers.append(f"👑 <b>OG-раритет:</b> {found_og[0].upper()}")
        est_tg_price = max(est_tg_price, 1100)

    # 2. Donat balance check (Gems / Pass)
    gems_match = GEMS_REGEX.search(desc_lower)
    if gems_match:
        gems = int(gems_match.group(1))
        # Ensure it's not negative
        if gems >= 80 and price <= 380:
            triggers.append(f"💎 <b>Баланс:</b> {gems} гемов")
            est_tg_price = max(est_tg_price, 850 + (gems * 3))

    if bool(BP_REGEX.search(desc_lower)) and price <= 420:
        triggers.append("🎟️ <b>Куплен Brawl Pass+</b>")
        est_tg_price = max(est_tg_price, 950)

    # 3. High skins count check
    skins_match = SKINS_COUNT_REGEX.search(desc_lower)
    if skins_match:
        skins_cnt = int(skins_match.group(1))
        if skins_cnt >= 70 and price <= 390:
            triggers.append(f"🎨 <b>Скин-коллекция:</b> {skins_cnt} скинов")
            est_tg_price = max(est_tg_price, 1200)

    # 4. Pure character unlock disparity (78+ brawlers at throwaway price)
    if brawlers >= 78 and price <= 380:
        triggers.append(f"👤 <b>Фулл-ростер:</b> {brawlers} бравлеров всего за {price:g}₽")
        est_tg_price = max(est_tg_price, 900)

    # 5. Heavy 11-lvl maxed powers smurf
    if primes >= 14 and price <= 380:
        triggers.append(f"⚡ <b>Готовая основа:</b> {primes} бойцов на 11 силе")
        est_tg_price = max(est_tg_price, 950)

    # 6. Overall fast flip condition: 25k+ trophies, 70+ brawlers at <= 260 RUB
    if trophies >= 25000 and brawlers >= 70 and price <= 260:
        triggers.append(f"🔥 <b>Срочный сброс:</b> 25k+ кубков за {price:g}₽")
        est_tg_price = max(est_tg_price, 750)

    if not triggers:
        return False, [], 0, 0

    # Minimum base Telegram market resale floor for a verified good account
    if est_tg_price == 0:
        est_tg_price = 700

    profit = est_tg_price - price
    # Only consider liquid if expected net profit is at least 350 RUB
    if profit >= 350 and price <= 450:
        return True, triggers, round(est_tg_price), round(profit)

    return False, [], 0, 0

def fetch_lots():
    try:
        resp = requests.get(FUNPAY_URL, headers=HEADERS, cookies=COOKIES, timeout=15)
        if resp.status_code != 200:
            logger.warning(f"FunPay returned status {resp.status_code}")
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

            # Exclude non-relevant prices (too high or 0)
            if price < 100 or price > 450:
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
        logger.error(f"Error fetching lots: {e}")
        return []

def format_gold_message(lot, is_new_alert=False):
    title = "🚨 <b>НАЙДЕН ОКУПНОЙ АККАУНТ НА FUNPAY!</b>" if is_new_alert else "💰 <b>ОКУПНОЙ ЛОТ ПОД БЫСТРЫЙ ФЛИП:</b>"
    mail_badge = "🟢 <b>Родная почта (Firstmail)</b>" if lot["has_firstmail"] else "🟡 <b>Почту уточнять у продавца</b>"
    
    triggers_text = "\n".join([f"• {t}" for t in lot["triggers"]])

    msg = (
        f"{title}\n\n"
        f"🎯 <b>ПОЧЕМУ ЭТО ОКУП:</b>\n"
        f"{triggers_text}\n\n"
        f"💵 <b>Цена на FunPay:</b> <code>{lot['price']:g} ₽</code>\n"
        f"📈 <b>Реальная продажа в ТГ:</b> ~<code>{lot['est_tg_price']} ₽</code>\n"
        f"🟢 <b>Твой чистый профит:</b> <b>+{lot['profit']} ₽</b>\n\n"
        f"🏆 <b>Кубков:</b> <b>{lot['trophies']:,}</b> | 👤 <b>Бравлеров:</b> <b>{lot['brawlers']}</b> | ⚡ <b>Праймов:</b> <b>{lot['primes']}</b>\n"
        f"👤 <b>Продавец:</b> {lot['seller']} (⭐ <b>{lot['reviews']}</b> отзывов)\n"
        f"{mail_badge}\n\n"
        f"📝 <i>{lot['desc'][:115]}...</i>"
    )
    return msg

def make_lot_keyboard(href):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="🔗 Забрать на FunPay", url=href))
    return kb

def get_main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_flip = types.KeyboardButton("🚀 Найти окупные лоты прямо сейчас")
    btn_status = types.KeyboardButton("📊 Статус мониторинга")
    kb.add(btn_flip)
    kb.add(btn_status)
    return kb

# ---------------- BOT COMMAND HANDLERS ----------------
@bot.message_handler(commands=["start", "help"])
def cmd_start(message):
    text = (
        "👋 <b>Снайпер окупных аккаунтов Brawl Stars активен!</b>\n\n"
        "<b>Критерии жесткого отбора (только реальный профит):</b>\n"
        "• Цена строго <b>100–450 ₽</b> (минимальный риск)\n"
        "• Наличие <b>OG-скинов (2018–2020)</b> или <b>запас гемов/Brawl Pass</b>\n"
        "• Или <b>78+ бравлеров / 14+ праймов</b> за копейки\n"
        "• Чистая окупаемость от <b>+350 ₽ до +1200 ₽</b> со сделки\n\n"
        "Нажимай кнопку ниже для поиска:"
    )
    bot.send_message(message.chat.id, text, reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda m: m.text and any(k in m.text.lower() for k in ["найти", "окуп", "лоты", "горяч", "флип"]))
def handle_find_deals(message):
    bot.send_message(message.chat.id, "🔍 Сканирую FunPay по триггерам ликвидности (OG-скины, баланс гемов, сброс прокачки)...")
    lots = fetch_lots()
    
    # Sort primarily by expected profit descending
    lots.sort(key=lambda x: (x["reviews"] >= 10, x["profit"]), reverse=True)

    if not lots:
        bot.send_message(message.chat.id, "Сейчас на FunPay нет лотов, проходящих фильтр окупаемости. Мониторинг ждет новые вбросы!", reply_markup=get_main_keyboard())
        return

    bot.send_message(message.chat.id, f"✅ Отобрано <b>{len(lots)}</b> реально окупных вариантов (до 450₽). Вот ТОП-3:")
    for lot in lots[:3]:
        bot.send_message(message.chat.id, format_gold_message(lot), reply_markup=make_lot_keyboard(lot["href"]))

@bot.message_handler(func=lambda m: m.text and "статус" in m.text.lower())
def handle_status(message):
    uptime_sec = int(time.time() - bot_stats["start_time"])
    hours = uptime_sec // 3600
    minutes = (uptime_sec % 3600) // 60

    text = (
        "📊 <b>СТАТУС МОНИТОРИНГА:</b>\n\n"
        f"🟢 <b>Сервер:</b> Render Cloud 24/7\n"
        f"⏱ <b>Время работы:</b> {hours} ч. {minutes} мин.\n"
        f"🔄 <b>Проведено сканов:</b> {bot_stats['scans_count']}\n"
        f"🕒 <b>Крайний скан:</b> {bot_stats['last_scan_time']}\n"
        f"🔔 <b>Отправлено новых алертов:</b> {bot_stats['alerts_sent']}\n\n"
        "🎯 <i>Фильтры: цена до 450₽, OG-скины, баланс гемов, защита от минусового баланса.</i>"
    )
    bot.send_message(message.chat.id, text, reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda m: True)
def handle_fallback(message):
    handle_find_deals(message)

# ---------------- BACKGROUND SCANNER THREAD ----------------
def background_scanner_loop():
    global seen_offers, bot_stats
    logger.info("Starting background sniper scanner...")
    is_initial_run = (len(seen_offers) == 0)

    while True:
        try:
            bot_stats["scans_count"] += 1
            bot_stats["last_scan_time"] = time.strftime("%H:%M:%S")

            lots = fetch_lots()
            if lots:
                new_offers_count = 0
                for lot in lots:
                    oid = lot["offer_id"]

                    if oid not in seen_offers:
                        seen_offers.add(oid)
                        new_offers_count += 1

                        if not is_initial_run:
                            # Push notification for truly profitable finds
                            logger.info(f"GOLD MINE FOUND: {lot['price']} RUB, ID: {oid}")
                            msg = format_gold_message(lot, is_new_alert=True)
                            kb = make_lot_keyboard(lot["href"])

                            try:
                                bot.send_message(TARGET_CHAT_ID, msg, reply_markup=kb)
                                bot_stats["alerts_sent"] += 1
                            except Exception as e:
                                logger.error(f"Error sending alert: {e}")

                if is_initial_run:
                    logger.info(f"Initial seeding complete: {len(seen_offers)} offers cached.")
                    save_seen_offers(seen_offers)
                    is_initial_run = False
                else:
                    if new_offers_count > 0:
                        save_seen_offers(seen_offers)
                        logger.info(f"Cached {new_offers_count} new lots.")

        except Exception as e:
            logger.error(f"Error in background scanner: {e}")

        time.sleep(CHECK_INTERVAL_SECONDS)

# ---------------- MAIN ENTRYPOINT ----------------
if __name__ == "__main__":
    logger.info("Starting FunPay Brawl Stars Sniper...")

    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()

    scanner_thread = threading.Thread(target=background_scanner_loop, daemon=True)
    scanner_thread.start()

    logger.info("Bot polling Telegram...")
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=15)
        except Exception as e:
            logger.error(f"Polling crashed: {e}, restarting in 5s...")
            time.sleep(5)
