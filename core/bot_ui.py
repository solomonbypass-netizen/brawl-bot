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

    roi = lot.get("roi_percent", 0)
    roi_badge = f" (ROI: <b>+{roi}%</b>)" if roi > 0 else ""
    
    breakdown = lot.get("valuation_breakdown", "")
    breakdown_block = f"📊 <b>Калькуляция Оценщика:</b>\n<i>{breakdown}</i>\n\n" if breakdown else ""

    msg = (
        f"{title}\n\n"
        f"🎯 <b>ПОЧЕМУ ЭТО ОКУП (Анализ рынка):</b>\n"
        f"{triggers_text}\n\n"
        f"💵 <b>Цена на FunPay:</b> <code>{lot['price']:g} ₽</code>\n"
        f"📈 <b>Справедливая цена в ТГ:</b> ~<code>{lot['est_tg_price']} ₽</code>\n"
        f"🟢 <b>Твой чистый профит:</b> <b>+{lot['profit']} ₽</b>{roi_badge}\n\n"
        f"{breakdown_block}"
        f"🏆 <b>Кубков:</b> <b>{lot['trophies']:,}</b> | 👤 <b>Бравлеров:</b> <b>{lot['brawlers']}</b> | ⚡ <b>Праймов:</b> <b>{lot['primes']}</b>\n"
        f"{screens_line}"
        f"👤 <b>Продавец:</b> {lot['seller']} (⭐ <b>{lot['reviews']}</b> отзывов){online_line}\n"
        f"{mail_badge}\n\n"
        f"📝 <i>{lot['desc'][:115]}...</i>"
    )
    return msg

def make_lot_keyboard(href, screenshots=None, offer_id=None):
    """
    Constructs high-conversion lot actions:
    Row 1: Instant purchase link on FunPay
    Row 2: Resale marketing post generator + Album viewer
    Row 3: AI Video Montage + Viral Text Promo Pack
    """
    kb = types.InlineKeyboardMarkup()
    kb.row(types.InlineKeyboardButton(text="🔗 Забрать на FunPay", url=href))
    
    action_row = []
    if offer_id:
        action_row.append(types.InlineKeyboardButton(
            text="📢 Пост в ТГ", 
            callback_data=f"post:{offer_id}"
        ))

    if screenshots and len(screenshots) > 1 and offer_id:
        action_row.append(types.InlineKeyboardButton(
            text=f"📸 Все фото ({len(screenshots)})", 
            callback_data=f"scr:{offer_id}"
        ))
    elif screenshots and len(screenshots) == 1:
        action_row.append(types.InlineKeyboardButton(text="🖼️ Скриншот (1)", url=screenshots[0]))
        
    if action_row:
        kb.row(*action_row)

    if offer_id:
        kb.row(
            types.InlineKeyboardButton(
                text="🎥 Смонтировать видео (ИИ)",
                callback_data=f"video:{offer_id}"
            ),
            types.InlineKeyboardButton(
                text="🎬 Текст промо-пака",
                callback_data=f"promo:{offer_id}"
            )
        )

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

def get_settings_inline_keyboard(current_limit=1, current_budget=420):
    """
    Inline keyboard allowing user to select output quantity and budget ceiling.
    """
    kb = types.InlineKeyboardMarkup()
    
    # Row 1: Quantity Limits
    qty_row = []
    options = [(1, "1 лот"), (2, "2 лота"), (3, "3 лота"), (5, "5 лотов")]
    for count, label in options:
        text = f"✅ {label}" if count == current_limit else label
        qty_row.append(types.InlineKeyboardButton(text=text, callback_data=f"setlim:{count}"))
    kb.row(*qty_row)

    # Row 2: Budget filters
    budget_row = []
    budgets = [(200, "до 200 ₽"), (300, "до 300 ₽"), (420, "Все до 420 ₽")]
    for b_val, b_label in budgets:
        b_text = f"✅ {b_label}" if b_val == current_budget else b_label
        budget_row.append(types.InlineKeyboardButton(text=b_text, callback_data=f"setbdg:{b_val}"))
    kb.row(*budget_row)

    return kb
