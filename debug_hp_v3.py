import httpx
from bs4 import BeautifulSoup
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

r = httpx.get("https://www.houseprice.tw/", headers=headers, timeout=15, follow_redirects=True)
print(f"Status: {r.status_code}, Length: {len(r.text)}")
soup = BeautifulSoup(r.text, "lxml")

# Find all a tags
links = soup.find_all("a", href=True)
print(f"\nTotal links: {len(links)}")
for a in links[:50]:
    href = a.get("href", "")
    text = a.get_text(" ", strip=True)[:40]
    print(f"  [{text}] -> {href}")

# Find script tags
scripts = soup.find_all("script")
for s in scripts:
    src = s.get("src", "")
    if src:
        print(f"\nScript src: {src}")

# Find form/inputs
forms = soup.find_all("form")
print(f"\nForms: {len(forms)}")
for f in forms:
    action = f.get("action", "")
    method = f.get("method", "")
    print(f"  action={action}, method={method}")
    inputs = f.find_all("input")
    for inp in inputs:
        print(f"    input: name={inp.get('name')}, type={inp.get('type')}, placeholder={inp.get('placeholder')}")

# Check for any URL patterns
text_sample = r.text[:5000]
buy_links = re.findall(r'https?://[^\s"\']+houseprice[^\s"\']*', text_sample)
print(f"\nInternal URLs: {buy_links[:20]}")

# Try common search URLs
test_urls = [
    "/buy/taipei",
    "/buy/list?city=taipei",
    "/house/buy",
    "/search?type=buy&city=taipei",
    "/sale/list",
]

for tu in test_urls:
    try:
        tr = httpx.get(f"https://www.houseprice.tw{tu}", headers=headers, timeout=10, follow_redirects=True)
        print(f"  {tu} -> {tr.status_code}")
    except:
        print(f"  {tu} -> error")
