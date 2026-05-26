import httpx
import re
import json

print("=== Sinyi Deep Debug ===")
r = httpx.get(
    "https://www.sinyi.com.tw/buy/list",
    params={"region": "taipei-city", "price-min": "300", "price-max": "1300",
            "age-max": "46", "area-min": "19", "room-min": "2"},
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
    timeout=30,
    follow_redirects=True
)
text = r.text
print(f"Length: {len(text)}")

# Find the huge script
for m in re.finditer(r"<script[^>]*>", text):
    start = m.end()
    end_tag = text.find("</script>", start)
    if end_tag < 0:
        continue
    content = text[start:end_tag]
    if len(content) > 50000:
        print(f"\nBig script ({len(content)} chars)")
        
        # Find all top-level keys
        key_pattern = re.findall(r'"([a-zA-Z_][a-zA-Z0-9_]*)":(?:\{|\[)', content)
        seen_keys = {}
        for k in key_pattern:
            seen_keys[k] = seen_keys.get(k, 0) + 1
        for k, v in sorted(seen_keys.items()):
            print(f"  '{k}': {v} times")

        # Search for list-like structures with multiple numeric keys
        for kw in ["list", "data", "items", "result", "entry", "object"]:
            idx = 0
            while True:
                idx = content.find(f'"{kw}"', idx)
                if idx < 0:
                    break
                ctx = content[idx:idx+300]
                if re.search(rf'"{kw}"\s*:\s*\[', ctx):
                    print(f"\n  '{kw}' array found at {idx}:")
                    print(f"    {ctx[:300]}")
                idx += 1

        # More aggressive: find any key whose value is an array of objects with "title" or "address"
        for m in re.finditer(r'"(\w+)"\s*:\s*\[', content):
            key = m.group(1)
            pos = m.end()
            chunk = content[pos:pos+500]
            if '"title"' in chunk or '"address"' in chunk or '"id"' in chunk or '"price"' in chunk:
                print(f"\n  '{key}' has object array with likely listing fields:")
                print(f"    {chunk[:400]}")

        # Find ALL object arrays
        print("\n  All object arrays:")
        for m in re.finditer(r'"(\w+)"\s*:\s*\[', content):
            key = m.group(1)
            pos = m.end()
            chunk = content[pos:pos+1000]
            # Count how many objects in this array
            obj_count = chunk.count("{")
            print(f"    '{key}': ~{obj_count} objects, preview: {chunk[:200]}")
        break

# Also check for API endpoints
print("\n=== API endpoint search ===")
for m in re.finditer(r'["\x27](/api/[^\x27"]+)["\x27]', text):
    print(f"  API: {m.group(1)}")

# Try common API patterns
for api_path in ["/api/search", "/api/buy/search", "/api/property/search",
                 "/api/listings", "/api/objects", "/api/buy/objects",
                 "/api/search-objects", "/api/v1/search"]:
    try:
        api_r = httpx.get(
            f"https://www.sinyi.com.tw{api_path}",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        if api_r.status_code == 200 and ("{" in api_r.text or "[" in api_r.text):
            print(f"  HIT: {api_path} -> {api_r.text[:200]}")
    except:
        pass

# Also check with POST
for api_path in ["/api/search", "/api/buy/search", "/api/buy/list"]:
    try:
        api_r = httpx.post(
            f"https://www.sinyi.com.tw{api_path}",
            json={"region": "taipei-city"},
            headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"},
            timeout=10
        )
        if api_r.status_code == 200 and ("{" in api_r.text or "[" in api_r.text):
            print(f"  POST HIT: {api_path} -> {api_r.text[:200]}")
    except:
        pass
