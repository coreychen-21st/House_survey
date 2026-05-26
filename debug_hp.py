import httpx
import re

r = httpx.get(
    "https://www.houseprice.tw/",
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=15,
    follow_redirects=True
)

# Find all script src
scripts = re.findall(r'src="([^"]+)"', r.text)
print("=== Scripts ===")
for s in scripts:
    print(f"  {s}")

# Find API patterns
apisms = re.findall(r'"([^"]*api[^"]*)"', r.text)
print("\n=== API ===")
for a in apisms:
    print(f"  {a}")

# Find href patterns
hrefs = re.findall(r'href="([^"]*buy[^"]*)"', r.text)
print("\n=== Buy links ===")
for h in hrefs:
    print(f"  {h}")

# Search page structure
print("\n=== Page title ===")
title_m = re.search(r'<title>([^<]+)</title>', r.text)
if title_m:
    print(f"  {title_m.group(1)}")

# Find any data-url or router links
router = re.findall(r'(?:data-url|router-link|to)="([^"]*)"', r.text)
print("\n=== Router/Data links ===")
for u in router[:20]:
    print(f"  {u}")

# Check if Vue/Nuxt
for fw in ["Vue", "Nuxt", "React", "Angular", "app", "__NUXT__", "__NEXT_DATA__"]:
    if fw in r.text:
        print(f"\nFramework: {fw} found")
