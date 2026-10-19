import html
import re

def generate_telegram_resale_post(lot, seller_contact="@твой_юзернейм"):
    """
    Generates a high-converting, beautifully formatted sales post
    ready for instant publication into Telegram resale channels.
    """
    trophies = lot.get("trophies", 0)
    brawlers = lot.get("brawlers", 0)
    primes = lot.get("primes", 0)
    est_price = lot.get("est_tg_price", round(lot.get("price", 200) * 2.2))
    has_mail = lot.get("has_firstmail", False)

    # Extract perks from triggers
    triggers = lot.get("triggers", [])
    perks = []
    for t in triggers:
        # Strip HTML tags
        clean_t = re.sub(r"<[^>]+>", "", t).replace("• ", "").strip()
        perks.append(f"• {clean_t}")

    perks_block = "\n".join(perks) if perks else "• Отличная прокачка и активный аккаунт"

    mail_security = "• Родная почта (Firstmail) с полным доступом\n• Смена почты и пароля на ваши данные" if has_mail else "• Полная перепривязка на вашу почту\n• Безопасная сделка"

    contact = seller_contact if seller_contact.startswith("@") else f"@{seller_contact}"

    post_content = (
        "🌟 BRAWL STARS | ТОПОВЫЙ АККАУНТ ПОД ОСНОВУ 🌟\n\n"
        f"🏆 Кубки: {trophies:,}\n"
        f"👤 Бравлеры: {brawlers} бойцов\n"
        f"⚡ Прокачка 11 LVL: {primes} праймов\n\n"
        "👑 ГЛАВНЫЕ ПЛЮСЫ И СКИНЫ:\n"
        f"{perks_block}\n\n"
        "🔒 БЕЗОПАСНОСТЬ И ПРИВЯЗКА:\n"
        f"{mail_security}\n"
        "• Никаких сторонних входов и бана\n\n"
        f"💵 ЦЕНА: {est_price} ₽ (быстрым скидка!)\n"
        "💳 Оплата: СБП / Тинькофф / Сбер / Крипта\n\n"
        f"📩 ДЛЯ ПОКУПКИ ПИСАТЬ: {contact}\n\n"
        "#brawlstars #бравлстарс #аккаунты #продажа"
    )

    return post_content
