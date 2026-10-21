from telebot import types

def format_gold_message(lot, is_new_alert=False):
    """
    Constructs the exact 5-point evaluation report card for HIGH and GOD TIER accounts:
    1. Found ID & Direct link to Brawlify / Brawl Time Ninja
    2. Ready valuation / Account score from the site
    3. Marketplace price vs Real fair market value
    4. Key asset value (Exclusive skins / Hypercharges / Rank)
    5. Detailed analytical verdict on why this lot must be bought
    """
    tier = lot.get("tier", "HIGH TIER")
    if "GOD" in tier:
        header = "👑 <b>[GOD TIER / SNIPE TARGET] 🎯 МГНОВЕННЫЙ ВЫКУП!</b>"
    else:
        header = "💎 <b>[HIGH TIER] 🔥 ТОПОВЫЙ ЛОТ ПОД ВЫКУП</b>"

    if is_new_alert:
        header = f"🚨 <b>НОВЫЙ ОКУПНОЙ ЛОТ НА FUNPAY!</b>\n{header}"

    player_tag = lot.get("player_tag", "Скрыт на фото и в описании")
    brawlify_url = lot.get("brawlify_url") or "https://brawlify.com"
    brawltime_url = lot.get("brawltime_url") or "https://brawltime.ninja"
    
    links_block = (
        f"• <b>Brawlify:</b> <a href=\"{brawlify_url}\">{brawlify_url}</a>\n"
        f"• <b>Brawl Time Ninja:</b> <a href=\"{brawltime_url}\">{brawltime_url}</a>"
    )

    site_score = lot.get("site_score", "Account Value: Авто-анализ по базе")
    roi = lot.get("roi_percent", 0)
    key_values = lot.get("key_values", "• Базовый боевой ростер")
    verdict = lot.get("verdict", "Высокая ликвидность для безопасного флипа.")

    mail_badge = "🟢 Родная почта (Firstmail)" if lot.get("has_firstmail") else "🟡 Почту уточнять у продавца"
    online_badge = lot.get("online_badge", "")
    online_line = f" | {online_badge}" if online_badge else ""

    est_tg_price = lot.get("est_tg_price", round(lot.get("price", 200) * 2.2))
    profit = lot.get("profit", est_tg_price - lot.get("price", 0))

    msg = (
        f"{header}\n\n"
        f"1️⃣ <b>АЙДИ ИГРОКА & ССЫЛКИ НА СТАТИСТИКУ:</b>\n"
        f"• <b>Тег игрока:</b> <code>{player_tag}</code>\n"
        f"{links_block}\n\n"
        f"2️⃣ <b>ОЦЕНКА СТОИМОСТИ САЙТА:</b>\n"
        f"⭐ <i>{site_score}</i>\n\n"
        f"3️⃣ <b>ЦЕНА VS РЕАЛЬНАЯ СТОИМОСТЬ:</b>\n"
        f"💵 <b>Цена на FunPay:</b> <code>{lot['price']:g} ₽</code>\n"
        f"📈 <b>Реальная рыночная цена:</b> ~<code>{est_tg_price} ₽</code>\n"
        f"🟢 <b>Чистый профит:</b> <b>+{profit} ₽</b> (ROI: <b>+{roi}%</b>)\n\n"
        f"4️⃣ <b>ГЛАВНАЯ ЦЕННОСТЬ АККАУНТА:</b>\n"
        f"{key_values}\n\n"
        f"5️⃣ <b>ВЕРДИКТ (ПОЧЕМУ НАДО КУПИТЬ):</b>\n"
        f"{verdict}\n\n"
        f"🔒 <b>Сделка:</b> {mail_badge}\n"
        f"👤 <b>Продавец:</b> {lot['seller']} (⭐ <b>{lot['reviews']}</b> отзывов){online_line}"
    )
    return msg

def make_lot_keyboard(href, screenshots=None, offer_id=None, brawlify_url=None, brawltime_url=None):
    """
    Constructs high-conversion lot actions:
    Row 1: Instant purchase link on FunPay
    Row 2: Instant profile statistics links (Brawlify + Brawl Time Ninja)
    Row 3: Resale marketing post generator + Album viewer
    Row 4: AI Video Montage + Viral Text Promo Pack
    """
    kb = types.InlineKeyboardMarkup()
    kb.row(types.InlineKeyboardButton(text="🔗 Забрать на FunPay", url=href))

    # Row 2: Instant Profile Stats buttons!
    profile_row = []
    if brawlify_url and "http" in brawlify_url:
        profile_row.append(types.InlineKeyboardButton(text="🌐 Brawlify Профиль", url=brawlify_url))
    if brawltime_url and "http" in brawltime_url:
        profile_row.append(types.InlineKeyboardButton(text="⚔️ Brawl Time Ninja", url=brawltime_url))
    if profile_row:
        kb.row(*profile_row)
    
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
