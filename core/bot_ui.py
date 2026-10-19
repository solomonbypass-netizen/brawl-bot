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

def make_lot_keyboard(href, screenshots=None, offer_id=None):
    kb = types.InlineKeyboardMarkup()
    buttons = [types.InlineKeyboardButton(text="🔗 Забрать на FunPay", url=href)]
    
    if screenshots and len(screenshots) > 1 and offer_id:
        buttons.append(types.InlineKeyboardButton(
            text=f"📸 Все фото в чат ({len(screenshots)})", 
            callback_data=f"scr:{offer_id}"
        ))
    elif screenshots and len(screenshots) == 1:
        buttons.append(types.InlineKeyboardButton(text="🖼️ Скриншот (1)", url=screenshots[0]))
        
    kb.row(*buttons)
    return kb

def get_main_keyboard(current_limit=1):
    """
    Creates dynamic main reply keyboard reflecting current user limit.
    Offers instant 1-tap shortcuts for 1 and 2 lots.
    """
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_one = types.KeyboardButton("⚡ 1 лучший лот")
    btn_two = types.KeyboardButton("🚀 2 лучших лота")
    btn_settings = types.KeyboardButton(f"⚙️ Лимит: {current_limit} шт.")
    btn_status = types.KeyboardButton("📊 Статус")
    
    kb.row(btn_one, btn_two)
    kb.row(btn_settings, btn_status)
    return kb

def get_settings_inline_keyboard(current_limit=1):
    """
    Inline keyboard allowing user to select default output quantity (1, 2, 3, 5).
    """
    kb = types.InlineKeyboardMarkup(row_width=4)
    buttons = []
    options = [(1, "1 лот"), (2, "2 лота"), (3, "3 лота"), (5, "5 лотов")]
    for count, label in options:
        text = f"✅ {label}" if count == current_limit else label
        buttons.append(types.InlineKeyboardButton(text=text, callback_data=f"setlim:{count}"))
    kb.row(*buttons)
    return kb
