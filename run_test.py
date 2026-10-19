from funpay_brawl_bot import fetch_lots

lots = fetch_lots()
print(f"Total liquid lots after gem-fix: {len(lots)}")
for i, l in enumerate(lots[:5]):
    triggers_clean = [t.replace("<b>", "").replace("</b>", "") for t in l.get("triggers", [])]
    print(f"#{i+1}: Price: {l.get('price')} RUB | Est. TG: ~{l.get('est_tg_price')} RUB | Profit: +{l.get('profit')} RUB")
    print(f"  Triggers: {' | '.join(triggers_clean)}")
    print(f"  Seller: {l.get('seller')} ({l.get('reviews')} rev)")
    print(f"  Link: {l.get('href')}\n")
