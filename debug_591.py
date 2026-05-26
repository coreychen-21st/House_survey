import httpx
import re
import json
from bs4 import BeautifulSoup

print("=== DEBUG 591 ===")
r = httpx.get(
    "https://sale.591.com.tw/?regionid=1&totalprice=300_1300&area=19_&room=2_&shType=list",
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
    timeout=30,
    follow_redirects=True
)
print(f"Status: {r.status_code}, Length: {len(r.text)}")

soup = BeautifulSoup(r.text, "lxml")
scripts = soup.find_all("script")
print(f"Scripts: {len(scripts)}")

for i, s in enumerate(scripts):
    content = s.string or ""
    if "NUXT" in content:
        print(f"\nScript {i}: contains NUXT ({len(content)} chars)")
        idx = content.find("NUXT")
        print(f"  Context before: {content[max(0,idx-100):idx+50]}")
        # Find the full NUXT payload
        m = re.search(r"__NUXT__\s*=\s*(.+);\s*window\.", content, re.DOTALL)
        if m:
            raw = m.group(1).strip()
            print(f"  NUXT value type: {raw[:20]}...")
            print(f"  NUXT ends with: {raw[-100:]}")
            try:
                data = json.loads(raw)
                print(f"  PARSED: type={type(data).__name__}")
                if isinstance(data, dict):
                    print(f"  Keys: {list(data.keys())[:20]}")
                    # Recursively find posts
                    def find_posts(obj, depth=0):
                        if depth > 10:
                            return
                        if isinstance(obj, dict):
                            if "post_id" in obj:
                                print(f"  FOUND POST: {obj.get('post_id')} - {str(obj.get('title',''))[:50]}")
                                return True
                            for v in obj.values():
                                if find_posts(v, depth+1):
                                    return True
                        elif isinstance(obj, list) and len(obj) > 0:
                            print(f"  List({len(obj)}) at depth {depth}")
                            for item in obj[:3]:
                                if isinstance(item, dict):
                                    print(f"    Item keys: {list(item.keys())[:15]}")
                                    if "post_id" in item:
                                        print(f"    FOUND POST: {item.get('post_id')} - {str(item.get('title',''))[:50]}")
                                        return True
                            for item in obj:
                                if find_posts(item, depth+1):
                                    return True
                        return False
                    find_posts(data)
                elif isinstance(data, list):
                    print(f"  List length: {len(data)}")
                    if data and isinstance(data[0], dict):
                        print(f"  First item keys: {list(data[0].keys())[:15]}")
            except Exception as e:
                print(f"  Parse error: {e}")
                print(f"  Raw preview: {raw[:500]}")
        else:
            m2 = re.search(r"__NUXT__\s*=\s*(.{1,500})", content, re.DOTALL)
            if m2:
                print(f"  NUXT preview: {m2.group(1)[:300]}")
    elif len(content) > 100:
        if "post" in content[:500] or "house" in content[:500] or "list" in content[:500]:
            print(f"\nScript {i}: {len(content)} chars, preview: {content[:300]}")

# Also check for the fetch'd API URLs
fetch_urls = re.findall(r'[\"\'](\/home\/search\/[^\"\']+)[\"\']', r.text)
print(f"\nFetch URLs: {fetch_urls[:10]}")

# Check if the page has SSR data
for pattern in ["__NEXT_DATA__", "__NUXT__", "INITIAL_STATE", "serverData", "SSR_DATA"]:
    if pattern in r.text:
        print(f"Found {pattern}!")
