import re
import logging

logger = logging.getLogger("ValuationGuru")

# =====================================================================
# 1. TIER S+ & TIER S: UNTOUCHABLE LEGACY EXCLUSIVES (2018-2020)
# These never return to the shop under any circumstances.
# =====================================================================
OG_TIER_S_PLUS = {
    "челленджер кольт": 550, "challenger colt": 550, "кольт чемпион": 550,
    "звездная шелли": 400, "star shelly": 400, "шелли 2018": 400
}

OG_TIER_S = {
    "вирус 8-бит": 300, "virus 8-bit": 300,
    "рикошет": 180, "ricochet": 180,
    "корсар кольт": 160, "corsair colt": 160,
    "сантамайк": 150, "santa mike": 150,
    "ведьма шелли": 160, "witch shelly": 160,
    "оборотень леон": 170, "werewolf leon": 170
}

# =====================================================================
# 2. TIER A: RETIRED BRAWL PASS EXCLUSIVES (SEASONS 1-10)
# Officially confirmed by Supercell to NEVER return to the shop.
# =====================================================================
OG_TIER_A = {
    "торговец гейл": 280, "merchant gale": 280,
    "трикси колетт": 320, "trixie colette": 320, "малефисента колетт": 300,
    "паладин вольт": 220, "mecha paladin surge": 220, "паладин": 200,
    "король лу": 180, "king lou": 180,
    "ронин гавс": 180, "ronin ruffs": 180,
    "белль золоторучка": 160, "goldhand belle": 160,
    "майор роза": 160, "major rosa": 160,
    "принцесса шелли": 200, "princess shelly": 200,
    "ниндзя эш": 180, "ninja ash": 180,
    "бунтарь вольт": 160, "rebel lola": 160,
    "майк портье": 160, "bellhop mike": 160,
    "d4r-ry1": 150, "дэрил d4r-ry1": 150
}

# =====================================================================
# 3. TRAP SKINS & WORTHLESS ILLUSIONS (0 RUB ADDON)
# Market traps that cost coins/freebies but add zero resale value in TG
# =====================================================================
FALSE_OG_TRAPS = [
    "варвар", "варварский король", "barbarian king",
    "красный дракон", "red dragon", "джесси дракон",
    "серебрян", "золотой скин", "true silver", "true gold",
    "бандит кольт", "звездный шериф"
]

BP_REGEX = re.compile(r"(?:бп\+|brawl\s*pass\+|бравл\s*пасс\+|куплен\s*бп)", re.IGNORECASE)
SKINS_COUNT_REGEX = re.compile(r"(\d{2,3})\s*скин", re.IGNORECASE)

# Ranked League: Master / Legendary (Strict context to avoid 'мастерство' confusion)
RANKED_MASTERS_REGEX = re.compile(
    r"(?:рангов\w*(?:\s*бо[яеий]\w*)?|лиг\w*)\s*(?:мастер|легенд\w*)|ранг\s*мастер\b|лига\s*мастер|\bмастер\s*лиг\w*", 
    re.IGNORECASE
)

# Veteran Registration Account Date (2018-2019)
VETERAN_YEAR_REGEX = re.compile(r"\b(2018|2019)\s*(?:год|г\b|года)?", re.IGNORECASE)

