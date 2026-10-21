import os
import time
import logging
import threading
import io
import html
import requests
import telebot

from core.config import BOT_TOKEN, TARGET_CHAT_ID, CHECK_INTERVAL_SECONDS, HEADERS, COOKIES
from core.server import run_http_server
from core.scanner import load_seen_offers, save_seen_offers, fetch_lots, deep_inspect_offer
from core.bot_ui import format_gold_message, make_lot_keyboard, get_main_keyboard, get_settings_inline_keyboard
from core.post_generator import generate_telegram_resale_post
from core.promo_generator import generate_viral_promo_pack
from core.video_maker import generate_ai_video_clip
from core.user_settings import (
    get_user_limit, set_user_limit,
    get_user_contact, set_user_contact,
    get_user_budget, set_user_budget
)

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

# In-memory cache for offer data and screenshots
offer_screenshots_cache = {}
offers_cache = {}

def send_lot_to_user(chat_id, lot, is_new_alert=False):
    """
    Sends lot with deep inspection details (screenshots, online badge).
    Downloads image stream directly to bypass Cloudflare/CDN blocking of Telegram bots.
    """
    deep_data = deep_inspect_offer(lot.get("href"))
    lot.update(deep_data)

    # Re-evaluate with deep OCR and detailed description!
    from core.analyzer import analyze_lot_liquidity
    is_liquid, triggers, est_tg_price, profit = analyze_lot_liquidity(lot)
    if not is_liquid:
        logger.info(f"Lot {lot.get('offer_id')} disqualified after deep OCR inspection (LOW TIER).")
        return

    offer_id = str(lot.get("offer_id", ""))
    screenshots = lot.get("screenshots", [])
    if offer_id:
        offers_cache[offer_id] = dict(lot)
        if screenshots:
            offer_screenshots_cache[offer_id] = screenshots

    msg = format_gold_message(lot, is_new_alert=is_new_alert)
    kb = make_lot_keyboard(
        lot["href"], 
        screenshots=screenshots, 
        offer_id=offer_id,
        brawlify_url=lot.get("brawlify_url"),
        brawltime_url=lot.get("brawltime_url")
    )

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

# ---------------- CALLBACK HANDLERS ----------------
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

@bot.callback_query_handler(func=lambda call: call.data.startswith("post:"))
def handle_generate_post(call):
    offer_id = call.data.split(":")[1]
    lot = offers_cache.get(offer_id)

    if not lot:
        bot.answer_callback_query(call.id, "Информация об этом лоте устарела. Запустите новый поиск.", show_alert=True)
        return

    contact = get_user_contact(call.message.chat.id)
    post_text = generate_telegram_resale_post(lot, seller_contact=contact)

    bot.answer_callback_query(call.id, "Готовый продающий пост сгенерирован!")

    response_msg = (
        "📋 <b>ГОТОВЫЙ ПОСТ ДЛЯ ВАШЕГО ТГ-КАНАЛА:</b>\n"
        "<i>(Нажмите на текст ниже, чтобы скопировать целиком в 1 клик)</i>\n\n"
        f"<pre>{html.escape(post_text)}</pre>\n\n"
        f"💡 <i>Контакт: <b>{contact}</b>. Изменить: <code>/contact @твой_юзер</code></i>"
    )
    bot.send_message(call.message.chat.id, response_msg, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("video:"))
def handle_generate_ai_video(call):
    offer_id = call.data.split(":")[1]
    lot = offers_cache.get(offer_id)

    if not lot:
        bot.answer_callback_query(call.id, "Информация об этом лоте устарела. Запустите новый поиск.", show_alert=True)
        return

    bot.answer_callback_query(call.id, "🤖 ИИ начал монтаж видео 9:16...")
    status_msg = bot.send_message(
        call.message.chat.id, 
        "⏳ <b>ИИ монтирует ролик для TikTok / Shorts...</b>\n"
        "<i>Накладываю скриншоты, анимированные хуки, плашки с ценой и призывом в ТГК (~3-4 сек)...</i>"
    )

    contact = get_user_contact(call.message.chat.id)
    video_path = None
    try:
        video_path = generate_ai_video_clip(lot, seller_contact=contact)
        if video_path and os.path.exists(video_path):
            caption = (
                "🎬 <b>ГОТОВЫЙ РОЛИК ОТ ИИ (9:16):</b>\n"
                f"• Формат: <b>Shorts / TikTok / Reels</b>\n"
                f"• Цена оффера: <code>{lot['price']:g} ₽</code> ──> <b>{lot.get('est_tg_price', 650)} ₽</b>\n"
                f"• Контакт в видео: <b>{contact}</b>\n\n"
                "👉 <i>Готово! Сохраняйте видео в галерею или жмите 'Поделиться' в TikTok / Shorts под любой трендовый звук!</i>"
            )
            with open(video_path, "rb") as vf:
                if video_path.endswith(".mp4"):
                    bot.send_video(
                        call.message.chat.id,
                        video=vf,
                        caption=caption,
                        supports_streaming=True
                    )
                else:
                    bot.send_animation(
                        call.message.chat.id,
                        animation=vf,
                        caption=caption
                    )
            try:
                bot.delete_message(call.message.chat.id, status_msg.message_id)
            except Exception:
                pass
        else:
            bot.send_message(call.message.chat.id, "❌ Не удалось сгенерировать видеофайл.")
    except Exception as e:
        logger.error(f"Error in handle_generate_ai_video: {e}")
        bot.send_message(call.message.chat.id, f"❌ Ошибка монтажа видео: {e}")
    finally:
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except Exception:
                pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("promo:"))
