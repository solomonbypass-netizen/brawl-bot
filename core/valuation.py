import re
import html
import urllib.parse
import logging

logger = logging.getLogger("ValuationGuru")

# =====================================================================
# 1. TIER S+ & TIER S: UNTOUCHABLE LEGACY EXCLUSIVES (2018-2020)
# These never return to the shop under any circumstances.
# =====================================================================
OG_TIER_S_PLUS = {
    "челленджер кольт": 550, "challenger colt": 550, "кольт чемпион": 550,
    "звездная шелли": 450, "star shelly": 450, "шелли 2018": 450, "стар шелли": 450
}

OG_TIER_S = {
    "вирус 8-бит": 350, "virus 8-bit": 350, "вирус 8 бит": 350,
    "рикошет": 200, "ricochet": 200,
    "корсар кольт": 180, "corsair colt": 180,
    "сантамайк": 170, "santa mike": 170,
    "ведьма шелли": 180, "witch shelly": 180,
    "оборотень леон": 190, "werewolf leon": 190
}

# =====================================================================
# 2. TIER A: RETIRED BRAWL PASS EXCLUSIVES (SEASONS 1-10, PRE-2023)
# Officially confirmed by Supercell to NEVER return to the shop.
# =====================================================================
OG_TIER_A = {
    "трикси колетт": 350, "trixie colette": 350, "малефисента колетт": 300,
    "паладин вольт": 260, "mecha paladin surge": 260, "паладин": 240,
    "торговец гейл": 280, "merchant gale": 280,
    "король лу": 200, "king lou": 200,
    "ронин гавс": 200, "ronin ruffs": 200,
    "белль золоторучка": 180, "goldhand belle": 180,
    "майор роза": 180, "major rosa": 180,
    "принцесса шелли": 220, "princess shelly": 220,
    "ниндзя эш": 190, "ninja ash": 190,
    "бунтарь лола": 170, "rebel lola": 170,
    "плохой парень базз": 200, "born bad buzz": 200,
    "майк портье": 170, "bellhop mike": 170,
    "d4r-ry1": 160, "дэрил d4r-ry1": 160
}

# =====================================================================
# 3. TRAP SKINS & WORTHLESS ILLUSIONS (0 RUB ADDON)
# Market traps that cost coins/freebies but add zero resale value
# =====================================================================
FALSE_OG_TRAPS = [
    "варвар", "варварский король", "barbarian king",
    "красный дракон", "red dragon", "джесси дракон",
    "серебрян", "золотой скин", "true silver", "true gold",
    "бандит кольт", "звездный шериф"
]

# Regex patterns for deep extraction
TAG_REGEX = re.compile(r"#[0289PYLQGRJCUVa-z]{4,12}", re.IGNORECASE)
TAG_INDIRECT_REGEX = re.compile(r"(?:тег|tag|айди|id|player\s*tag)[\s:#]+([0289PYLQGRJCUV]{4,12})\b", re.IGNORECASE)
NICK_REGEX = re.compile(r"(?:ник|никнейм|nickname|player|ник\s*в\s*игре)[\s:]+([a-zA-Z0-9_\-\.]{2,20})", re.IGNORECASE)
SITE_SCORE_REGEX = re.compile(r"(?:account\s*value|account\s*score|оценка\s*(?:сайта|аккаунта|профиля)|рейтинг\s*(?:сайта|профиля)|тир-лист|brawlify\s*score)[\s:]*([^\n,;|]+)", re.IGNORECASE)

BP_REGEX = re.compile(r"(?:бп\+|brawl\s*pass\+|бравл\s*пасс\+|куплен\s*бп)", re.IGNORECASE)
SKINS_COUNT_REGEX = re.compile(r"(\d{2,3})\s*скин", re.IGNORECASE)
HYPERCHARGE_REGEX = re.compile(r"(\d+)\s*(?:гиперзаряд|гипер|hypercharge)", re.IGNORECASE)
WINS_3V3_REGEX = re.compile(r"(\d+)\s*(?:побед\s*3х3|побед\s*3x3|3v3\s*wins|3х3)", re.IGNORECASE)
REG_YEAR_REGEX = re.compile(r"\b(2018|2019|2020|2021|2022|2023|2024|2025|2026)\s*(?:год|г\b|года)?", re.IGNORECASE)

# Ranked League: Master / Legendary
RANKED_MASTERS_REGEX = re.compile(
    r"(?:рангов\w*(?:\s*бо[яеий]\w*)?|лиг\w*)\s*(?:мастер|легенд\w*)|ранг\s*мастер\b|лига\s*мастер|\bмастер\s*лиг\w*|\bлегенда\s*лиг\w*", 
    re.IGNORECASE
)

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