def extract_real_gems(desc_lower):
    """
    Extracts authentic wallet gems (50 to 500).
    Filters out skin appraisals ('скины на 4800 gems') and negative debt balances.
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

def calculate_brawl_fair_valuation(lot_dict):
    """
    Deep Market Intelligence Valuation Engine (Cycle 5).
    Incorporates:
      1. Base foundation (Trophies + Brawlers unlocked out of 84+)
      2. Power 11 Primes & Hypercharges
      3. Strict 1:1 Gem valuation (0.95-1.0 RUB/gem)
      4. Tier S+ (Challenger Colt, Star Shelly) & Tier S (Legacy OG 2018-2020)
      5. Tier A (Retired Brawl Pass 1-10 Seasons)
      6. Trap filter: True Silver/Gold and free giveaway skins ignored
      7. Ranked Status: Masters / Legendary prestige
      8. Veteran registration check (2018-2019)
      9. Security Multiplier (Firstmail vs Unverified)
    Returns: (is_approved, est_tg_price, profit, roi_percent, triggers, breakdown_summary)
    """
    price = lot_dict["price"]
    desc_lower = lot_dict["desc"].lower()
    brawlers = lot_dict.get("brawlers", 0)
    primes = lot_dict.get("primes", 0)
    trophies = lot_dict.get("trophies", 0)
    has_firstmail = lot_dict.get("has_firstmail", False)

    # Instant rejection: Scam / Negative gems / Price out of flipping scope
    real_gems = extract_real_gems(desc_lower)
    if real_gems == -1:
        return False, 0, 0, 0, [], "Отрицательный баланс гемов (СКАМ)"
    if price < 70 or price > 450:
        return False, 0, 0, 0, [], "Цена вне диапазона арбитража"

    triggers = []
    notes = []

    # --- 1. BASE VALUE (Trophies + Brawlers) ---
    if trophies >= 50000:
        base_val = 750
        triggers.append(f"🏆 <b>Киберспорт кубки:</b> {trophies:,}")
        notes.append("Кубки 50k+ (750₽)")
    elif trophies >= 35000:
        base_val = 450
        triggers.append(f"🏆 <b>Высокие кубки:</b> {trophies:,}")
        notes.append("Кубки 35k-50k (450₽)")
    elif trophies >= 25000:
        base_val = 280
        triggers.append(f"🏆 <b>База основы:</b> {trophies:,} куб.")
        notes.append("Кубки 25k-35k (280₽)")
    elif trophies >= 15000:
        base_val = 170
        notes.append("Кубки 15k-25k (170₽)")
    else:
        base_val = 90
        notes.append("Кубки <15k (90₽)")

    # Brawler count adjustment
    if brawlers >= 82:
        base_val += 160
        triggers.append(f"👤 <b>Фулл-ростер:</b> {brawlers} бойцов")
        notes.append("Фулл-ростер (+160₽)")
    elif brawlers >= 75:
        base_val += 80
        triggers.append(f"👤 <b>Бойцов:</b> {brawlers}")
        notes.append("Ростер 75+ (+80₽)")
    elif brawlers < 55 and trophies < 20000:
        base_val = max(50, base_val - 40)
        notes.append("Мало бойцов (-40₽)")

    # --- 2. POWER 11 PRIMES ---
    primes_val = 0
    if primes >= 20:
        primes_val = 250
        triggers.append(f"⚡ <b>Ультра-прокачка:</b> {primes} праймов (11 LVL)")
        notes.append(f"20+ праймов (+250₽)")
    elif primes >= 12:
        primes_val = 140
        triggers.append(f"⚡ <b>Прокачка 11 LVL:</b> {primes} бойцов")
        notes.append(f"12-19 праймов (+140₽)")
    elif primes >= 6:
        primes_val = 60
        notes.append(f"6-11 праймов (+60₽)")

    # --- 3. GEMS FAIR VALUATION (Strict ~0.95 RUB per gem) ---
    gems_val = 0
    if real_gems >= 50:
        gems_val = round(real_gems * 0.95)
        triggers.append(f"💎 <b>Чистый баланс:</b> {real_gems} гемов (+{gems_val}₽)")
        notes.append(f"Гемы {real_gems} шт. (+{gems_val}₽)")

    # --- 4. EXCLUSIVE & OG SKINS (With Trap Disqualification) ---
    skins_val = 0

    # Tier S+ (Holy Grail: Challenger Colt, Star Shelly)
    found_tier_s_plus = None
    for name, val in OG_TIER_S_PLUS.items():
        if name in desc_lower:
            found_tier_s_plus = (name, val)
            break

    if found_tier_s_plus:
        skins_val += found_tier_s_plus[1]
        triggers.append(f"👑 <b>Святой Грааль:</b> {found_tier_s_plus[0].upper()} (+{found_tier_s_plus[1]}₽)")
        notes.append(f"OG S+ {found_tier_s_plus[0]} (+{found_tier_s_plus[1]}₽)")

    # Tier S (2018-2020 Archive)
    found_tier_s = None
    for name, val in OG_TIER_S.items():
        if name in desc_lower:
            found_tier_s = (name, val)
            break

    if found_tier_s and not found_tier_s_plus:
        skins_val += found_tier_s[1]
        triggers.append(f"👑 <b>OG Tier S:</b> {found_tier_s[0].upper()} (+{found_tier_s[1]}₽)")
        notes.append(f"OG {found_tier_s[0]} (+{found_tier_s[1]}₽)")

    # Tier A (Brawl Pass Seasons 1-10 Retired Exclusives)
    found_tier_a = None
    for name, val in OG_TIER_A.items():
        if name in desc_lower:
            found_tier_a = (name, val)
            break

    if found_tier_a and not found_tier_s and not found_tier_s_plus:
        skins_val += found_tier_a[1]
        triggers.append(f"✨ <b>БП Эксклюзив (Сезоны 1-10):</b> {found_tier_a[0].capitalize()} (+{found_tier_a[1]}₽)")
        notes.append(f"BP {found_tier_a[0]} (+{found_tier_a[1]}₽)")

    # Skin count
    skins_match = SKINS_COUNT_REGEX.search(desc_lower)
    if skins_match:
        cnt = int(skins_match.group(1))
        if 70 <= cnt <= 300:
            add_s = min(220, int(cnt * 1.5))
            skins_val += add_s
            triggers.append(f"🎨 <b>Коллекция скинов:</b> {cnt} шт.")
            notes.append(f"{cnt} скинов (+{add_s}₽)")

    # Active Brawl Pass+
    if bool(BP_REGEX.search(desc_lower)):
        skins_val += 150
        triggers.append("🎟️ <b>Куплен Brawl Pass+</b> (+150₽)")
        notes.append("Brawl Pass+ (+150₽)")

    # --- 5. COMPETITIVE RANK PRESTIGE & VETERAN AGE ---
    rank_val = 0
    if RANKED_MASTERS_REGEX.search(desc_lower):
        rank_val = 180
        triggers.append("🎖️ <b>Ранговый статус: МАСТЕР</b> (+180₽)")
        notes.append("Мастер лиги (+180₽)")

    veteran_match = VETERAN_YEAR_REGEX.search(desc_lower)
    if veteran_match and (found_tier_s_plus or found_tier_s or trophies >= 20000):
        # Validated veteran registration
        rank_val += 70
        triggers.append(f"🕰️ <b>Олд-аккаунт ({veteran_match.group(1)} г.)</b> (+70₽)")
        notes.append(f"Олд {veteran_match.group(1)} (+70₽)")

    # --- 6. SAFETY MULTIPLIER ---
    raw_est = base_val + primes_val + gems_val + skins_val + rank_val
    safety_factor = 1.0 if has_firstmail else 0.80

    if not has_firstmail:
        notes.append("Риск почты (-20%)")
    else:
        notes.append("Родная почта 100%")

    est_tg_price = round((raw_est * safety_factor) / 10) * 10
    est_tg_price = max(150, min(est_tg_price, 1600))

    profit = est_tg_price - price
    roi_percent = round((profit / price) * 100) if price > 0 else 0

    breakdown_summary = " | ".join(notes)

    # --- 7. GURU'S STRICT VERDICT ---
    # Must have minimum ROI >= 60% AND net profit >= 260 RUB,
    # OR net profit >= 350 RUB regardless of ROI.
    is_approved = (
        (profit >= 260 and roi_percent >= 60 and price <= 420) or
        (profit >= 350 and price <= 420)
    )

    return is_approved, est_tg_price, profit, roi_percent, triggers, breakdown_summary
