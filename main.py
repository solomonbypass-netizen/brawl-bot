import time
import logging
import threading
import io
import requests
import telebot

from core.config import BOT_TOKEN, TARGET_CHAT_ID, CHECK_INTERVAL_SECONDS, HEADERS, COOKIES
from core.server import run_http_server
from core.scanner import load_seen_offers, save_seen_offers, fetch_lots, deep_inspect_offer
from core.bot_ui import format_gold_message, make_lot_keyboard, get_main_keyboard, get_settings_inline_keyboard
from core.user_settings import get_user_limit, set_user_limit

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

# In-memory cache for offer screenshots so user can request full album
offer_screenshots_cache = {}

def send_lot_to_user(chat_id, lot, is_new_alert=False):
    """
    Sends lot with deep inspection details (screenshots, online badge).
    Downloads image stream directly to bypass Cloudflare/CDN blocking of Telegram bots.
    """
    deep_data = deep_inspect_offer(lot.get("href"))
    lot.update(deep_data)

    offer_id = lot.get("offer_id", "")
    screenshots = lot.get("screenshots", [])
    if offer_id and screenshots:
        offer_screenshots_cache[str(offer_id)] = screenshots

    msg = format_gold_message(lot, is_new_alert=is_new_alert)
    kb = make_lot_keyboard(lot["href"], screenshots=screenshots, offer_id=offer_id)

    sent = False

    # Try downloading image and streaming bytes directly to Telegram
    if screenshots:
        try:
            r = requests.get(screenshots[0], headers=HEADERS, cookies=COOKIES, timeout=5)
            if r.status_code == 200 and len(r.content) > 1000:
                photo_stream = io.BytesIO(r.content)
                photo_stream.name = "screenshot.jpg"
                bot.send_photo(chat_id, photo=photo_stream, caption=msg, reply_markup=kb)
                sent = True
        except Exception as e:
            logger.warning(f"Direct photo stream upload failed ({e}), falling back to text...")

    if not sent:
        bot.send_message(chat_id, msg, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("scr:"))
def handle_view_all_screenshots(call):
    offer_id = call.data.split(":")[1]
    screenshots = offer_screenshots_cache.get(offer_id, [])

    if not screenshots:
        bot.answer_callback_query(call.id, "Скриншоты устарели или не найдены в кэше.", show_alert=True)
        return

    bot.answer_callback_query(call.id, f"Отправляю все {len(screenshots)} скриншотов в чат...")

    media_group = []
    for i, img_url in enumerate(screenshots[:8]):
        try:
            r = requests.get(img_url, headers=HEADERS, cookies=COOKIES, timeout=4)
            if r.status_code == 200 and len(r.content) > 1000:
                stream = io.BytesIO(r.content)
                stream.name = f"screen_{i}.jpg"
                caption = f"📸 Скриншот {i+1} из {len(screenshots)}" if i == 0 else None
                media_group.append(telebot.types.InputMediaPhoto(media=stream, caption=caption))
        except Exception as e:
            logger.warning(f"Failed to fetch screenshot {img_url}: {e}")

    if len(media_group) >= 2:
        bot.send_media_group(call.message.chat.id, media=media_group)
    elif len(media_group) == 1:
        bot.send_photo(call.message.chat.id, photo=media_group[0].media)
    else:
        bot.send_message(call.message.chat.id, "Не удалось скачать скриншоты. Открой лот на FunPay по ссылке выше.")


# ---------------- CORE SEARCH EXECUTION ----------------
def execute_deal_search(chat_id, requested_limit=None):
    current_limit = get_user_limit(chat_id)
    limit = requested_limit if requested_limit is not None else current_limit

    bot.send_message(
        chat_id, 
        f"⚡ <b>Ищу ТОП-{limit} окупных лотов...</b>\n<i>Провожу глубокий аудит страниц и скриншотов...</i>",
        reply_markup=get_main_keyboard(current_limit)
    )
    lots = fetch_lots()
    lots.sort(key=lambda x: (x["reviews"] >= 10, x["profit"]), reverse=True)

    if not lots:
        bot.send_message(
            chat_id, 
            "Сейчас на FunPay нет лотов, проходящих строгий фильтр окупаемости. Мониторинг ждет новые вбросы!", 
            reply_markup=get_main_keyboard(current_limit)
        )
        return

    selected_lots = lots[:limit]
    bot.send_message(chat_id, f"✅ Найдено <b>{len(lots)}</b> окупных вариантов. Загружаю <b>ТОП-{len(selected_lots)}</b>:")
    for lot in selected_lots:
        send_lot_to_user(chat_id, lot, is_new_alert=False)
        time.sleep(0.3)


