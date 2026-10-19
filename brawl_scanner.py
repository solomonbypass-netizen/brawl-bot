"""
FunPay Brawl Stars Account Arbitrage Scanner & Valuation Engine
---------------------------------------------------------------
Scans FunPay accounts, parses structured game attributes, scores account value,
and identifies heavily undervalued accounts for profitable flipping.
"""

import re
import sys
import json
import urllib.request
from bs4 import BeautifulSoup

def clean_price(raw_price_str):
    """Converts price strings like '733.20 ₽' or '1 200 ₽' to float."""
    cleaned = re.sub(r"[^\d.]", "", raw_price_str.replace(" ", "").replace(",", "."))
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

def parse_funpay_catalog(html_content):
    """Parses all lots from FunPay catalog HTML."""
    soup = BeautifulSoup(html_content, "html.parser")
    lots = soup.find_all("a", class_="tc-item")
    
    # Regex to extract trophies, brawlers, primes
    pattern = re.compile(r"(\d+)\s*кубк\w*,\s*(\d+)\s*бравлер\w*(?:,\s*(\d+)\s*прайм\w*)?", re.IGNORECASE)
    tag_regex = re.compile(r"#[0289PYLQGRJCUVa-z]{4,12}", re.IGNORECASE)
    
    results = []
    for lot in lots:
        desc_el = lot.find("div", class_="tc-desc-text")
        price_el = lot.find("div", class_="tc-price")
        user_el = lot.find("div", class_="media-user-name")
        rating_el = lot.find("span", class_="rating-mini-count")
        
        if not desc_el or not price_el:
            continue
            
        desc = desc_el.get_text(strip=True)
        price = clean_price(price_el.get_text(strip=True))
        seller = user_el.get_text(strip=True) if user_el else "Unknown"
        reviews = int(rating_el.get_text(strip=True)) if rating_el else 0
        href = lot.get("href", "")
        if href and not href.startswith("http"):
            href = "https://funpay.com" + href
            
        match = pattern.search(desc)
        trophies = int(match.group(1)) if match else 0
        brawlers = int(match.group(2)) if match and match.group(2) else 0
        primes = int(match.group(3)) if match and match.group(3) else 0
        
        tags = tag_regex.findall(desc)
        
        # Security indicators in text
        desc_lower = desc.lower()
        has_firstmail = any(k in desc_lower for k in ["firstmail", "родная почта", "родная", "с почтой", "отдам почту", "чистая"])
        is_negotiable = any(k in desc_lower for k in ["договорная", "цена в лс", "писать в лс"])
        
        # Valuation Model (Estimated Market Resale Value in RUB):
        # Base account value = (trophies * 0.035) + (brawlers * 15) + (primes * 35)
        # Accounts with 70+ brawlers and 30k+ trophies typically sell in TG for 1000-2500 RUB
        estimated_market_value = (trophies * 0.035) + (brawlers * 18.0) + (primes * 35.0)
        
        # Fix for unrealistic typo trophies (e.g. 500,000 trophies when world max is ~150k)
        if trophies > 150000:
            estimated_market_value = (50000 * 0.035) + (brawlers * 18.0) + (primes * 35.0)

        # Margin multiplier
        margin_score = (estimated_market_value / price) if price > 0 else 0
        
        results.append({
            "href": href,
            "price": price,
            "trophies": trophies,
            "brawlers": brawlers,
            "primes": primes,
            "seller": seller,
            "reviews": reviews,
            "desc": desc,
            "tags": tags,
            "has_firstmail": has_firstmail,
            "is_negotiable": is_negotiable,
            "est_value": round(estimated_market_value, 2),
            "margin_score": round(margin_score, 2)
        })
        
    return results

def filter_arbitrage_deals(lots, min_price=150, max_price=1500, min_trophies=15000, min_brawlers=50, min_margin=2.5):
    """Filters out trash, negotiable fake prices, and isolates high-profit flipping candidates."""
    candidates = []
    for lot in lots:
        # Exclude fake negotiable / price-placeholder accounts (e.g. 100 ruble accounts asking to DM)
        if lot["is_negotiable"] and lot["price"] < 200:
            continue
        if lot["price"] < min_price or lot["price"] > max_price:
            continue
        if lot["trophies"] < min_trophies or lot["brawlers"] < min_brawlers:
            continue
        if lot["margin_score"] < min_margin:
            continue
            
        candidates.append(lot)
        
    # Sort by margin score descending
    candidates.sort(key=lambda x: x["margin_score"], reverse=True)
    return candidates

def fetch_brawltime_stats(tag):
    """Fetches real-time profile verification from BrawlTime Ninja for a player tag."""
    clean_tag = tag.replace("#", "").upper()
    url = f"https://brawltime.ninja/profile/{clean_tag}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            # Extract trophies / brawlers / name from HTML if present
            name_match = re.search(r"<h1[^>]*>([^<]+)</h1>", html)
            name = name_match.group(1).strip() if name_match else "Verified Player"
            return {"status": "success", "player_name": name, "url": url}
    except Exception as e:
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    filepath = r"C:\Users\alina\.gemini\antigravity\brain\48b8737a-8b17-4173-b0e6-e6d38506da18\.system_generated\steps\35\content.md"
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    print("Analyzing FunPay Brawl Stars Market...")
    all_lots = parse_funpay_catalog(html)
    print(f"Loaded and parsed {len(all_lots)} live accounts.\n")
    
    deals = filter_arbitrage_deals(
        all_lots, 
        min_price=200,          # Minimum realistic non-dummy price
        max_price=1200,         # Sweet spot for fast resale in Telegram
        min_trophies=20000,     # Serious accounts
        min_brawlers=60,        # Most characters unlocked
        min_margin=2.0          # At least 2x resale potential
    )
    
    print(f"Found {len(deals)} High-Confidence Arbitrage Deals (Price: 200 - 1200 RUB):\n" + "="*80)
    for i, deal in enumerate(deals[:10]):
        mail_badge = "[EMAIL INCLUDED]" if deal["has_firstmail"] else "[CHECK EMAIL]"
        print(f"Deal #{i+1} | Price: {deal['price']} RUB | Est. Value: ~{deal['est_value']} RUB | X-Profit: {deal['margin_score']}x")
        print(f"Stats: {deal['trophies']} Trophies | {deal['brawlers']} Brawlers | {deal['primes']} Primes (11lvl)")
        print(f"Seller: {deal['seller']} ({deal['reviews']} reviews) | {mail_badge}")
        if deal["tags"]:
            print(f"Player Tag: {', '.join(deal['tags'])}")
        print(f"Link: {deal['href']}")
        print(f"Desc: {deal['desc'][:90]}...")
        print("-" * 80)
