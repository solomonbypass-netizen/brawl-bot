from telebot import types

def format_gold_message(lot, is_new_alert=False):
    title = "🚨 <b>НАЙДЕН ОКУПНОЙ АККАУНТ НА FUNPAY!</b>" if is_new_alert else "💰 <b>ОКУПНОЙ ЛОТ ПОД БЫСТРЫЙ ФЛИП:</b>"
    mail_badge = "🟢 <b>Родная почта (Firstmail)</b>" if lot.get("has_firstmail") else "🟡 <b>Почту уточнять у продавца</b>"
    
    triggers = lot.get("triggers", [])
    triggers_text = "\n".join([f"• {t}" for t in triggers])

    online_badge = lot.get("online_badge", "")
    online_line = f"\n{online_badge}" if online_badge else ""

    screenshots_cnt = len(lot.get("screenshots", []))
    screens_line = f"🖼️ <b>Скриншотов:</b> {screenshots_cnt} шт.\n" if screenshots_cnt > 0 else ""

    msg = (
        f"{title}\n\n"
        f"🎯 <b>ПОЧЕМУ ЭТО ОКУП:</b>\n"
        f"{triggers_text}\n\n"
        f"💵 <b>Цена на FunPay:</b> <code>{lot['price']:g} ₽</code>\n"
        f"📈 <b>Реальная продажа в ТГ:</b> ~<code>{lot['est_tg_price']} ₽</code>\n"
        f"🟢 <b>Твой чистый профит:</b> <b>+{lot['profit']} ₽</b>\n\n"
        f"🏆 <b>Кубков:</b> <b>{lot['trophies']:,}</b> | 👤 <b>Бравлеров:</b> <b>{lot['brawlers']}</b> | ⚡ <b>Праймов:</b> <b>{lot['primes']}</b>\n"
        f"{screens_line}"
        f"👤 <b>Продавец:</b> {lot['seller']} (⭐ <b>{lot['reviews']}</b> отзывов){online_line}\n"
        f"{mail_badge}\n\n"
        f"📝 <i>{lot['desc'][:115]}...</i>"
    )
    return msg

def make_lot_keyboard(href, screenshots=None):
    kb = types.InlineKeyboardMarkup()
    buttons = [types.InlineKeyboardButton(text="🔗 Забрать на FunPay", url=href)]
    if screenshots and len(screenshots) > 0:
        buttons.append(types.InlineKeyboardButton(text=f"🖼️ Скриншоты ({len(screenshots)})", url=screenshots[0]))
    kb.row(*buttons)
    return kb

def get_main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_flip = types.KeyboardButton("🚀 Найти окупные лоты прямо сейчас")
    btn_status = types.KeyboardButton("📊 Статус мониторинга")
    kb.add(btn_flip)
    kb.add(btn_status)
    return kb
