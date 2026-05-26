import httpx
import re
import json

print("=" * 60)
print("=== YUNGCHING HTML STRUCTURE ===")
print("=" * 60)
r = httpx.get(
    "https://buy.yungching.com.tw/region/%E5%8F%B0%E5%8C%97%E5%B8%82-_c/totalprice_300_1300/age_0_46/area_19_/room_2_",
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=20,
    follow_redirects=True
)
# Find first house block
idx = r.text.find('/house/')
print(f"First /house/ at byte {idx}")
start = max(0, idx - 500)
end = min(len(r.text), idx + 4000)
block = r.text[start:end]
print(f"HTML block ({len(block)} bytes):")
print(block)
print("\n" + "=" * 60)

# Also check: is there SSR data somewhere?
for m in re.finditer(r'<div[^>]*>', r.text[idx:idx+2000]):
    print(f"  DIV tag: {m.group()}")
