import re

OG_SKINS = [
    "звездная шелли", "star shelly", "шелли 2018", "2018", "2019", "корсар кольт",
    "рикошет", "вирус 8-бит", "вирус", "ведьма шелли", "оборотень леон",
    "торговец гейл", "паладин вольт", "майк портье", "хэллоуин", "олд акк"
]

SPAM_KEYWORDS = [
    "договорная", "цена в лс", "писать в лс", "в лс", "не покупать", 
    "куплю", "обмен", "тест", "витрина", "предлагайте", "предлагать", 
    "цена договор", "договор", "отзыв", "пустышка", "минус", "-гем", "отрицательн"
]

BP_REGEX = re.compile(r"(?:бп\+|brawl\s*pass\+|бравл\s*пасс\+|куплен\s*бп)", re.IGNORECASE)
SKINS_COUNT_REGEX = re.compile(r"(\d{2,3})\s*скин", re.IGNORECASE)
PATTERN_STATS = re.compile(r"(\d+)\s*кубк\w*,\s*(\d+)\s*бравлер\w*(?:,\s*(\d+)\s*прайм\w*)?", re.IGNORECASE)

def extract_exact_rub_price(price_el):
    """
    Extracts the true price in RUB using FunPay's internal data-s attribute.
    Falls back to text with currency conversion if attribute missing.
    """
    if not price_el:
        return 0.0
    data_s = price_el.get("data-s")
    if data_s:
        try:
            val = float(data_s)
            if val > 0:
                return round(val, 2)
        except ValueError:
            pass

    text = price_el.get_text(strip=True)
    cleaned = re.sub(r"[^\d.]", "", text.replace(" ", "").replace(",", "."))
    try:
        val = float(cleaned)
    except ValueError:
        return 0.0

    if "$" in text or "usd" in text.lower():
        return round(val * 95.0, 2)
    elif "€" in text or "eur" in text.lower():
        return round(val * 105.0, 2)

    return round(val, 2)

def extract_real_gem_balance(desc_lower):
    """
    Extracts true wallet balance of gems (50 to 500).
    Filters out 'скины на 4800 gems', '(на 4000 гемов)', negative balance, and fake values.
    """
    if re.search(r"-\s*\d+\s*(?:гем|gem)", desc_lower) or "минус" in desc_lower or "отрицательн" in desc_lower:
        return -1

    cleaned = re.sub(r"(?:скин\w*|skin\w*|вещ\w*)\s*(?:на|за|около|стоимостью|≈|~|\+|-)?\s*\d+\s*(?:к|k)?\s*(?:гем\w*|gem\w*)", "", desc_lower)
    cleaned = re.sub(r"\(\s*(?:на|за)\s*\d+\s*(?:к|k)?\s*(?:гем\w*|gem\w*)\s*\)", "", cleaned)
    cleaned = re.sub(r"\bна\s*\d{3,5}\s*(?:гем\w*|gem\w*)", "", cleaned)
    cleaned = re.sub(r"≈\s*\d+\s*(?:к|k)?\s*(?:гем\w*|gem\w*)", "", cleaned)

    match = re.search(r"\b(\d{2,3})\s*(?:гем\w*|gem\w*)", cleaned)
    if match:
        val = int(match.group(1))
        if 50 <= val <= 500:
            return val
    return 0

def analyze_lot_liquidity(lot_dict):
    """
    Evaluates real market liquidity and profit margin in Telegram resale.
    Returns: (is_liquid, triggers_list, est_tg_price, profit)
    """
    price = lot_dict["price"]
    desc_lower = lot_dict["desc"].lower()
    brawlers = lot_dict["brawlers"]
    primes = lot_dict["primes"]
    trophies = lot_dict["trophies"]

    # 1. Real Gem Balance check
    real_gems = extract_real_gem_balance(desc_lower)
    if real_gems == -1:
        return False, [], 0, 0

    triggers = []
    est_tg_price = 0

    # 2. OG / Exclusive Skins check
    found_og = [s for s in OG_SKINS if s in desc_lower]
    if found_og and price <= 420:
        triggers.append(f"👑 <b>OG-раритет:</b> {found_og[0].upper()}")
        est_tg_price = max(est_tg_price, 950)

    # 3. Legitimate Gems Wallet Balance
    if real_gems >= 70 and price <= 380:
        triggers.append(f"💎 <b>Баланс на счете:</b> {real_gems} гемов")
        est_tg_price = max(est_tg_price, 750 + int(real_gems * 1.5))

    # 4. Brawl Pass+ purchased
    if bool(BP_REGEX.search(desc_lower)) and price <= 400:
        triggers.append("🎟️ <b>Куплен Brawl Pass+</b>")
        est_tg_price = max(est_tg_price, 850)

    # 5. True Skin collections (70+ skins)
    skins_match = SKINS_COUNT_REGEX.search(desc_lower)
    if skins_match:
        skins_cnt = int(skins_match.group(1))
        if 70 <= skins_cnt <= 300 and price <= 380:
            triggers.append(f"🎨 <b>Коллекция:</b> {skins_cnt} скинов")
            est_tg_price = max(est_tg_price, 1000)

    # 6. High brawler unlock disparity (78+ characters at <= 360 RUB)
    if brawlers >= 78 and price <= 360:
        triggers.append(f"👤 <b>Фулл-ростер:</b> {brawlers} бравлеров")
        est_tg_price = max(est_tg_price, 850)

    # 7. Maxed 11-level powers
    if primes >= 14 and price <= 360:
        triggers.append(f"⚡ <b>Готовая основа:</b> {primes} бойцов (11 LVL)")
        est_tg_price = max(est_tg_price, 850)

    # 8. Fast-flip trophy floor: 25k+ trophies, 70+ brawlers at <= 260 RUB
    if trophies >= 25000 and brawlers >= 70 and price <= 260:
        triggers.append(f"🔥 <b>Срочный сброс:</b> 25k+ кубков всего за {price:g}₽")
        est_tg_price = max(est_tg_price, 750)

    if not triggers:
        return False, [], 0, 0

    est_tg_price = min(max(est_tg_price, 650), 1400)
    profit = est_tg_price - price

    if profit >= 350 and price <= 420:
        return True, triggers, round(est_tg_price), round(profit)

    return False, [], 0, 0
