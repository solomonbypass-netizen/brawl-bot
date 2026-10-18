import os
import re
import sys
import time
import json
import logging
import threading
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
        # Keep only last 10,000 IDs to avoid huge files
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

# ---------------- PARSER & VALUATION ----------------
PATTERN_STATS = re.compile(r"(\d+)\s*кубк\w*,\s*(\d+)\s*бравлер\w*(?:,\s*(\d+)\s*прайм\w*)?", re.IGNORECASE)

def clean_price(price_str):
    cleaned = re.sub(r"[^\d.]", "", price_str.replace(" ", "").replace(",", "."))
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

def fetch_lots():
    """Fetches FunPay Brawl Stars section and parses lots."""
    try:
        resp = requests.get(FUNPAY_URL, headers=HEADERS, timeout=15)
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
                
            # Extract offer ID
            offer_id_match = re.search(r"id=(\d+)", href)
            offer_id = offer_id_match.group(1) if offer_id_match else href
            
            desc_el = lot.find("div", class_="tc-desc-text")
            price_el = lot.find("div", class_="tc-price")
            user_el = lot.find("div", class_="media-user-name")
            rating_el = lot.find("span", class_="rating-mini-count")
            
            if not desc_el or not price_el:
                continue
                
            desc = desc_el.get_text(strip=True)
            price = clean_price(price_el.get_text(strip=True))
            seller = user_el.get_text(strip=True) if user_el else "Неизвестен"
            reviews = int(rating_el.get_text(strip=True)) if rating_el else 0
            
            match = PATTERN_STATS.search(desc)
            trophies = int(match.group(1)) if match else 0
            brawlers = int(match.group(2)) if match and match.group(2) else 0
            primes = int(match.group(3)) if match and match.group(3) else 0
            
            desc_lower = desc.lower()
            has_firstmail = any(k in desc_lower for k in [
                "firstmail", "родная почта", "родная", "с почтой", "отдам почту", "чистая почта", "почта рамблер", "рамблер", "mail.ru"
            ])
            is_negotiable = any(k in desc_lower for k in ["договорная", "цена в лс", "писать в лс"])
            
            # Valuation calculation
            est_value = (trophies * 0.035) + (brawlers * 18.0) + (primes * 35.0)
            if trophies > 150000:
                est_value = (50000 * 0.035) + (brawlers * 18.0) + (primes * 35.0)
                
            margin_score = (est_value / price) if price > 0 else 0
            
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
                "is_negotiable": is_negotiable,
                "est_value": round(est_value),
                "margin_score": round(margin_score, 1)
            })
            
        return parsed_lots
    except Exception as e:
        logger.error(f"Error fetching lots: {e}")
        return []

def format_lot_message(lot, is_new_alert=False):
    """Formats lot into a readable message."""
    title = "🚨 <b>НОВЫЙ ВЫГОДНЫЙ АККАУНТ НА FUNPAY!</b>" if is_new_alert else "🔥 <b>НАХОДКА ПОД ПЕРЕПРОДАЖУ:</b>"
    mail_info = "✅ <b>Родная почта / Firstmail включена</b>" if lot["has_firstmail"] else "⚠️ <i>Почту нужно уточнять у продавца</i>"
    
    msg = (
        f"{title}\n\n"
        f"💰 <b>Цена:</b> <code>{lot['price']:g} ₽</code>\n"
        f"📈 <b>Оценка стоимости:</b> ~<code>{lot['est_value']} ₽</code> (<b>x{lot['margin_score']}</b>)\n\n"
        f"🏆 <b>Кубков:</b> <b>{lot['trophies']:,}</b>\n"
        f"👤 <b>Бравлеров:</b> <b>{lot['brawlers']}</b>\n"
        f"⚡ <b>Праймов (11 ур):</b> <b>{lot['primes']}</b>\n\n"
        f"👤 <b>Продавец:</b> {lot['seller']} (⭐ <b>{lot['reviews']}</b> отзывов)\n"
        f"📧 {mail_info}\n\n"
        f"📝 <i>{lot['desc'][:110]}...</i>"
    )
    return msg

