import httpx
import re
import json
from bs4 import BeautifulSoup

print("=== DEEP DEBUG 永慶房屋 ===")
r = httpx.get(
    "https://buy.yungching.com.tw/region/%E5%8F%B0%E5%8C%97%E5%B8%82-_c/totalprice_300_1300/age_0_46/area_19_/room_2_",
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=30,
    follow_redirects=True
)

soup = BeautifulSoup(r.text, "lxml")
scripts = soup.find_all("script")
for i, s in enumerate(scripts):
    content = s.string or ""
    if "ItemList" in content:
        idx = content.find("ItemList")
        chunk = content[idx:idx+20000]
        print(f"Script {i}: ItemList found at {idx}")
        print(f"ItemList content preview: {chunk[:3000]}")
        
        # Extract structured data
        m = re.search(r'"itemListElement"\s*:\s*(\[.+?\}\])\s*\}', chunk, re.DOTALL)
        if m:
            print(f"\nitemListElement found!")
            raw = m.group(1)
            print(f"Length: {len(raw)}, preview: {raw[:500]}")
            if raw.endswith("}]"):
                # Fix potential truncation
                raw += "}]"
            try:
                items = json.loads(raw)
                print(f"Successfully parsed {len(items)} items!")
                for item in items[:3]:
                    print(f"  item keys: {list(item.keys())}")
                    print(f"  item sample: {json.dumps(item, ensure_ascii=False)[:300]}")
            except Exception as e:
                print(f"Parse error: {e}")
                lines = raw.split("},{")
                print(f"Items approx: {len(lines)}")
                if lines:
                    try_line = lines[0] + "}]"
                    try:
                        first = json.loads(try_line)
                        print(f"  First item: {json.dumps(first, ensure_ascii=False)[:200]}")
                    except:
                        print(f"  Failed: {try_line[:200]}")

# Also check the redirect destination
print(f"\nFinal URL: {str(r.url)[:200]}")

# Check if listing content is loaded via a different URL
redirects = r.history
print(f"Redirect chain: {[str(h.url)[:200] for h in redirects]}")
