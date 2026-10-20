from core.valuation import calculate_brawl_fair_valuation
from core.analyzer import analyze_lot_liquidity
from core.bot_ui import format_gold_message

def run_tests():
    # Test Case 1: GOD TIER with Star Shelly & Player Tag
    lot1 = {
        "offer_id": "1001",
        "href": "https://funpay.com/lots/offer?id=1001",
        "price": 280,
        "trophies": 32000,
        "brawlers": 78,
        "primes": 12,
        "seller": "SniperSeller",
        "reviews": 45,
        "desc": "32000 кубков, 78 бравлеров, 12 праймов, Звездная Шелли 2018, тег #2VP9GUPPU2",
        "has_firstmail": True
    }
    is_liquid, triggers, est_tg, profit = analyze_lot_liquidity(lot1)
    print("--- TEST 1: STAR SHELLY SNIPE ---")
    print(f"Liquid: {is_liquid} | Tier: {lot1.get('tier')} | Est: {est_tg}₽ | Profit: {profit}₽")
    print(f"Tag: {lot1.get('player_tag')} | Brawlify: {lot1.get('brawlify_url')}")
    assert is_liquid == True
    assert "GOD" in lot1.get("tier")
    msg1 = format_gold_message(lot1, is_new_alert=True)
    print("Message sample:\n", msg1[:300], "...\n")

    # Test Case 2: HIGH TIER with 54k trophies & Master rank
    lot2 = {
        "offer_id": "1002",
        "href": "https://funpay.com/lots/offer?id=1002",
        "price": 350,
        "trophies": 54000,
        "brawlers": 84,
        "primes": 22,
        "seller": "ProGamer",
        "reviews": 120,
        "desc": "54000 кубков, 84 бравлера, 22 прайма, 12 гиперзарядов, ранг Мастер лига, ник: cyber_beast",
        "has_firstmail": True
    }
    is_liquid2, triggers2, est_tg2, profit2 = analyze_lot_liquidity(lot2)
    print("--- TEST 2: HIGH TIER MASTER ---")
    print(f"Liquid: {is_liquid2} | Tier: {lot2.get('tier')} | Est: {est_tg2}₽ | Profit: {profit2}₽")
    assert is_liquid2 == True
    assert lot2.get("tier") == "HIGH TIER"
    msg2 = format_gold_message(lot2, is_new_alert=False)
    print("Message sample:\n", msg2[:300], "...\n")

    # Test Case 3: LOW TIER / МУСОР (Low trophies, newreg 2026, no OG skins)
    lot3 = {
        "offer_id": "1003",
        "href": "https://funpay.com/lots/offer?id=1003",
        "price": 250,
        "trophies": 21000,
        "brawlers": 55,
        "primes": 3,
        "seller": "NoobSeller",
        "reviews": 2,
        "desc": "21000 кубков, 55 бравлеров, 3 прайма, акк 2026 года, 9-10 уровни, тег #9YQ882L",
        "has_firstmail": False
    }
    is_liquid3, triggers3, est_tg3, profit3 = analyze_lot_liquidity(lot3)
    print("--- TEST 3: LOW TIER (MUST BE REJECTED) ---")
    print(f"Liquid: {is_liquid3} | Tier: {lot3.get('tier')} | Est: {est_tg3}₽ | Profit: {profit3}₽")
    assert is_liquid3 == False
    assert "LOW" in lot3.get("tier")

    print("\n✅ ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
