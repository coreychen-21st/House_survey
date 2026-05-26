import httpx
import re
from bs4 import BeautifulSoup
import json

print("=== DEBUG 信義房屋 ===")
r = httpx.get(
    "https://www.sinyi.com.tw/buy/list",
    params={"region": "taipei-city", "price-min": "300", "price-max": "1300", "age-max": "46", "area-min": "19", "room-min": "2"},
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
    timeout=30,
    follow_redirects=True
)
print(f"Status: {r.status_code}, Length: {len(r.text)}")

soup = BeautifulSoup(r.text, "lxml")
scripts = soup.find_all("script")
print(f"Scripts: {len(scripts)}")

for i, s in enumerate(scripts):
    content = s.string or ""
    if not content:
        continue
    # Search for listing-related keywords
    for kw in ["listingList", "listings", "houseList", "searchResult", "objectList", "saleList", "items", "data", "house"]:
        if f'"{kw}"' in content[:5000] or f"{kw}:" in content[:2000]:
            print(f"\nScript {i}: found '{kw}' ({len(content)} chars)")
            idx = content.find(kw)
            print(f"  Context: {content[max(0,idx-50):idx+300]}")
            break

# Also dump specific inline scripts  
for i, s in enumerate(scripts):
    content = s.string or ""
    if len(content) > 5000:
        print(f"\nScript {i}: {len(content)} chars")
        for kw in ["listing", "house", "buy", "sale", "search"]:
            cnt = content.count(kw)
            if cnt > 5:
                print(f"  '{kw}' appears {cnt} times")
        
# Try to find the API endpoint used by the page
api_patterns = re.findall(r'["\'](\/api\/[^"\']+)["\']', r.text)
print(f"\nAPI endpoints found: {api_patterns[:10]}")

# Try to request the actual API
try:
    api_r = httpx.get(
        "https://www.sinyi.com.tw/api/buy/list",
        params={"region": "taipei-city", "price-min": "300", "price-max": "1300", "age-max": "46", "area-min": "19", "room-min": "2"},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=15
    )
    print(f"\nAPI /api/buy/list status: {api_r.status_code}")
    if api_r.status_code == 200:
        try:
            data = api_r.json()
            print(f"  JSON keys: {list(data.keys())[:10] if isinstance(data, dict) else type(data)}")
        except:
            print(f"  Text: {api_r.text[:300]}")
except Exception as e:
    print(f"  API error: {e}")
