import sys
from bs4 import BeautifulSoup

def main():
    filepath = r"C:\Users\alina\.gemini\antigravity\brain\48b8737a-8b17-4173-b0e6-e6d38506da18\.system_generated\steps\35\content.md"
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    lots = soup.find_all("a", class_="tc-item")
    print(f"Total lots found: {len(lots)}")

    header = soup.find("div", class_="tc-header")
    if header:
        print("Table Header Columns:")
        for col in header.find_all("div"):
            print(f"  - {col.get('class')}: {col.get_text(strip=True)}")

    for i, lot in enumerate(lots[:3]):
        print(f"\n=== Lot #{i+1} ===")
        desc_div = lot.find("div", class_="tc-desc")
        if desc_div:
            print("tc-desc HTML:")
            for child in desc_div.children:
                if child.name:
                    print(f"  <{child.name} class='{child.get('class')}'>{child.get_text(strip=True)}</{child.name}>")
                else:
                    text = child.strip()
                    if text:
                        print(f"  [NavigableString]: {text}")



if __name__ == "__main__":
    main()
