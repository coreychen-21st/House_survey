import sqlite3
import os
from datetime import datetime
from config.settings import DB_PATH


def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            house_id TEXT NOT NULL,
            title TEXT,
            address TEXT,
            district TEXT,
            total_price REAL,
            unit_price REAL,
            area_ping REAL,
            rooms INTEGER,
            halls INTEGER,
            baths REAL,
            building_age REAL,
            building_type TEXT,
            floor TEXT,
            image_urls TEXT,
            floorplan_url TEXT,
            url TEXT,
            description TEXT,
            listed_date TEXT,
            address_hash TEXT,
            image_hash TEXT,
            is_notified INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source, house_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notified_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER,
            notified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(listing_id) REFERENCES listings(id)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_listings_address_hash ON listings(address_hash)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_listings_image_hash ON listings(image_hash)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_listings_is_notified ON listings(is_notified)
    """)
    conn.commit()
    conn.close()


def listing_exists(source, house_id):
    conn = get_db()
    row = conn.execute(
        "SELECT id FROM listings WHERE source = ? AND house_id = ?",
        (source, house_id)
    ).fetchone()
    conn.close()
    return row is not None


def insert_listing(data):
    conn = get_db()
    try:
        conn.execute("""
            INSERT OR IGNORE INTO listings
            (source, house_id, title, address, district, total_price, unit_price,
             area_ping, rooms, halls, baths, building_age, building_type, floor,
             image_urls, floorplan_url, url, description, listed_date,
             address_hash, image_hash, is_notified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            data.get("source"), data.get("house_id"), data.get("title"),
            data.get("address"), data.get("district"), data.get("total_price"),
            data.get("unit_price"), data.get("area_ping"), data.get("rooms"),
            data.get("halls"), data.get("baths"), data.get("building_age"),
            data.get("building_type"), data.get("floor"),
            data.get("image_urls"), data.get("floorplan_url"), data.get("url"),
            data.get("description"), data.get("listed_date"),
            data.get("address_hash"), data.get("image_hash")
        ))
        conn.commit()
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    except Exception as e:
        conn.rollback()
        return None
    finally:
        conn.close()


def get_new_listings():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM listings WHERE is_notified = 0 ORDER BY total_price ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_notified(listing_id):
    conn = get_db()
    conn.execute(
        "UPDATE listings SET is_notified = 1 WHERE id = ?", (listing_id,)
    )
    conn.execute(
        "INSERT OR IGNORE INTO notified_listings (listing_id) VALUES (?)",
        (listing_id,)
    )
    conn.commit()
    conn.close()


def find_similar_by_address(address_hash, exclude_id=None):
    conn = get_db()
    if exclude_id:
        rows = conn.execute(
            "SELECT * FROM listings WHERE address_hash = ? AND id != ?",
            (address_hash, exclude_id)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM listings WHERE address_hash = ?",
            (address_hash,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_listing(listing_id):
    conn = get_db()
    conn.execute("DELETE FROM listings WHERE id = ?", (listing_id,))
    conn.commit()
    conn.close()
