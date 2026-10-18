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
CHECK_INTERVAL_SECONDS = 45  # Scan interval in seconds

# Configure logging
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
    "cy": "rub"  # Force FunPay to always respond with Russian Rubles (RUB)
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

# ---------------- ADVANCED PARSER & VALUATION ----------------
PATTERN_STATS = re.compile(r"(\d+)\s*кубк\w*,\s*(\d+)\s*бравлер\w*(?:,\s*(\d+)\s*прайм\w*)?", re.IGNORECASE)

SPAM_KEYWORDS = [
    "договорная", "цена в лс", "писать в лс", "в лс", "не покупать", 
    "куплю", "обмен", "тест", "витрина", "предлагайте", "предлагать", 
    "цена договор", "договор", "отзыв", "пустышка"
]

def extract_exact_rub_price(price_el):
    """
    Extracts the true, accurate price in RUB.
    FunPay stores the exact price in RUB inside the 'data-s' attribute.
    This prevents foreign currency errors (e.g. 206.26 USD treated as 206 RUB).
    """
    if not price_el:
        return 0.0

    # 1. Primary: 'data-s' attribute (FunPay's source of truth in base currency/RUB)
    data_s = price_el.get("data-s")
    if data_s:
        try:
            val = float(data_s)
            if val > 0:
                return round(val, 2)
        except ValueError:
            pass

    # 2. Fallback: Parse text and account for currencies
    text = price_el.get_text(strip=True)
    cleaned = re.sub(r"[^\d.]", "", text.replace(" ", "").replace(",", "."))
    try:
        val = float(cleaned)
    except ValueError:
        return 0.0

    # Currency exchange rate fallback if FunPay ignored cookie
    if "$" in text or "usd" in text.lower():
        return round(val * 95.0, 2)
    elif "€" in text or "eur" in text.lower():
        return round(val * 105.0, 2)

    return round(val, 2)

def calculate_trust_score(seller, reviews, has_mail):
    """Calculates risk and trust rating (1 to 10)."""
    score = 5
    if reviews >= 50:
        score += 3
    elif reviews >= 15:
        score += 2
    elif reviews == 0:
        score -= 3

    if has_mail:
        score += 2

    return max(1, min(10, score))

def fetch_lots():
    """Fetches FunPay Brawl Stars section, parses and strictly validates lots."""
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

            # Filter out non-actionable lots (0 rub, or obvious spam)
            if price <= 10.0:
                continue

            match = PATTERN_STATS.search(desc)
            trophies = int(match.group(1)) if match else 0
            brawlers = int(match.group(2)) if match and match.group(2) else 0
            primes = int(match.group(3)) if match and match.group(3) else 0

            desc_lower = desc.lower()

            # Anti-Spam / Placeholder detection
            is_spam = any(kw in desc_lower for kw in SPAM_KEYWORDS)

            # Mail verification
            has_firstmail = any(k in desc_lower for k in [
                "firstmail", "родная почта", "родная", "с почтой", "отдам почту", 
                "чистая почта", "почта рамблер", "рамблер", "mail.ru", "почта отдается"
            ])

            # Realistic Trophies normalization (fix typo values like 145000 or 500000)
            valid_trophies = trophies
            if trophies > 95000:
                # If someone claims >95k trophies, cap the valuation score to a realistic max
                valid_trophies = min(trophies, 70000)

            # Realistic Market Valuation in Telegram (RUB):
            # Accounts with 60+ brawlers and 25k-40k trophies easily sell for 800 - 2200 RUB
            est_value = (valid_trophies * 0.035) + (brawlers * 18.0) + (primes * 35.0)

            # Net Estimated Profit
            net_profit = est_value - price
            margin_score = (est_value / price) if price > 0 else 0
            trust_score = calculate_trust_score(seller, reviews, has_firstmail)

            parsed_lots.append({
                "offer_id": offer_id,
                "href": href,
                "price": price,
                "trophies": trophies,
                "brawlers": brawlers,
                "primes": primes,
                "seller": seller,
                "reviews": reviews,
                "desc": desc,
                "has_firstmail": has_firstmail,
                "is_spam": is_spam,
                "trust_score": trust_score,
                "est_value": round(est_value),
                "net_profit": round(net_profit),
                "margin_score": round(margin_score, 1)
            })

        return parsed_lots
    except Exception as e:
        logger.error(f"Error fetching lots: {e}")
        return []

