import httpx
import json

r = httpx.post(
    "https://www.houseprice.tw/ws/buygetWebCase/",
    json={"City": "台北市", "LTotalPrice": 300, "HTotalPrice": 1300,
          "BuildPinMin": 19, "RoomMin": 2, "BuildAgeMax": 46,
          "Page": 1, "Rows": 5},
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json",
        "Referer": "https://www.houseprice.tw/",
        "Origin": "https://www.houseprice.tw",
    },
    timeout=30
)
data = r.json()
with open("D:\\House_survey\\hp_response.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Status: {r.status_code}")
print(f"Keys: {list(data.keys())}")
cases = data.get("webCaseGroupings", [])
print(f"Cases: {len(cases)}")
if cases:
    c = cases[0]
    print(f"\nFirst case keys: {list(c.keys())}")
    for k, v in c.items():
        if isinstance(v, (str, int, float)):
            print(f"  {k}: {v}")
        elif isinstance(v, list):
            print(f"  {k}: list[{len(v)}] - {v[:3]}")
        elif isinstance(v, dict):
            print(f"  {k}: dict keys={list(v.keys())[:5]}")
