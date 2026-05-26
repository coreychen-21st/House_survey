import httpx
import re
import json
from bs4 import BeautifulSoup

print("=== Quick YungChing LD Test ===")
r = httpx.get(
    "https://buy.yungching.com.tw/region/%E5%8F%B0%E5%8C%97%E5%B8%82-_c/totalprice_300_1300/age_0_46/area_19_/room_2_",
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=20,
    follow_redirects=True
)
soup = BeautifulSoup(r.text, "lxml")
ld_tags = soup.find_all("script", type="application/ld+json")
print(f"LD script tags: {len(ld_tags)}")
for ld in ld_tags:
    content = ld.string
    if not content:
        continue
    print(f"  LD content ({len(content)} chars): {content[:200]}")
    try:
        data = json.loads(content)
        if isinstance(data, list):
            print(f"  Is list of {len(data)}")
            if data and isinstance(data[0], dict):
                print(f"  First keys: {list(data[0].keys())[:10]}")
        elif isinstance(data, dict):
            keys = list(data.keys())
            print(f"  Keys: {keys}")
            if "itemListElement" in data:
                elems = data["itemListElement"]
                print(f"  Items: {len(elems)}")
                for e in elems[:3]:
                    print(f"    {e}")
            if "about" in data:
                print(f"  about: {str(data['about'])[:100]}")
    except Exception as e:
        print(f"  Parse error: {e}")

print("\n=== Quick Sinyi Keys Test ===")
r2 = httpx.get(
    "https://www.sinyi.com.tw/buy/list",
    params={"region": "taipei-city", "price-min": "300", "price-max": "1300",
            "age-max": "46", "area-min": "19", "room-min": "2"},
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
    timeout=20,
    follow_redirects=True
)
text = r2.text
for kw in ["listingList", "objects", "houseList", "searchResults",
           "listings", "searchResult", "saleList", "result", "property"]:
    idx = text.find(kw)
    print(f"  '{kw}' at pos {idx}" + (f": {text[idx:idx+100]}" if idx > 0 else ""))

print("\n=== Quick 591 NUXT Test ===")
r3 = httpx.get(
    "https://sale.591.com.tw/?regionid=1&totalprice=300_1300&area=19_&room=2_",
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
    timeout=20,
    follow_redirects=True
)
soup3 = BeautifulSoup(r3.text, "lxml")
for s in soup3.find_all("script"):
    content = s.string or ""
    if "NUXT" in content:
        print(f"NUXT script: {len(content)} chars")
        nidx = content.find("NUXT")
        segment = content[nidx:nidx+200]
        print(f"  Preview: {segment}")
        break
