import httpx
import re
import json
from bs4 import BeautifulSoup

print("=== DEEP DEBUG 信義房屋 ===")
r = httpx.get(
    "https://www.sinyi.com.tw/buy/list",
    params={"region": "taipei-city", "price-min": "300", "price-max": "1300", "age-max": "46", "area-min": "19", "room-min": "2"},
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
    timeout=30,
    follow_redirects=True
)

soup = BeautifulSoup(r.text, "lxml")
scripts = soup.find_all("script")

# Find the big script (127511 chars) 
for i, s in enumerate(scripts):
    content = s.string or ""
    if len(content) > 50000:
        print(f"Script {i}: {len(content)} chars")
        
        # Search for specific patterns
        patterns = [
            r'"props"\s*:\s*\{',
            r'"pageProps"\s*:\s*\{',
            r'"listings"\s*:\s*\[',
            r'"data"\s*:\s*\{',
            r'"results"\s*:\s*\[',
            r'"houses"\s*:\s*\[',
            r'"objects"\s*:\s*\[',
            r'"items"\s*:\s*\[',
        ]
        for pat in patterns:
            m = re.search(pat, content)
            if m:
                print(f"  Found: {pat} at position {m.start()}")
                print(f"  Context: {content[m.start():m.start()+500]}")
        
        # Check for "house" context  
        for m in re.finditer(r'"house[A-Za-z]*"\s*:', content):
            ctx = content[m.start():m.start()+200]
            print(f"  House key: {ctx}")
            break
        
        # Try to find structured listing data
        # Search for JSON-LD structured data
        if "application/ld+json" in content:
            print("  Has JSON-LD!")
        
        # Find all price-like patterns for sanity
        prices = re.findall(r'"price"\s*:\s*(\d+)', content)
        print(f"  'price' values found: {len(prices)}")
        if prices:
            print(f"  Sample prices: {prices[:10]}")

# Check for next.js __NEXT_DATA__
for m in re.finditer(r'__NEXT_DATA__', r.text):
    ctx = r.text[m.start():m.start()+200]
    print(f"\nNEXT_DATA found: {ctx}")

# Check for any script with id  
scripts_with_id = [s for s in scripts if s.get("id")]
for s in scripts_with_id:
    content = s.string or ""
    print(f"\nScript id={s['id']}: {len(content)} chars")
    if len(content) > 100:
        print(f"  Type: {s.get('type','none')}, Preview: {content[:300]}")
