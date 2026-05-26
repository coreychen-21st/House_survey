import httpx, re, json

r = httpx.get(
    "https://www.sinyi.com.tw/buy/list",
    params={"region": "taipei-city", "price-min": "300", "price-max": "1300", "age-max": "46", "area-min": "19", "room-min": "2"},
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
    timeout=30, follow_redirects=True
)
text = r.text

# Find the "list" array with object data  
m = re.search(r'"list"\s*:\s*\[', text)
print(f"'list' found at byte {m.start() if m else 'NOTFOUND'}")

if m:
    start = m.start() + len('"list":[')
    # Walk through bracket counting to find end of array
    depth = 1
    pos = start
    in_string = False
    while depth > 0 and pos < len(text):
        c = text[pos]
        if c == '\\':
            pos += 1
        elif c == '"' and (pos == 0 or text[pos-1] != '\\'):
            in_string = not in_string
        elif not in_string:
            if c == '[':
                depth += 1
            elif c == ']':
                depth -= 1
        pos += 1

    raw = text[start:pos-1]
    print(f"Array length: {len(raw)} bytes")
    # Try to repair and parse
    try:
        data = json.loads(f"[{raw}]")
        print(f"Parsed: {type(data).__name__} length {len(data)}")
        if data and isinstance(data, list) and isinstance(data[0], dict):
            print(f"First item keys: {list(data[0].keys())}")
            # Find items within price range
            for item in data[:5]:
                price_keys = ["price", "totalPrice", "total_price", "salePrice"]
                p = 0
                for k in price_keys:
                    v = item.get(k)
                    if v:
                        if isinstance(v, str):
                            v = float(v.replace(",", "").replace("萬", ""))
                        if v > 0:
                            p = v
                            break
                addr = item.get("address", "") or item.get("section", "") or item.get("road", "")
                name = item.get("name", "")
                print(f"  price={p}, addr={addr[:40]}, name={name}")
    except Exception as e:
        print(f"Parse error: {e}")
        print(f"Sample: {raw[:500]}")