# ---------------- TELEGRAM HANDLERS ----------------
@bot.message_handler(commands=["start", "help"])
def cmd_start(message):
    limit = get_user_limit(message.chat.id)
    text = (
        "👋 <b>Снайпер окупных аккаунтов Brawl Stars активен! [v3 Speed & Quantity Control]</b>\n\n"
        "<b>Критерии жесткого отбора (только реальный профит):</b>\n"
        "• Цена строго <b>100–420 ₽</b> (минимальный риск)\n"
        "• Наличие <b>OG-скинов (2018–2020)</b> или <b>запас гемов/Brawl Pass</b>\n"
        "• Или <b>78+ бравлеров / 14+ праймов</b> за копейки\n"
        "• 🟢 <b>Авто-проверка:</b> продавец онлайн + прикрепленные скриншоты\n"
        "• Чистая окупаемость от <b>+350 ₽ до +1200 ₽</b> со сделки\n\n"
        f"⚡ <i>Текущий лимит выдачи: <b>{limit} лот(а)</b></i>\n"
        "Выбирай нужный вариант на клавиатуре:"
    )
    bot.send_message(message.chat.id, text, reply_markup=get_main_keyboard(limit))

@bot.message_handler(func=lambda m: m.text and "1 лучший лот" in m.text.lower())
def handle_top_1(message):
    execute_deal_search(message.chat.id, requested_limit=1)

@bot.message_handler(func=lambda m: m.text and "2 лучших лота" in m.text.lower())
def handle_top_2(message):
    execute_deal_search(message.chat.id, requested_limit=2)

@bot.message_handler(func=lambda m: m.text and ("лимит" in m.text.lower() or "настройк" in m.text.lower()))
def handle_settings_menu(message):
    limit = get_user_limit(message.chat.id)
    text = (
        "⚙️ <b>Настройка количества лотов при выдаче:</b>\n\n"
        f"Сейчас при поиске выдается: <b>{limit} шт.</b>\n"
        "Выберите, сколько лучших вариантов загружать:"
    )
    bot.send_message(message.chat.id, text, reply_markup=get_settings_inline_keyboard(limit))

@bot.callback_query_handler(func=lambda call: call.data.startswith("setlim:"))
def handle_limit_selection(call):
    new_limit = int(call.data.split(":")[1])
    saved = set_user_limit(call.message.chat.id, new_limit)
    bot.answer_callback_query(call.id, f"✅ Лимит выдачи: {saved} шт.")
    
    try:
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_settings_inline_keyboard(saved)
        )
    except Exception:
        pass

    bot.send_message(
        call.message.chat.id,
        f"👌 Настройка сохранена! Теперь при поиске бот покажет <b>ТОП-{saved}</b> лотов.",
        reply_markup=get_main_keyboard(saved)
    )

@bot.message_handler(func=lambda m: m.text and "статус" in m.text.lower())
def handle_status(message):
    limit = get_user_limit(message.chat.id)
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
        f"🔔 <b>Отправлено новых алертов:</b> {bot_stats['alerts_sent']}\n"
        f"⚙️ <b>Твой лимит выдачи:</b> {limit} шт.\n\n"
        "🎯 <i>Глубокий аудит страниц офферов и скриншотов активен.</i>"
    )
    bot.send_message(message.chat.id, text, reply_markup=get_main_keyboard(limit))

@bot.message_handler(func=lambda m: True)
def handle_fallback(message):
    limit = get_user_limit(message.chat.id)
    execute_deal_search(message.chat.id, requested_limit=limit)

# ---------------- BACKGROUND SCANNER ----------------
def background_scanner_loop():
    global seen_offers, bot_stats
    logger.info("Starting background sniper scanner with Deep Inspection...")
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
                            try:
                                send_lot_to_user(TARGET_CHAT_ID, lot, is_new_alert=True)
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
    logger.info("Initializing Modular FunPay Sniper Architecture with Deep Inspection & Custom Limit...")

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
