import httpx
import re

print("=== YungChing: Find SSR listing blocks ===")
r = httpx.get(
    "https://buy.yungching.com.tw/region/%E5%8F%B0%E5%8C%97%E5%B8%82-_c/totalprice_300_1300/age_0_46/area_19_/room_2_",
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=20,
    follow_redirects=True
)
print(f"Final URL: {r.url}")
print(f"Total size: {len(r.text)}")

# Skip LD+JSON area and find actual listing HTML
# Search for patterns like: "台北市" followed by district
idx = r.text.find('"ItemList"')
if idx < 0:
    idx = 0
post_ld = r.text[idx:]
house_url_idx = post_ld.rfind('"url":"https://buy.yungching.com.tw/house/')
ld_end = post_ld.find("}", house_url_idx + 100)

# Now find listings AFTER the LD data
search_start = idx + ld_end + 50

# Search for SSR listing blocks - they contain full details
# Look for patterns like: "綠蔭窗景公園二樓", "台北市信義區松德路"
listing_area = r.text[search_start:search_start+50000]

# Find listing blocks by looking for price patterns in non-LD area
price_positions = []
for m in re.finditer(r'([\d,]+)\s*萬', listing_area):
    v = float(m.group(1).replace(",", ""))
    if 300 <= v <= 1300:
        ctx_start = max(0, m.start() - 2000)
        ctx_end = min(len(listing_area), m.end() + 3000)
        price_positions.append((ctx_start, ctx_end))

print(f"\nFound {len(price_positions)} potential listing blocks with target price range")
if price_positions:
    s, e = price_positions[0]
    print(f"\n--- Block 1 ({e-s} bytes) ---")
    print(listing_area[s:e])

# Also check for anchor tags with /house/ URLs in the SSR area
house_anchors = list(re.finditer(r'<a[^>]*href="https://buy\.yungching\.com\.tw/house/\d+"[^>]*>(.*?)</a>', listing_area, re.DOTALL))
print(f"\nAnchor tags with house URLs: {len(house_anchors)}")
for m in house_anchors[:3]:
    print(f"\nAnchor: {m.group()}")
