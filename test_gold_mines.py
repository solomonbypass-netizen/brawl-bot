import re
from bs4 import BeautifulSoup
from funpay_brawl_bot import extract_exact_rub_price

filepath = r"C:\Users\alina\.gemini\antigravity\brain\48b8737a-8b17-4173-b0e6-e6d38506da18\.system_generated\steps\35\content.md"
with open(filepath, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

lots = soup.find_all("a", class_="tc-item")

OG_SKINS = [
    "звездная шелли", "star shelly", "шелли 2018", "2018", "2019", "корсар кольт",
    "рикошет", "вирус 8-бит", "вирус", "ведьма шелли", "оборотень леон",
    "торговец гейл", "паладин вольт", "майк портье", "хэллоуин"
]

GEMS_REGEX = re.compile(r"(\d{2,4})\s*(?:гем|gem)", re.IGNORECASE)
BP_REGEX = re.compile(r"(?:бп\+|brawl\s*pass\+|бравл\s*пасс\+|куплен\s*бп)", re.IGNORECASE)
PATTERN_STATS = re.compile(r"(\d+)\s*кубк\w*,\s*(\d+)\s*бравлер\w*(?:,\s*(\d+)\s*прайм\w*)?", re.IGNORECASE)

gold_mines = []

for lot in lots:
    price_el = lot.find("div", class_="tc-price")
    desc_el = lot.find("div", class_="tc-desc-text")
    user_el = lot.find("div", class_="media-user-name")
    rating_el = lot.find("span", class_="rating-mini-count")
    
    if not price_el or not desc_el:
        continue
        
    price = extract_exact_rub_price(price_el)
    desc = desc_el.get_text(strip=True)
    seller = user_el.get_text(strip=True) if user_el else "Unknown"
    reviews = int(rating_el.get_text(strip=True)) if rating_el else 0
    href = lot.get("href", "")
    
    # HARD FILTER: Only ultra-low entry (100 - 380 RUB)
    if price < 100 or price > 380:
        continue
        
    desc_lower = desc.lower()
    
    found_og = [s for s in OG_SKINS if s in desc_lower]
    gems_match = GEMS_REGEX.search(desc_lower)
    gems_count = int(gems_match.group(1)) if gems_match else 0
    has_bp = bool(BP_REGEX.search(desc_lower))
    
    match = PATTERN_STATS.search(desc)
    trophies = int(match.group(1)) if match else 0
    brawlers = int(match.group(2)) if match and match.group(2) else 0
    primes = int(match.group(3)) if match and match.group(3) else 0
    has_mail = any(k in desc_lower for k in ["firstmail", "родная почта", "родная", "с почтой", "отдам почту"])
    
    reasons = []
    if found_og:
        reasons.append(f"OG Скин: {found_og[0].upper()}")
    if gems_count >= 80:
        reasons.append(f"Баланс: {gems_count} гемов")
    if has_bp:
        reasons.append("Куплен Brawl Pass+")
    if brawlers >= 75:
        reasons.append(f"{brawlers} бравлеров за {price}₽")
    if primes >= 15:
        reasons.append(f"{primes} прокачанных праймов (11lvl)")
        
    if reasons:
        gold_mines.append({
            "price": price,
            "trophies": trophies,
            "brawlers": brawlers,
            "primes": primes,
            "seller": seller,
            "reviews": reviews,
            "reasons": reasons,
            "has_mail": has_mail,
            "href": href,
            "desc": desc
        })

print(f"Total true high-liquidity gold mines found: {len(gold_mines)}")
for i, g in enumerate(gold_mines[:10]):
    print(f"#{i+1}: Price: {g['price']} RUB | Seller: {g['seller']} ({g['reviews']} rev)")
    print(f"    Triggers: {' | '.join(g['reasons'])}")
    print(f"    Stats: {g['trophies']} trophies, {g['brawlers']} brawlers, {g['primes']} primes")
    print(f"    Desc: {g['desc'][:85]}...")
    print(f"    Link: {g['href']}\n")
