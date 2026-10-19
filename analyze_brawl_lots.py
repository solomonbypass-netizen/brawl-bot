import re
from bs4 import BeautifulSoup

def main():
    filepath = r"C:\Users\alina\.gemini\antigravity\brain\48b8737a-8b17-4173-b0e6-e6d38506da18\.system_generated\steps\35\content.md"
    with open(filepath, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    lots = soup.find_all("a", class_="tc-item")
    print(f"Total lots: {len(lots)}")

    parsed = []
    
    # Regex to extract trophies, brawlers, primes
    # Pattern: r"(\d+)\s+кубков(?:,\s+(\d+)\s+бравлер\w*)?(?:,\s+(\d+)\s+прайм\w*)?"
    pattern = re.compile(r"(\d+)\s*кубк\w*,\s*(\d+)\s*бравлер\w*(?:,\s*(\d+)\s*прайм\w*)?", re.IGNORECASE)

    for lot in lots:
        desc_div = lot.find("div", class_="tc-desc-text")
        price_div = lot.find("div", class_="tc-price")
        user_div = lot.find("div", class_="media-user-name")
        rating_div = lot.find("span", class_="rating-mini-count")

        if not desc_div or not price_div:
            continue

        full_desc = desc_div.get_text(strip=True)
        raw_price = price_div.get_text(strip=True)
        # clean price: "733.20 ₽" -> 733.20
        clean_price = re.sub(r"[^\d.]", "", raw_price.replace(" ", "").replace(",", "."))
        try:
            price = float(clean_price)
        except ValueError:
            price = 0.0

        user = user_div.get_text(strip=True) if user_div else "Unknown"
        reviews = int(rating_div.get_text(strip=True)) if rating_div else 0

        match = pattern.search(full_desc)
        trophies = int(match.group(1)) if match else None
        brawlers = int(match.group(2)) if match and match.group(2) else None
        primes = int(match.group(3)) if match and match.group(3) else 0

        parsed.append({
            "href": lot.get("href"),
            "price": price,
            "trophies": trophies,
            "brawlers": brawlers,
            "primes": primes,
            "seller": user,
            "reviews": reviews,
            "desc": full_desc
        })

    with_stats = [p for p in parsed if p["trophies"] is not None and p["brawlers"] is not None]
    print(f"Successfully extracted stats from {len(with_stats)} of {len(lots)} lots!")

    # Let's find the most undervalued accounts!
    # Formula example: Account Value score = (trophies / 1000) * 15 + (brawlers * 20) + (primes * 40)
    # Price-to-Value ratio: Value / Price
    for item in with_stats:
        if item["price"] > 50: # exclude fake 1 ruble accounts
            # simple benchmark: price per 1000 trophies
            item["price_per_1k_trophies"] = item["price"] / (item["trophies"] / 1000.0) if item["trophies"] > 0 else 999999
            # price per brawler
            item["price_per_brawler"] = item["price"] / item["brawlers"] if item["brawlers"] > 0 else 999999
            # estimated value
            item["score"] = (item["trophies"] * 0.03) + (item["brawlers"] * 15) + (item["primes"] * 30)
            item["margin_ratio"] = item["score"] / item["price"] if item["price"] > 0 else 0
        else:
            item["margin_ratio"] = 0

    valid = [p for p in with_stats if p["price"] >= 100 and p["trophies"] >= 10000]
    valid.sort(key=lambda x: x["margin_ratio"], reverse=True)

    print("\n=== TOP 10 POTENTIALLY UNDERVALUED ACCOUNTS (HIGH VALUE / LOW PRICE) ===")
    for i, it in enumerate(valid[:10]):
        print(f"#{i+1}: Price: {it['price']}₽ | Trophies: {it['trophies']} | Brawlers: {it['brawlers']} | Primes: {it['primes']}")
        print(f"    Seller: {it['seller']} ({it['reviews']} reviews) | Margin Score: {it['margin_ratio']:.1f}x")
        print(f"    Link: {it['href']}")
        print(f"    Desc: {it['desc'][:80]}...\n")

if __name__ == "__main__":
    main()
