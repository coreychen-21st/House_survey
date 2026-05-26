import httpx
import re

print("=== 591 HTML Structure ===")
r = httpx.get(
    "https://sale.591.com.tw/?regionid=1&totalprice=300_1300&area=19_&room=2_&shType=list",
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
    timeout=20,
    follow_redirects=True
)

# Find non-NUXT listing content
nuxt_start = r.text.find("window.__NUXT__")
print(f"__NUXT__ at byte {nuxt_start}")

# Look in the non-NUXT area for listing HTML
before_nuxt = r.text[:nuxt_start] if nuxt_start > 0 else ""

# Search for listing patterns like post_id, house title etc
for kw in ["post_id", "postId", "detail/2/", "house-item", "vue-list"]:
    idx = before_nuxt.find(kw)
    print(f"  '{kw}' in before-NUXT: {idx}")

# Find listing elements by ID/class patterns
for pattern in ['<div id="vue-list"', '<div id="house-list"', '<ul class="house', '<div class="list']:
    idx = r.text.find(pattern)
    print(f"  '{pattern}' at: {idx}")

# Check entire page for listing-like data
for kw in ['"post_id":', '"postId":', "'post_id':", 'detail/2/']:
    count = r.text.count(kw)
    print(f"  '{kw}' count: {count}")

# Find JSON-like listing data in script
from bs4 import BeautifulSoup
soup = BeautifulSoup(r.text, "lxml")
for script in soup.find_all("script"):
    content = script.string or ""
    if "NUXT" in content:
        # Try to find the rendered data by looking at the last part of NUXT
        last_part = content[-5000:]
        for kw in [r'"data":', r'"list":', r'"items":', r'"posts":']:
            idx = last_part.find(kw)
            if idx >= 0:
                print(f"\n  Found '{kw}' in last 5000 chars of NUXT:")
                print(f"    {last_part[idx:idx+300]}")
        
        # Check if the NUXT function evaluates to data
        # The pattern: (function(a,b,c,...){...return {data:[...]}})(...)
        return_idx = content.rfind("return")
        if return_idx > 0:
            ret_segment = content[return_idx:return_idx+2000]
            print(f"\n  Return segment preview:")
            print(f"    {ret_segment[:500]}")

# Check: Is the data in the body HTML?
body = soup.find("body")
if body:
    body_text = body.get_text(" ", strip=True)
    if "坪" in body_text:
        print(f"\nBody contains listings (has 坪): len={len(body_text)}")
        for m in re.finditer(r"[0-9,]+\s*萬", body_text):
            print(f"  Price in body: {m.group()}")

# Alternative: check if 591 has a separate API endpoint visible
print("\n=== Searching for API ===")
for pattern in ['"search/list"', '"home/search"', '"/api"', "'api'", 'axios', 'fetch(']:
    count = r.text.count(pattern)
    print(f"  '{pattern}': {count}")