def make_lot_keyboard(href):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="🔗 Купить на FunPay", url=href))
    return kb

def get_main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_top = types.KeyboardButton("🚀 Найти лучшие лоты")
    btn_mail = types.KeyboardButton("🛡️ Только с родной почтой")
    btn_cheap = types.KeyboardButton("⚡ Быстрый флип (< 500₽)")
    btn_status = types.KeyboardButton("📊 Статус бота")
    kb.add(btn_top, btn_mail)
    kb.add(btn_cheap, btn_status)
    return kb

# ---------------- BOT COMMAND HANDLERS ----------------
@bot.message_handler(commands=["start", "help"])
def cmd_start(message):
    text = (
        "👋 <b>Добро пожаловать в FunPay Brawl Arbitrage Bot!</b>\n\n"
        "Бот 24/7 сканирует раздел Brawl Stars на FunPay, математически оценивает аккаунты "
        "и мгновенно присылает уведомления о новых дешевых аккаунтах с высокой маржой.\n\n"
        "Используй кнопки ниже для моментального поиска:"
    )
    bot.send_message(message.chat.id, text, reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda m: m.text == "🚀 Найти лучшие лоты")
def handle_top_deals(message):
    bot.send_message(message.chat.id, "🔍 Сканирую каталог FunPay на наличие максимальной маржи...")
    lots = fetch_lots()
    if not lots:
        bot.send_message(message.chat.id, "❌ Не удалось получить список лотов. Попробуй через минуту.")
        return
        
    candidates = [
        l for l in lots 
        if not l["is_negotiable"] and 200 <= l["price"] <= 1500 and l["trophies"] >= 20000 and l["brawlers"] >= 65 and l["margin_score"] >= 3.0
    ]
    candidates.sort(key=lambda x: x["margin_score"], reverse=True)
    
    if not candidates:
        bot.send_message(message.chat.id, "Сейчас нет лотов с маржой выше 3.0x. Ждем новые предложения!")
        return
        
    bot.send_message(message.chat.id, f"✅ Найдено <b>{len(candidates)}</b> сочных вариантов. Вот ТОП-3 прямо сейчас:")
    for lot in candidates[:3]:
        bot.send_message(message.chat.id, format_lot_message(lot), reply_markup=make_lot_keyboard(lot["href"]))

@bot.message_handler(func=lambda m: m.text == "🛡️ Только с родной почтой")
def handle_mail_deals(message):
    bot.send_message(message.chat.id, "🔍 Ищу безопасные аккаунты с подтвержденной родной почтой...")
    lots = fetch_lots()
    candidates = [
        l for l in lots 
        if l["has_firstmail"] and not l["is_negotiable"] and 150 <= l["price"] <= 1200 and l["trophies"] >= 15000 and l["margin_score"] >= 2.5
    ]
    candidates.sort(key=lambda x: x["margin_score"], reverse=True)
    
    if not candidates:
        bot.send_message(message.chat.id, "Лотов с явным указанием родной почты в топе сейчас нет. Мониторинг продолжается.")
        return
        
    bot.send_message(message.chat.id, f"✅ Найдено <b>{len(candidates)}</b> безопасных лотов с почтой. Вот лучшие:")
    for lot in candidates[:3]:
        bot.send_message(message.chat.id, format_lot_message(lot), reply_markup=make_lot_keyboard(lot["href"]))

@bot.message_handler(func=lambda m: m.text == "⚡ Быстрый флип (< 500₽)")
def handle_cheap_deals(message):
    bot.send_message(message.chat.id, "🔍 Ищу дешевые аккаунты до 500₽ с быстрой окупаемостью...")
    lots = fetch_lots()
    candidates = [
        l for l in lots 
        if not l["is_negotiable"] and 150 <= l["price"] <= 500 and l["trophies"] >= 15000 and l["brawlers"] >= 50 and l["margin_score"] >= 4.0
    ]
    candidates.sort(key=lambda x: x["margin_score"], reverse=True)
    
    if not candidates:
        bot.send_message(message.chat.id, "Дешевых аномалий до 500₽ сейчас нет.")
        return
        
    bot.send_message(message.chat.id, f"✅ Найдено <b>{len(candidates)}</b> вариантов для быстрого флипа. Топ-3:")
    for lot in candidates[:3]:
        bot.send_message(message.chat.id, format_lot_message(lot), reply_markup=make_lot_keyboard(lot["href"]))