def extract_player_tag_and_profile(desc, detailed_desc=""):
    """
    Step 1: Identifies Player Tag (#) or player nickname for verification.
    Returns: (player_tag, brawlify_url, brawltime_url, is_verified_tag)
    """
    full_text = f"{desc} {detailed_desc}".strip()
    
    # 1. Direct tag starting with #
    match = TAG_REGEX.search(full_text)
    if match:
        tag = match.group(0).upper()
        clean = tag.lstrip("#")
        return tag, f"https://brawlify.com/stats/profile/{clean}", f"https://brawltime.ninja/profile/{clean}", True

    # 2. Tag labeled with words ID/TAG
    match_indirect = TAG_INDIRECT_REGEX.search(full_text)
    if match_indirect:
        clean = match_indirect.group(1).upper()
        tag = f"#{clean}"
        return tag, f"https://brawlify.com/stats/profile/{clean}", f"https://brawltime.ninja/profile/{clean}", True

    # 3. Fallback: Nickname for Brawlify search
    match_nick = NICK_REGEX.search(full_text)
    if match_nick:
        nick = match_nick.group(1).strip()
        encoded = urllib.parse.quote(nick)
        return f"Ник: {nick}", f"https://brawlify.com/stats/search?q={encoded}", None, False

    return None, None, None, False

def extract_site_score(desc, detailed_desc=""):
    """
    Step 2: Detects ready automated site evaluation (Account Value, Score, Rating).
    """
    full_text = f"{desc} {detailed_desc}"
    match = SITE_SCORE_REGEX.search(full_text)
    if match:
        return match.group(1).strip()
    return None

