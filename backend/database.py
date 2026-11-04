"""
SoleScout FDS - SQLite Database Setup & Schema Management
"""

import os
import sys
import sqlite3
from typing import Optional

# Ensure UTF-8 output encoding for console on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "solescout.db")


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Return a SQLite connection with row_factory set and foreign keys enabled."""
    target_path = db_path or DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[str] = None):
    """
    Create tables and indexes if they do not exist.
    Enforces the non-negotiable UNIQUE(product_id, collection_date) snapshot constraint.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS sneakers (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id    TEXT UNIQUE NOT NULL,
            sku           TEXT UNIQUE NOT NULL,
            name          TEXT NOT NULL,
            brand         TEXT,
            colorway      TEXT,
            retail_price  REAL,
            release_date  TEXT,
            image_url     TEXT,
            is_demo       INTEGER DEFAULT 0,
            fetched_at    TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS price_history (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            sneaker_id       INTEGER NOT NULL,
            product_id       TEXT NOT NULL,
            platform         TEXT NOT NULL,
            size             TEXT,
            price            REAL NOT NULL,
            condition        TEXT DEFAULT 'new',
            seller           TEXT,
            rating           REAL,
            collection_date  TEXT NOT NULL,
            is_demo          INTEGER DEFAULT 0,
            recorded_at      TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (sneaker_id) REFERENCES sneakers(id) ON DELETE CASCADE,
            CONSTRAINT uq_product_snapshot UNIQUE(product_id, collection_date)
        );

        CREATE TABLE IF NOT EXISTS normalized_sneakers (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id           TEXT NOT NULL,
            product_name         TEXT NOT NULL,
            brand                TEXT,
            model                TEXT,
            category             TEXT,
            price                REAL,
            currency             TEXT DEFAULT 'USD',
            retail_price         REAL,
            discount             REAL,
            size                 TEXT,
            condition            TEXT DEFAULT 'new',
            seller               TEXT,
            availability         TEXT,
            marketplace          TEXT,
            product_url          TEXT,
            image_url            TEXT,
            collection_date      TEXT NOT NULL,
            collection_timestamp TEXT NOT NULL,
            is_demo              INTEGER DEFAULT 0,
            CONSTRAINT uq_norm_product_snapshot UNIQUE(product_id, collection_date)
        );

        CREATE INDEX IF NOT EXISTS idx_sneakers_sku ON sneakers(sku);
        CREATE INDEX IF NOT EXISTS idx_sneakers_product_id ON sneakers(product_id);
        CREATE INDEX IF NOT EXISTS idx_price_history_product_date ON price_history(product_id, collection_date);
        CREATE INDEX IF NOT EXISTS idx_price_history_sneaker ON price_history(sneaker_id);
        CREATE INDEX IF NOT EXISTS idx_price_history_platform ON price_history(platform);
        CREATE INDEX IF NOT EXISTS idx_norm_product_date ON normalized_sneakers(product_id, collection_date);
        CREATE INDEX IF NOT EXISTS idx_norm_brand ON normalized_sneakers(brand);
    """)

    conn.commit()
    conn.close()
    target_path = db_path or DB_PATH
    try:
        print(f"[DB] Database initialized at: {os.path.abspath(target_path)}")
    except UnicodeEncodeError:
        print(f"[DB] Database initialized at: {os.path.abspath(target_path)}")
