import re
from bs4 import BeautifulSoup

def main():
    filepath = r"C:\Users\alina\.gemini\antigravity\brain\48b8737a-8b17-4173-b0e6-e6d38506da18\.system_generated\steps\35\content.md"
    with open(filepath, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    lots = soup.find_all("a", class_="tc-item")
    
    # Brawl Stars tag regex: starts with #, characters 0289PYLQGRJCUV, length 3-12
    tag_regex = re.compile(r"#[0289PYLQGRJCUVa-z]{4,12}", re.IGNORECASE)
    
    found_tags = []
    for lot in lots:
        desc_div = lot.find("div", class_="tc-desc-text")
        if not desc_div:
            continue
        text = desc_div.get_text()
        tags = tag_regex.findall(text)
        if tags:
            price_div = lot.find("div", class_="tc-price")
            price = price_div.get_text(strip=True) if price_div else "N/A"
            found_tags.append({
                "tags": tags,
                "price": price,
                "desc": text,
                "href": lot.get("href")
            })

    print(f"Total lots with explicit #TAG in table description: {len(found_tags)}")
    for item in found_tags[:10]:
        print(f"Tag: {item['tags']} | Price: {item['price']} | Link: {item['href']}")
        print(f"  Snippet: {item['desc'][:70]}...\n")

if __name__ == "__main__":
    main()
