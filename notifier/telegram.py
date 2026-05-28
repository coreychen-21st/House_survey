import time
import httpx
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def format_listing_message(listing):
    source_emoji = {"sinyi": "🏠", "yungching": "🏘️", "591": "🏡"}
    emoji = source_emoji.get(listing.get("source"), "🏠")

    msg_parts = [
        f"{emoji} *{listing.get('title', '無標題')}*",
        "",
        f"📍 *地址*: {listing.get('address', 'N/A')}",
        f"💰 *總價*: {listing.get('total_price', 0):,.0f} 萬",
    ]

    if listing.get("unit_price"):
        msg_parts.append(f"💵 *單價*: {listing.get('unit_price', 0):.2f} 萬/坪")

    if listing.get("area_ping"):
        msg_parts.append(f"📐 *坪數*: {listing.get('area_ping', 0):.1f} 坪")

    room_str = f"{int(listing.get('rooms', 0))}房" if listing.get('rooms') else ""
    hall_str = f"{int(listing.get('halls', 0))}廳" if listing.get('halls') else ""
    bath_str = f"{listing.get('baths', 0)}衛" if listing.get('baths') else ""
    layout = f"{room_str}{hall_str}{bath_str}"
    if layout:
        msg_parts.append(f"🏗️ *格局*: {layout}")

    msg_parts.append(f"📅 *屋齡*: {listing.get('building_age', 'N/A')} 年")
    msg_parts.append(f"🏢 *類型*: {listing.get('building_type', 'N/A')}")

    floor = listing.get('floor', '')
    if floor:
        msg_parts.append(f"🔢 *樓層*: {floor}")

    if listing.get("description"):
        desc = listing["description"][:100]
        msg_parts.append(f"📝 _{desc}_")

    msg_parts.append("")
    msg_parts.append(f"🔗 [查看詳情]({listing.get('url', '')})")
    msg_parts.append(f"📋 來源: {listing.get('source', 'N/A')}")

    return "\n".join(msg_parts)


def _send_telegram_message(text, parse_mode="Markdown", disable_web_page_preview=False):
    if not TELEGRAM_CHAT_ID:
        print("[TG] 未設定 TELEGRAM_CHAT_ID，略過發送")
        return None

    with httpx.Client(timeout=30) as client:
        resp = client.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": disable_web_page_preview
            }
        )
        return resp.json()


def _send_photo_with_caption(image_url, caption):
    if not TELEGRAM_CHAT_ID:
        print("[TG] 未設定 TELEGRAM_CHAT_ID，略過發送")
        return None

    with httpx.Client(timeout=30) as client:
        resp = client.post(
            f"{TELEGRAM_API}/sendPhoto",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "photo": image_url,
                "caption": caption,
                "parse_mode": "Markdown"
            }
        )
        return resp.json()


def notify_listing(listing):
    caption = format_listing_message(listing)
    image_urls = listing.get("image_urls", "")
    first_img = image_urls.split(",")[0] if image_urls else ""

    if first_img and first_img.startswith("http"):
        try:
            result = _send_photo_with_caption(first_img, caption)
            if result and result.get("ok"):
                return result
        except Exception:
            pass

    return _send_telegram_message(caption)


def notify_batch(listings):
    if not TELEGRAM_CHAT_ID:
        print("[TG] 未設定 TELEGRAM_CHAT_ID，略過發送")
        return

    if not listings:
        print("[TG] 沒有新物件需要通知")
        return

    _send_telegram_message(
        f"🏠 *House Survey 新物件通知*\n"
        f"共發現 {len(listings)} 個符合條件的新物件\n"
        f"已過濾重複、凶宅、海砂屋等問題物件"
    )

    for listing in listings[:20]:
        try:
            notify_listing(listing)
            time.sleep(1)
        except Exception as e:
            print(f"[TG] 發送失敗: {e}")