def handle_generate_promo_pack(call):
    offer_id = call.data.split(":")[1]
    lot = offers_cache.get(offer_id)

    if not lot:
        bot.answer_callback_query(call.id, "Информация об этом лоте устарела. Запустите новый поиск.", show_alert=True)
        return

    contact = get_user_contact(call.message.chat.id)
    promo = generate_viral_promo_pack(lot, seller_contact=contact)

    bot.answer_callback_query(call.id, "🎬 Промо-пак для Shorts/TikTok готов!")

    hook = html.escape(promo["hook_text"])
    script = html.escape(promo["voice_script"])
    caption = html.escape(promo["caption_text"])
    sound = promo["sound_recommendation"]
    fmt = promo["video_format"]

    msg = (
        "🎬 <b>ВИРУСНЫЙ ПРОМО-ПАК ДЛЯ TIKTOK / SHORTS / REELS:</b>\n"
        "<i>Используйте этот набор, чтобы смонтировать видео за 30 секунд и перелить трафик в ТГК!</i>\n\n"
        f"📌 <b>1. ТЕКСТ НА 1-Й КАДР (Хук для удержания):</b>\n"
        f"<i>(Нажмите, чтобы скопировать)</i>\n"
        f"<pre>{hook}</pre>\n\n"
        f"🎙️ <b>2. СЦЕНАРИЙ ОЗВУЧКИ (10-12 секунд):</b>\n"
        f"<i>(Озвучьте своим голосом или роботом в CapCut)</i>\n"
        f"<pre>{script}</pre>\n\n"
        f"🎵 <b>3. РЕКОМЕНДАЦИЯ ПО МОНТАЖУ:</b>\n"
        f"• {sound}\n"
        f"• {fmt}\n\n"
        f"📝 <b>4. ОПИСАНИЕ И ВИРУСНЫЕ ХЭШТЕГИ:</b>\n"
        f"<pre>{caption}</pre>\n\n"
        f"💡 <i>Скриншоты аккаунта для видео можно выгрузить кнопкой «Все фото» выше!</i>"
    )
    bot.send_message(call.message.chat.id, msg, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("setlim:"))
def handle_limit_selection(call):
    new_limit = int(call.data.split(":")[1])
    saved = set_user_limit(call.message.chat.id, new_limit)
    current_budget = get_user_budget(call.message.chat.id)
    bot.answer_callback_query(call.id, f"✅ Лимит выдачи: {saved} шт.")
    
    try:
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_settings_inline_keyboard(saved, current_budget)
        )
    except Exception:
        pass

    bot.send_message(
        call.message.chat.id,
        f"👌 Настройка сохранена! Теперь при поиске бот покажет <b>ТОП-{saved}</b> лотов.",
        reply_markup=get_main_keyboard(saved)
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("setbdg:"))
def handle_budget_selection(call):
    new_budget = int(call.data.split(":")[1])
    saved_budget = set_user_budget(call.message.chat.id, new_budget)
    current_limit = get_user_limit(call.message.chat.id)
    bot.answer_callback_query(call.id, f"✅ Максимальная цена: {saved_budget} ₽")

    try:
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_settings_inline_keyboard(current_limit, saved_budget)
        )
    except Exception:
        pass

    bot.send_message(
        call.message.chat.id,
        f"💰 Бюджетный фильтр обновлен: <b>до {saved_budget} ₽</b>.",
        reply_markup=get_main_keyboard(current_limit)
    )


# ---------------- CORE SEARCH EXECUTION ----------------
def execute_deal_search(chat_id, requested_limit=None):
    current_limit = get_user_limit(chat_id)
    limit = requested_limit if requested_limit is not None else current_limit
    max_budget = get_user_budget(chat_id)

    budget_label = f"до {max_budget} ₽" if max_budget < 420 else "без ограничений"
    bot.send_message(
        chat_id, 
        f"⚡ <b>Ищу ТОП-{limit} окупных лотов...</b>\n<i>Фильтр бюджета: {budget_label}</i>",
        reply_markup=get_main_keyboard(current_limit)
    )
    lots = fetch_lots()
    
    # Filter by user budget ceiling
    lots = [l for l in lots if l["price"] <= max_budget]
    lots.sort(key=lambda x: (x["reviews"] >= 10, x["profit"]), reverse=True)

    if not lots:
        bot.send_message(
            chat_id, 
            f"Сейчас на FunPay нет окупных лотов в диапазоне {budget_label}. Мониторинг ждет новые вбросы!", 
            reply_markup=get_main_keyboard(current_limit)
        )
        return

    selected_lots = lots[:limit]
    bot.send_message(chat_id, f"✅ Отобрано <b>{len(selected_lots)}</b> из {len(lots)} подходящих окупных вариантов:")
    for lot in selected_lots:
        send_lot_to_user(chat_id, lot, is_new_alert=False)
        time.sleep(0.3)


