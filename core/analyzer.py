import re
from core.valuation import calculate_brawl_fair_valuation, extract_real_gems

OG_SKINS = [
    "звездная шелли", "star shelly", "шелли 2018", "2018", "2019", "корсар кольт",
    "рикошет", "вирус 8-бит", "вирус", "ведьма шелли", "оборотень леон",
    "торговец гейл", "паладин вольт", "майк портье", "хэллоуин", "олд акк", "трикси колетт"
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
    """Delegates to ValuationGuru's strict gem extractor."""
    return extract_real_gems(desc_lower)

def analyze_lot_liquidity(lot_dict):
    """
    Delegates to the Valuation Guru engine for realistic multi-factor market pricing.
    Returns: (is_approved, triggers, est_tg_price, profit)
    Enriches lot_dict with 'roi_percent' and 'valuation_breakdown'.
    """
    is_approved, est_tg_price, profit, roi_percent, triggers, breakdown = calculate_brawl_fair_valuation(lot_dict)
    lot_dict["roi_percent"] = roi_percent
    lot_dict["valuation_breakdown"] = breakdown
    return is_approved, triggers, est_tg_price, profit