def format_lot_message(lot, is_new_alert=False):
    """Formats lot into a detailed analytical dossier."""
    title = "🚨 <b>НОВЫЙ ВЫГОДНЫЙ АККАУНТ НА FUNPAY!</b>" if is_new_alert else "💎 <b>АНАЛИЗ ЛОТА ПОД ПЕРЕПРОДАЖУ:</b>"
    
    # Mail badge
    if lot["has_firstmail"]:
        mail_badge = "🟢 <b>Родная почта / Firstmail подтверждена</b>"
    else:
        mail_badge = "🟡 <b>Почту нужно уточнять (перепривязка)</b>"

    # Trust badge
    if lot["trust_score"] >= 8:
        trust_badge = f"🛡️ <b>Надежность:</b> <code>Высокая ({lot['trust_score']}/10)</code> ⭐ Проверенный"
    elif lot["trust_score"] >= 5:
        trust_badge = f"⚖️ <b>Надежность:</b> <code>Средняя ({lot['trust_score']}/10)</code>"
    else:
        trust_badge = f"⚠️ <b>Надежность:</b> <code>Новичок ({lot['trust_score']}/10)</code> <i>Проверяй данные перед подтверждением!</i>"

    profit_color = "🟢" if lot["net_profit"] > 0 else "🔴"

    msg = (
        f"{title}\n\n"
        f"💵 <b>Цена на FunPay:</b> <code>{lot['price']:g} ₽</code>\n"
        f"📈 <b>Рыночная цена в ТГ:</b> ~<code>{lot['est_value']} ₽</code> (<b>x{lot['margin_score']}</b>)\n"
        f"{profit_color} <b>Ожидаемая чистая прибыль:</b> <b>+{lot['net_profit']} ₽</b>\n\n"
        f"🏆 <b>Кубков:</b> <b>{lot['trophies']:,}</b>\n"
        f"👤 <b>Бравлеров:</b> <b>{lot['brawlers']}</b>\n"
        f"⚡ <b>Праймов (11 ур):</b> <b>{lot['primes']}</b>\n\n"
        f"👤 <b>Продавец:</b> {lot['seller']} (⭐ <b>{lot['reviews']}</b> отзывов)\n"
        f"{trust_badge}\n"
        f"{mail_badge}\n\n"
        f"📝 <i>{lot['desc'][:120]}...</i>"
    )
    return msg

def make_lot_keyboard(href):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="🔗 Купить на FunPay", url=href))
    return kb

def get_main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_tier1 = types.KeyboardButton("💎 Топ TIER-1 (Надежные)")
    btn_hot = types.KeyboardButton("🚀 Все горячие лоты")
    btn_flip = types.KeyboardButton("⚡ Быстрый флип (< 500₽)")
    btn_status = types.KeyboardButton("📊 Статус и статистика")
    kb.add(btn_tier1, btn_hot)
    kb.add(btn_flip, btn_status)
    return kb

# ---------------- BOT COMMAND HANDLERS ----------------
@bot.message_handler(commands=["start", "help"])
def cmd_start(message):
    text = (
        "👋 <b>Добро пожаловать в обновленный FunPay Brawl Stars Arbitrage Scanner!</b>\n\n"
        "<b>Что обновлено:</b>\n"
        "• Точный расчет цен в рублях (без ошибок валют)\n"
        "• Фильтр спама и фейковых кубков\n"
        "• Индекс доверия к продавцу (Trust Score 1-10)\n"
        "• Расчет ожидаемой чистой прибыли в рублях\n\n"
        "Выбери нужный фильтр поиска ниже:"
    )
    bot.send_message(message.chat.id, text, reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda m: m.text and any(k in m.text for k in ["TIER-1", "Только с родной почтой", "Надежные"]))
def handle_tier1(message):
    bot.send_message(message.chat.id, "🔍 Ищу TIER-1 лоты (проверенные продавцы + высокая маржа + родная почта)...")
    lots = fetch_lots()
    
    candidates = [
        l for l in lots
        if not l["is_spam"] and 200 <= l["price"] <= 1500 and l["trust_score"] >= 6 and l["trophies"] >= 20000 and l["margin_score"] >= 2.2
    ]
    candidates.sort(key=lambda x: (x["trust_score"], x["margin_score"]), reverse=True)

    if not candidates:
        bot.send_message(message.chat.id, "Сейчас нет лотов, подходящих под строгий TIER-1. Попробуй «Все горячие лоты».", reply_markup=get_main_keyboard())
        return

    bot.send_message(message.chat.id, f"✅ Найдено <b>{len(candidates)}</b> проверенных TIER-1 аккаунтов. Вот лучшие:", reply_markup=get_main_keyboard())
    for lot in candidates[:3]:
        bot.send_message(message.chat.id, format_lot_message(lot), reply_markup=make_lot_keyboard(lot["href"]))

