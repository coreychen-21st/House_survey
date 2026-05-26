import httpx

# Try different user-agents and approaches
headers_pairs = [
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
     "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
     "Accept-Encoding": "gzip, deflate, br",
     "Referer": "https://www.google.com/",
     "Sec-Ch-Ua": '"Chromium";v="120"',
     "Sec-Ch-Ua-Mobile": "?0",
     "Sec-Ch-Ua-Platform": '"Windows"',
    },
    {"User-Agent": "houseprice-crawler/1.0"},
    {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"},
]

for headers in headers_pairs:
    try:
        r = httpx.get("https://www.houseprice.tw/", headers=headers, timeout=15, follow_redirects=True)
        print(f"Status: {r.status_code} | UA: {str(headers.get('User-Agent',''))[:60]}")
        if r.status_code == 200:
            print(f"  Length: {len(r.text)}")
            break
    except Exception as e:
        print(f"Error: {e} | UA: {str(headers.get('User-Agent',''))[:60]}")