@bot.message_handler(func=lambda m: m.text == "📊 Статус бота")
def handle_status(message):
    uptime_sec = int(time.time() - bot_stats["start_time"])
    hours = uptime_sec // 3600
    minutes = (uptime_sec % 3600) // 60
    
    text = (
        "📊 <b>СТАТИСТИКА МОНИТОРИНГА:</b>\n\n"
        f"🟢 <b>Статус:</b> Активен 24/7\n"
        f"⏱ <b>Аптайм:</b> {hours} ч. {minutes} мин.\n"
        f"🔄 <b>Проведено сканирований:</b> {bot_stats['scans_count']}\n"
        f"🕒 <b>Последнее сканирование:</b> {bot_stats['last_scan_time']}\n"
        f"📦 <b>База известных лотов:</b> {len(seen_offers)} шт.\n"
        f"🔔 <b>Отправлено авто-алертов:</b> {bot_stats['alerts_sent']}"
    )
    bot.send_message(message.chat.id, text)

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
                        
                        # Only send alerts for genuinely NEW lots appearing after initial database seeding
                        if not is_initial_run:
                            # Criteria for push notification:
                            # 1. Price between 150 and 1500 RUB
                            # 2. At least 15,000 trophies and 60 brawlers
                            # 3. High margin multiplier (>= 3.0x)
                            # 4. Not a negotiable placeholder
                            if (not lot["is_negotiable"] and 
                                150 <= lot["price"] <= 1500 and 
                                lot["trophies"] >= 15000 and 
                                lot["brawlers"] >= 60 and 
                                lot["margin_score"] >= 3.0):
                                
                                logger.info(f"ALERTTT! Found new hot deal: {lot['price']} RUB, {lot['trophies']} trophies, ID: {oid}")
                                msg = format_lot_message(lot, is_new_alert=True)
                                kb = make_lot_keyboard(lot["href"])
                                
                                try:
                                    bot.send_message(TARGET_CHAT_ID, msg, reply_markup=kb)
                                    bot_stats["alerts_sent"] += 1
                                except Exception as e:
                                    logger.error(f"Error sending alert to Telegram: {e}")
                                    
                if is_initial_run:
                    logger.info(f"Initial run completed: seeded {len(seen_offers)} existing offers. Now waiting for NEW listings.")
                    save_seen_offers(seen_offers)
                    is_initial_run = False
                    # Send ready confirmation to user
                    try:
                        bot.send_message(
                            TARGET_CHAT_ID, 
                            f"✅ <b>Система мониторинга запущена!</b>\nБаза из <b>{len(seen_offers)}</b> существующих предложений зафиксирована.\n\nТеперь каждый раз, когда кто-то выставит <b>новый жирный аккаунт</b>, тебе моментально придет пуш с кнопкой покупки!",
                            reply_markup=get_main_keyboard()
                        )
                    except Exception as e:
                        logger.error(f"Failed to send startup message: {e}")
                else:
                    if new_offers_count > 0:
                        save_seen_offers(seen_offers)
                        logger.info(f"Scan finished: processed {new_offers_count} new lots.")
                        
        except Exception as e:
            logger.error(f"Error in scanner loop: {e}")
            
        time.sleep(CHECK_INTERVAL_SECONDS)

# ---------------- MAIN ENTRYPOINT ----------------
if __name__ == "__main__":
    logger.info("Initializing FunPay Brawl Stars Bot...")
    
    # Start background thread
    scanner_thread = threading.Thread(target=background_scanner_loop, daemon=True)
    scanner_thread.start()
    
    # Start Telegram polling
    logger.info("Bot is now polling Telegram for commands...")
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=15)
        except Exception as e:
            logger.error(f"Polling crashed: {e}, restarting in 5 seconds...")
            time.sleep(5)