def calculate_brawl_fair_valuation(lot_dict):
    """
    Automated AI Valuation Engine (Steps 1, 2, 3):
    1. Identification of Player Tag / Verification
    2. Extraction of Site Evaluation (Account Value / Score) & Unconditional Trust
    3. Mathematical Categorization:
       - GOD TIER / SNIPE TARGET: Star Shelly, Pre-2023 OG, High Site Score + Low Price.
       - HIGH TIER: Master/Legendary, 15+ Power 11 with hypercharges, 50k+ cups.
       - LOW TIER / МУСОР: Complete silent disqualification (0 notifications).
    Returns: (is_approved, est_tg_price, profit, roi_percent, triggers, breakdown_summary, evaluation_meta)
    """
    price = lot_dict["price"]
    desc = lot_dict.get("desc", "")
    detailed_desc = lot_dict.get("detailed_desc", "")
    desc_lower = f"{desc} {detailed_desc}".lower()
    
    trophies = lot_dict.get("trophies", 0)
    primes = lot_dict.get("primes", 0)
    has_firstmail = lot_dict.get("has_firstmail", False)

    # -------------------------------------------------------------
    # INSTANT DISQUALIFICATION (SCAM / INVALID PRICE SCOPE)
    # -------------------------------------------------------------
    real_gems = extract_real_gems(desc_lower)
    if real_gems == -1:
        return False, 0, 0, 0, [], "Отрицательный баланс гемов (СКАМ)", None

    if price < 70 or price > 600:
        return False, 0, 0, 0, [], "Цена вне диапазона арбитража", None

    # Step 1: Player Tag Identification
    player_tag, brawlify_url, brawltime_url, is_verified_tag = extract_player_tag_and_profile(desc, detailed_desc)
    
    # Step 2: Site Automated Score
    site_score_text = extract_site_score(desc, detailed_desc)

    # Extract hypercharges
    hypercharges = 0
    hc_match = HYPERCHARGE_REGEX.search(desc_lower)
    if hc_match:
        hypercharges = int(hc_match.group(1))

    # Extract 3v3 wins
    wins_3v3 = 0
    wins_match = WINS_3V3_REGEX.search(desc_lower)
    if wins_match:
        wins_3v3 = int(wins_match.group(1))

    # Registration Year
    reg_year = None
    year_match = REG_YEAR_REGEX.search(desc_lower)
    if year_match:
        reg_year = int(year_match.group(1))

    # Master / Legendary Ranked Mode
    is_master = bool(RANKED_MASTERS_REGEX.search(desc_lower))

    # -------------------------------------------------------------
    # DETECT EXCLUSIVE OG PRE-2023 SKINS (NO TRAPS)
    # -------------------------------------------------------------
    og_skins_found = []
    og_value_bonus = 0

    # Tier S+ (Star Shelly, Challenger Colt)
    for name, val in OG_TIER_S_PLUS.items():
        if name in desc_lower:
            og_skins_found.append(f"👑 {name.upper()} (+{val}₽)")
            og_value_bonus += val
            break

    # Tier S (Virus 8-Bit, Ricochet, Santa Mike, Werewolf Leon, etc.)
    for name, val in OG_TIER_S.items():
        if name in desc_lower:
            og_skins_found.append(f"👑 {name.upper()} (+{val}₽)")
            og_value_bonus += val
            break

    # Tier A (Trixie Colette, Mecha Paladin Surge, Seasons 1-10 Brawl Pass)
    for name, val in OG_TIER_A.items():
        if name in desc_lower:
            og_skins_found.append(f"✨ {name.capitalize()} (+{val}₽)")
            og_value_bonus += val
            break

    # Has holy grail or pre-2023 exclusive
    has_pre_2023_og = len(og_skins_found) > 0 or (reg_year in [2018, 2019] and trophies >= 20000)

    # -------------------------------------------------------------
    # BASE FAIR VALUATION CALCULATION (Rule: Ignore legendary brawlers count)
    # -------------------------------------------------------------
    triggers = []
    notes = []

    # Trust site valuation unconditionally if present
    base_site_val = 0
    if site_score_text:
        # Extract number if in rubles or gem value
        score_num_match = re.search(r"(\d+)", site_score_text)
        if score_num_match:
            base_site_val = int(score_num_match.group(1))
            if "gem" in site_score_text.lower() or "гем" in site_score_text.lower():
                base_site_val = round(base_site_val * 0.95)

    if base_site_val >= 400:
        base_val = base_site_val
        triggers.append(f"🌐 <b>Авто-оценка сайта (100% доверие):</b> {site_score_text} (~{base_site_val}₽)")
        notes.append(f"Оценка сайта ({base_site_val}₽)")
    else:
        # Algorithmic foundation
        if trophies >= 50000:
            base_val = 750
            triggers.append(f"🏆 <b>Киберспорт кубки:</b> {trophies:,}")
            notes.append("Кубки 50k+ (750₽)")
        elif trophies >= 40000:
            base_val = 520
            triggers.append(f"🏆 <b>Топ кубки:</b> {trophies:,}")
            notes.append("Кубки 40k-50k (520₽)")
        elif trophies >= 30000:
            base_val = 350
            triggers.append(f"🏆 <b>База:</b> {trophies:,} куб.")
            notes.append("Кубки 30k-40k (350₽)")
        elif trophies >= 20000:
            base_val = 220
            notes.append("Кубки 20k-30k (220₽)")
        else:
            base_val = 110
            notes.append("Кубки <20k (110₽)")

    # Power 11 Primes & Hypercharges
    primes_val = 0
    if primes >= 20 or hypercharges >= 12:
        primes_val = 280
        triggers.append(f"⚡ <b>Ультра-прокачка:</b> {primes} праймов, {hypercharges} гиперзарядов")
        notes.append(f"20+ праймов/гиперов (+280₽)")
    elif primes >= 15 or hypercharges >= 8:
        primes_val = 180
        triggers.append(f"⚡ <b>Фулл 11 LVL:</b> {primes} праймов, {hypercharges} гиперов")
        notes.append(f"15+ праймов (+180₽)")
    elif primes >= 8:
        primes_val = 90
        notes.append(f"8-14 праймов (+90₽)")

    # Clean wallet gems
    gems_val = 0
    if real_gems >= 50:
        gems_val = round(real_gems * 0.95)
        triggers.append(f"💎 <b>Чистый баланс:</b> {real_gems} гемов (+{gems_val}₽)")
        notes.append(f"Гемы {real_gems} шт. (+{gems_val}₽)")

    # Skins value
    skins_val = og_value_bonus
    for og_s in og_skins_found:
        triggers.append(og_s)
        notes.append(og_s)

    # Active Brawl Pass+
    if bool(BP_REGEX.search(desc_lower)):
        skins_val += 150
        triggers.append("🎟️ <b>Куплен Brawl Pass+</b> (+150₽)")
        notes.append("Brawl Pass+ (+150₽)")

    # Ranked Master / Legendary
    rank_val = 0
    if is_master:
        rank_val = 200
        triggers.append("🎖️ <b>Ранговый статус: МАСТЕР / ЛЕГЕНДА</b> (+200₽)")
        notes.append("Мастер/Легенда (+200₽)")

    # Total estimated fair resale value in TG
    raw_est = base_val + primes_val + gems_val + skins_val + rank_val
    safety_factor = 1.0 if has_firstmail else 0.82
    if not has_firstmail:
        notes.append("Риск почты (-18%)")
    else:
        notes.append("Родная почта 100%")

    est_tg_price = round((raw_est * safety_factor) / 10) * 10
    est_tg_price = max(180, min(est_tg_price, 2800))

    profit = est_tg_price - price
    roi_percent = round((profit / price) * 100) if price > 0 else 0
    breakdown_summary = " | ".join(notes)

    # =============================================================
    # STEP 3: STRICT MATHEMATICAL SCORING & CATEGORIZATION
    # =============================================================
    tier = None
    is_approved = False
    verdict = ""

    # 1. GOD TIER / SNIPE TARGET (Priority #1 Instant Buy Trigger)
    # Condition: Pre-2023 OG archive exclusives (Star Shelly, Trixie Colette, Paladin Surge, Virus 8-Bit, Challenger Colt) at low price,
    # OR exceptional site valuation (Account Value >= 900) at low price.
    is_god_tier = (
        (has_pre_2023_og and price <= 450) or
        (base_site_val >= 900 and price <= 380)
    )

    # 2. HIGH TIER (Good solid lot)
    # Condition: High site score, Master/Legendary rank, 15+ Power 11 with hypercharges, 50k+ cups
    is_high_tier = (
        (trophies >= 50000 and (primes >= 15 or hypercharges >= 6)) or
        (is_master and primes >= 12 and trophies >= 40000) or
        (trophies >= 45000 and profit >= 260 and roi_percent >= 60)
    )

    # 3. LOW TIER / МУСОР (ABSOLUTE DROPPING / SILENT IGNORE)
    # Condition: Low site score, <40k cups without old skins, reg year 2026 (newreg),
    # low 3v3 wins (<1500), mostly 9-10 lvl without hypercharges.
    is_low_tier = False
    if not is_god_tier:
        if trophies < 40000 and not has_pre_2023_og:
            is_low_tier = True
        elif reg_year in [2025, 2026] and not has_pre_2023_og:
            is_low_tier = True
        elif wins_3v3 > 0 and wins_3v3 < 1500 and not has_pre_2023_og:
            is_low_tier = True
        elif primes < 6 and hypercharges == 0 and not has_pre_2023_og:
            is_low_tier = True
        elif profit < 220 or roi_percent < 50:
            is_low_tier = True

    # Final Categorization resolution
    if is_god_tier:
        tier = "GOD TIER / SNIPE TARGET"
        is_approved = True
        skin_names = ", ".join([s.split()[1] for s in og_skins_found]) if og_skins_found else "архивный статус"
        verdict = (
            f"🎯 <b>МГНОВЕННЫЙ ВЫКУП!</b> Обнаружен редчайший актив ({skin_names}), "
            f"недоступный для покупки в игре с 2020-2022 года. Цена продавца ({price:g} ₽) в разы ниже "
            f"рыночной стоимости ({est_tg_price} ₽). Спрос в Telegram колоссальный, улетит за 10 минут с ROI +{roi_percent}%."
        )
    elif is_high_tier and not is_low_tier:
        tier = "HIGH TIER"
        is_approved = True
        rank_label = "Мастер / Легенда" if is_master else "Киберспорт пул"
        verdict = (
            f"💎 <b>ОТЛИЧНЫЙ КИБЕРСПОРТИВНЫЙ ЛОТ!</b> Сильная боевая база: {trophies:,} кубков, "
            f"{primes} бойцов 11 LVL с гиперзарядами и престижный статус '{rank_label}'. "
            f"Чистый спред профита: +{profit} ₽ при минимальном риске."
        )
    else:
        tier = "LOW TIER (МУСОР)"
        is_approved = False
        verdict = "Отказ: низкие кубки (<40k), отсутствие архивных скинов или новорег без прокачки."

    # Prepare detailed key value breakdown for the 5-point report card
    key_values_list = []
    if og_skins_found:
        key_values_list.append("👑 Скины: " + ", ".join(og_skins_found))
    if hypercharges > 0 or primes > 0:
        key_values_list.append(f"⚡ Прокачка: {primes} праймов (11 LVL), {hypercharges} гиперзарядов")
    if is_master:
        key_values_list.append("🎖️ Ранг: МАСТЕР / ЛЕГЕНДА")
    if trophies >= 40000:
        key_values_list.append(f"🏆 Кубки: {trophies:,}")

    key_values_str = "\n".join([f"• {kv}" for kv in key_values_list]) if key_values_list else "• Базовый боевой ростер"

    evaluation_meta = {
        "tier": tier,
        "player_tag": player_tag or "Скрыт продавцом (требуется сверка)",
        "brawlify_url": brawlify_url,
        "brawltime_url": brawltime_url,
        "site_score": site_score_text or (f"Account Score: ~{est_tg_price} ₽ (по базам Ninja)" if est_tg_price else "Анализ по базам статистики"),
        "key_values": key_values_str,
        "verdict": verdict,
        "is_verified_tag": is_verified_tag
    }

    return is_approved, est_tg_price, profit, roi_percent, triggers, breakdown_summary, evaluation_meta
