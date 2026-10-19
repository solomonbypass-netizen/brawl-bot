import time
import logging
import threading
import telebot
from core.config import BOT_TOKEN, TARGET_CHAT_ID, CHECK_INTERVAL_SECONDS
from core.server import run_http_server
from core.scanner import load_seen_offers, save_seen_offers, fetch_lots
from core.bot_ui import format_gold_message, make_lot_keyboard, get_main_keyboard

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("AppOrchestrator")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

bot_stats = {
    "start_time": time.time(),
    "scans_count": 0,
    "last_scan_time": "Еще не проводился",
    "alerts_sent": 0
}
seen_offers = load_seen_offers()

# ---------------- TELEGRAM HANDLERS ----------------
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
    lots.sort(key=lambda x: (x["reviews"] >= 10, x["profit"]), reverse=True)

    if not lots:
        bot.send_message(
            message.chat.id, 
            "Сейчас на FunPay нет лотов, проходящих строгий фильтр окупаемости. Мониторинг ждет новые вбросы!", 
            reply_markup=get_main_keyboard()
        )
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
        f"📦 <b>База известных лотов:</b> {len(seen_offers)} шт.\n"
        f"🔔 <b>Отправлено новых алертов:</b> {bot_stats['alerts_sent']}\n\n"
        "🎯 <i>Фильтры: цена до 450₽, OG-скины, баланс гемов, защита от минусового баланса.</i>"
    )
    bot.send_message(message.chat.id, text, reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda m: True)
def handle_fallback(message):
    handle_find_deals(message)

# ---------------- BACKGROUND SCANNER ----------------
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
                            logger.info(f"GOLD MINE DETECTED! Price: {lot['price']} RUB, ID: {oid}")
                            msg = format_gold_message(lot, is_new_alert=True)
                            kb = make_lot_keyboard(lot["href"])

                            try:
                                bot.send_message(TARGET_CHAT_ID, msg, reply_markup=kb)
                                bot_stats["alerts_sent"] += 1
                            except Exception as e:
                                logger.error(f"Error dispatching alert to Telegram: {e}")

                if is_initial_run:
                    logger.info(f"Initial seeding complete: {len(seen_offers)} offers cached.")
                    save_seen_offers(seen_offers)
                    is_initial_run = False
                else:
                    if new_offers_count > 0:
                        save_seen_offers(seen_offers)
                        logger.info(f"Processed and cached {new_offers_count} new lots.")

        except Exception as e:
            logger.error(f"Unexpected error in background loop: {e}")

        time.sleep(CHECK_INTERVAL_SECONDS)

# ---------------- MAIN RUNNER ----------------
def start_app():
    logger.info("Initializing Modular FunPay Sniper Architecture...")

    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()

    scanner_thread = threading.Thread(target=background_scanner_loop, daemon=True)
    scanner_thread.start()

    logger.info("Bot polling loop initiated...")
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=15)
        except Exception as e:
            logger.error(f"Telegram polling exception: {e}, auto-recovering in 5s...")
            time.sleep(5)

if __name__ == "__main__":
    start_app()
