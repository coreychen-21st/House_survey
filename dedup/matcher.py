from dedup.address_norm import address_fingerprint
from storage.database import (
    get_db, find_similar_by_address, delete_listing,
    listing_exists, insert_listing, get_new_listings, mark_notified
)


def deduplicate_cross_source(listings):
    """
    跨站去重：
    1. 相同 address_hash → 保留總價最低的
    2. 相同 image_hash → 保留總價最低的（輔助）
    """
    grouped = {}
    for item in listings:
        addr_hash = item.get("address_hash", "")
        img_hash = item.get("image_hash", "")

        key = addr_hash if addr_hash else f"img:{img_hash}" if img_hash else f"url:{item.get('url', id(item))}"

        if key not in grouped:
            grouped[key] = item
        else:
            existing = grouped[key]
            if item.get("total_price", 0) < existing.get("total_price", 0):
                grouped[key] = item

    deduped = list(grouped.values())
    deduped.sort(key=lambda x: x.get("total_price", 0))
    return deduped


def merge_and_deduplicate(all_listings):
    """
    合併所有來源 + 跨站去重 + 與歷史資料比對
    - 跨來源去重：同 address_hash 只保留最低價
    - 歷史去重：相同 (source, house_id) 已存在則跳過
    - 價格檢查：同地址已通知過才跳過（除非降價）
    """
    if not all_listings:
        return []

    deduped = deduplicate_cross_source(all_listings)

    final = []
    for item in deduped:
        source = item.get("source", "")
        house_id = item.get("house_id", "")

        # 相同來源 + 相同 ID → 已收錄過，跳過
        if source and house_id and listing_exists(source, house_id):
            continue

        # 同地址曾通知過 → 僅在降價時才重新通知
        addr_hash = item.get("address_hash", "")
        if addr_hash:
            existing = find_similar_by_address(addr_hash)
            if existing:
                # 只看已通知的歷史紀錄
                existing_notified = [e for e in existing if e.get("is_notified")]
                if existing_notified:
                    min_notified_price = min(e["total_price"] for e in existing_notified)
                    if item["total_price"] >= min_notified_price:
                        continue

        final.append(item)

    return final


def process_and_store(all_listings):
    deduped = merge_and_deduplicate(all_listings)
    stored_ids = []
    for item in deduped:
        lid = insert_listing(item)
        if lid:
            stored_ids.append(lid)
    return stored_ids