# ---------------- TELEGRAM HANDLERS ----------------
@bot.message_handler(commands=["start", "help"])
def cmd_start(message):
    limit = get_user_limit(message.chat.id)
    budget = get_user_budget(message.chat.id)
    contact = get_user_contact(message.chat.id)
    text = (
        "👋 <b>Снайпер окупных аккаунтов Brawl Stars активен! [v3 Turbo Flip Edition]</b>\n\n"
        "<b>Критерии жесткого отбора (только реальный профит):</b>\n"
        f"• Цена: строго <b>100–{budget} ₽</b>\n"
        "• Наличие <b>OG-скинов (2018–2020)</b> или <b>запас гемов/Brawl Pass</b>\n"
        "• Или <b>78+ бравлеров / 14+ праймов</b> за копейки\n"
        "• 🟢 <b>Авто-проверка:</b> продавец онлайн + прикрепленные скриншоты\n"
        "• Чистая окупаемость от <b>+350 ₽ до +1200 ₽</b> со сделки\n\n"
        "📢 <b>Новинка:</b> под каждым лотом кнопка <b>«Готовый пост в ТГ»</b> — генерирует продающий пост для вашего канала с копированием в 1 тап!\n\n"
        f"⚡ <i>Лимит: <b>{limit} шт.</b> | Бюджет: <b>до {budget} ₽</b> | Контакт: <b>{contact}</b></i>\n"
        "Выбирай нужный вариант на клавиатуре:"
    )
    bot.send_message(message.chat.id, text, reply_markup=get_main_keyboard(limit))

@bot.message_handler(commands=["contact"])
def cmd_set_contact(message):
    parts = message.text.split(maxsplit=1)
    limit = get_user_limit(message.chat.id)
    if len(parts) < 2:
        current = get_user_contact(message.chat.id)
        bot.send_message(
            message.chat.id,
            f"Текущий контакт для постов перепродажи: <b>{current}</b>\n\n"
            "Чтобы изменить контакт, отправьте:\n<code>/contact @ваш_юзернейм</code>",
            reply_markup=get_main_keyboard(limit)
        )
        return

    new_contact = parts[1].strip()
    saved = set_user_contact(message.chat.id, new_contact)
    bot.send_message(
        message.chat.id,
        f"✅ Контакт сохранен: <b>{saved}</b>!\nТеперь этот юзернейм автоматически подставляется в продающие посты.",
        reply_markup=get_main_keyboard(limit)
    )

@bot.message_handler(func=lambda m: m.text and "1 лучший лот" in m.text.lower())
def handle_top_1(message):
    execute_deal_search(message.chat.id, requested_limit=1)

@bot.message_handler(func=lambda m: m.text and "2 лучших лота" in m.text.lower())
def handle_top_2(message):
    execute_deal_search(message.chat.id, requested_limit=2)

@bot.message_handler(func=lambda m: m.text and ("лимит" in m.text.lower() or "настройк" in m.text.lower()))
def handle_settings_menu(message):
    limit = get_user_limit(message.chat.id)
    budget = get_user_budget(message.chat.id)
    contact = get_user_contact(message.chat.id)
    text = (
        "⚙️ <b>НАСТРОЙКИ СНАЙПЕРА И ПЕРЕПРОДАЖИ:</b>\n\n"
        f"• Количество выдачи: <b>{limit} шт.</b>\n"
        f"• Потолок цены: <b>до {budget} ₽</b>\n"
        f"• Твой контакт в постах: <b>{contact}</b>\n\n"
        "Выберите лимит и бюджет ниже (или смените контакт командой <code>/contact @юзернейм</code>):"
    )
    bot.send_message(message.chat.id, text, reply_markup=get_settings_inline_keyboard(limit, budget))

@bot.message_handler(func=lambda m: m.text and "статус" in m.text.lower())
def handle_status(message):
    limit = get_user_limit(message.chat.id)
    budget = get_user_budget(message.chat.id)
    contact = get_user_contact(message.chat.id)
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
        f"⚙️ <b>Настройки:</b> {limit} шт. | до {budget} ₽ | {contact}\n\n"
        "🎯 <i>Глубокий аудит, генератор постов и альбом фото активны.</i>"
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
    logger.info("Initializing Modular FunPay Sniper Architecture [v3 Turbo Flip Edition]...")

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
