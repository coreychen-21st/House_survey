import httpx
import re
import json
import sys

# Test 591 site structure
print("=== Testing 591 ===")
r = httpx.get(
    "https://sale.591.com.tw/?regionid=1&totalprice=300_1300&area=19_&room=2_",
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
    timeout=20
)
print(f"Status: {r.status_code}, Length: {len(r.text)}")

# Check if it's SPA empty shell
from bs4 import BeautifulSoup
soup = BeautifulSoup(r.text, "lxml")
scripts = soup.find_all("script")
print(f"Scripts found: {len(scripts)}")
for s in scripts[:5]:
    src = s.get("src", "")
    content = s.string or ""
    content_preview = content[:200] if content else ""
    if src:
        print(f"  src: {src[:120]}")
    if content_preview:
        print(f"  inline: {content_preview}")

# Test sinyi
print("\n=== Testing Sinyi ===")
r2 = httpx.get(
    "https://www.sinyi.com.tw/buy/list",
    params={"region": "taipei-city", "price-min": "300", "price-max": "1300", "age-max": "46", "area-min": "19", "room-min": "2"},
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
    timeout=20,
    follow_redirects=True
)
print(f"Status: {r2.status_code}, Length: {len(r2.text)}")

# Try to find JSON/API data in sinyi
soup2 = BeautifulSoup(r2.text, "lxml")
scripts2 = soup2.find_all("script")
print(f"Scripts found: {len(scripts2)}")

# Check for __NEXT_DATA__ or similar
for s in scripts2:
    content = s.string or ""
    if "__NEXT_DATA__" in content:
        print("Found __NEXT_DATA__!")
        m = re.search(r'__NEXT_DATA__\s*=\s*({.+})', content, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(1))
                print("Parsed NEXT_DATA successfully")
                props = data.get("props", {}).get("pageProps", {})
                print(f"Keys: {list(props.keys())[:10]}")
            except:
                print("Failed to parse NEXT_DATA")
    elif "apiCache" in content:
        print("Found apiCache!")
        m = re.search(r'"apiCache":({.+?})', content, re.DOTALL)
        if m:
            print(f"apiCache preview: {m.group(1)[:500]}")
    elif "listings" in content[:500]:
        print("Found 'listings' in inline script")
        print(f"Preview: {content[:500]}")

# Also check all inline scripts for listing data  
for i, s in enumerate(scripts2[:5]):
    content = s.string or ""
    if len(content) > 100:
        print(f"\nScript {i} content preview ({len(content)} chars):")
        print(content[:500])

print("\n=== Testing yungching ===")
r3 = httpx.get(
    "https://buy.yungching.com.tw/region/%E5%8F%B0%E5%8C%97%E5%B8%82-_c/totalprice_300_1300/age_0_46/area_19_/room_2_",
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=20,
    follow_redirects=True
)
print(f"Status: {r3.status_code}, Length: {len(r3.text)}")
soup3 = BeautifulSoup(r3.text, "lxml")
cards = soup3.select("a[href*='/house/']")
print(f"House links found: {len(cards)}")
hrefs = [c.get("href", "") for c in cards[:5]]
print(f"Sample hrefs: {hrefs}")

# Try to find JSON data in yungching
scripts3 = soup3.find_all("script")
print(f"Scripts: {len(scripts3)}")
for s in scripts3[:5]:
    content = s.string or ""
    if "list" in content[:200] or "house" in content[:200] or "data" in content[:200]:
        print(f"Script preview ({len(content)} chars): {content[:300]}")
