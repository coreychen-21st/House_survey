import httpx
import re
from bs4 import BeautifulSoup

print("=== DEBUG 永慶房屋 ===")
r = httpx.get(
    "https://buy.yungching.com.tw/region/%E5%8F%B0%E5%8C%97%E5%B8%82-_c/totalprice_300_1300/age_0_46/area_19_/room_2_",
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=30,
    follow_redirects=True
)
print(f"Status: {r.status_code}, Length: {len(r.text)}")

soup = BeautifulSoup(r.text, "lxml")

# Check for house links
links = soup.find_all("a", href=True)
house_links = [l for l in links if "/house/" in l.get("href", "")]
print(f"All links: {len(links)}, House links: {len(house_links)}")

if house_links:
    for hl in house_links[:3]:
        h = hl.get("href", "")
        text = hl.get_text(" ", strip=True)[:100]
        print(f"  href={h}, text={text}")
else:
    # Debug: show some link hrefs
    print("Non-house link samples:")
    for l in links[:20]:
        print(f"  href={l.get('href','')[:100]}")
    
# Check for JSON data in scripts
scripts = soup.find_all("script")
print(f"\nScripts: {len(scripts)}")
for s in scripts:
    content = s.string or ""
    if "/house/" in content or "houseData" in content or "listing" in content.lower()[:500]:
        print(f"  Found listing data: {content[:300]}")
    elif len(content) > 500:
        # Check for any JSON-like data
        if '"data"' in content[:200] or '"list"' in content[:200]:
            print(f"  JSON data: {content[:300]}")

# Check entire text for house patterns  
text_sample = r.text[:5000]
house_matches = re.findall(r'/house/\d+', text_sample)
print(f"\nHouse URL patterns in first 5000 chars: {house_matches[:10]}")

# Check if content is loaded via JS
if "SSR" in r.text[:500] or "ssr" in r.text[:500].lower():
    print("Page appears SSR")
if "window.__INITIAL" in r.text:
    print("Has INITIAL_STATE!")
    m = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.+?});', r.text, re.DOTALL)
    if m:
        print(f"  INITIAL_STATE preview: {m.group(1)[:500]}")