@bot.message_handler(func=lambda m: m.text and any(k in m.text for k in ["Найти лучшие лоты", "Все горячие лоты", "горячие лоты", "лучшие лоты"]))
def handle_hot_deals(message):
    bot.send_message(message.chat.id, "🔍 Сканирую каталог FunPay на максимальную маржу...")
    lots = fetch_lots()
    candidates = [
        l for l in lots 
        if not l["is_spam"] and 150 <= l["price"] <= 1200 and l["trophies"] >= 15000 and l["brawlers"] >= 55 and l["margin_score"] >= 2.5
    ]
    candidates.sort(key=lambda x: x["margin_score"], reverse=True)

    if not candidates:
        bot.send_message(message.chat.id, "Горячих предложений прямо сейчас нет. Мониторинг ждет новые лоты.", reply_markup=get_main_keyboard())
        return

    bot.send_message(message.chat.id, f"✅ Найдено <b>{len(candidates)}</b> выгодных лотов. ТОП-3 по марже:", reply_markup=get_main_keyboard())
    for lot in candidates[:3]:
        bot.send_message(message.chat.id, format_lot_message(lot), reply_markup=make_lot_keyboard(lot["href"]))

@bot.message_handler(func=lambda m: m.text and any(k in m.text for k in ["Быстрый флип", "флип"]))
def handle_quick_flip(message):
    bot.send_message(message.chat.id, "🔍 Ищу дешевые аккаунты до 500₽ для быстрого оборота...")
    lots = fetch_lots()
    candidates = [
        l for l in lots 
        if not l["is_spam"] and 150 <= l["price"] <= 500 and l["trophies"] >= 15000 and l["brawlers"] >= 50 and l["margin_score"] >= 2.5
    ]
    candidates.sort(key=lambda x: x["net_profit"], reverse=True)

    if not candidates:
        bot.send_message(message.chat.id, "Дешевых аномалий до 500₽ сейчас нет.", reply_markup=get_main_keyboard())
        return

    bot.send_message(message.chat.id, f"✅ Найдено <b>{len(candidates)}</b> лотов для быстрого флипа. Топ-3:", reply_markup=get_main_keyboard())
    for lot in candidates[:3]:
        bot.send_message(message.chat.id, format_lot_message(lot), reply_markup=make_lot_keyboard(lot["href"]))

@bot.message_handler(func=lambda m: m.text and any(k in m.text for k in ["Статус", "статус"]))
def handle_status(message):
    uptime_sec = int(time.time() - bot_stats["start_time"])
    hours = uptime_sec // 3600
    minutes = (uptime_sec % 3600) // 60

    text = (
        "📊 <b>СТАТУС ОБЛАЧНОГО МОНИТОРИНГА:</b>\n\n"
        f"🟢 <b>Сервер:</b> Render Cloud 24/7\n"
        f"⏱ <b>Время работы:</b> {hours} ч. {minutes} мин.\n"
        f"🔄 <b>Проведено циклов сканирования:</b> {bot_stats['scans_count']}\n"
        f"🕒 <b>Крайний скан:</b> {bot_stats['last_scan_time']}\n"
        f"📦 <b>База известных лотов:</b> {len(seen_offers)} шт.\n"
        f"🔔 <b>Отправлено новых алертов:</b> {bot_stats['alerts_sent']}\n\n"
        "⚡ <i>Защита от валютных ошибок и спам-фильтр активны.</i>"
    )
    bot.send_message(message.chat.id, text, reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda m: True)
def handle_fallback(message):
    # Any unexpected text triggers a search and refreshes keyboard
    bot.send_message(message.chat.id, "🔍 Запускаю поиск по FunPay...", reply_markup=get_main_keyboard())
    handle_hot_deals(message)


# ---------------- BACKGROUND SCANNER THREAD ----------------
def background_scanner_loop():
    global seen_offers, bot_stats
    logger.info("Starting background scanner thread...")
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
                            # Strict alert filter for push notification:
                            # 1. Price between 150 and 1200 RUB
                            # 2. At least 18,000 trophies and 60 brawlers
                            # 3. Margin >= 2.5x and net profit >= 500 RUB
                            # 4. Not spam
                            if (not lot["is_spam"] and 
                                150 <= lot["price"] <= 1200 and 
                                lot["trophies"] >= 18000 and 
                                lot["brawlers"] >= 60 and 
                                lot["margin_score"] >= 2.5 and
                                lot["net_profit"] >= 500):

                                logger.info(f"HOT DEAL ALERT! {lot['price']} RUB, {lot['trophies']} trophies, ID: {oid}")
                                msg = format_lot_message(lot, is_new_alert=True)
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
                        logger.info(f"Processed {new_offers_count} newly listed offers.")

        except Exception as e:
            logger.error(f"Error in background scanner: {e}")

        time.sleep(CHECK_INTERVAL_SECONDS)

# ---------------- MAIN ENTRYPOINT ----------------
if __name__ == "__main__":
    logger.info("Starting updated FunPay Brawl Stars Engine...")

    # Start health-check server for Render
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    logger.info(f"Health-check server running on port {os.environ.get('PORT', 10000)}")

    # Start background monitor
    scanner_thread = threading.Thread(target=background_scanner_loop, daemon=True)
    scanner_thread.start()

    # Start Telegram polling
    logger.info("Bot polling Telegram...")
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=15)
        except Exception as e:
            logger.error(f"Polling crashed: {e}, restarting in 5s...")
            time.sleep(5)
