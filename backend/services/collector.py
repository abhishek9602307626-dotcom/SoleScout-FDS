"""
SoleScout FDS - Sneaker Data Collector Service
Stage 3: Multi-Query, Multi-Page Data Collection & Snapshot Storage

Responsibilities:
1. Query SoleScout API for sneaker products across multiple brands/queries.
2. Support multi-page pagination with rate-limit adherence.
3. Normalize API responses strictly to available fields (NULL for missing).
4. Timestamp every snapshot with collection_date (YYYY-MM-DD) and collection_timestamp (ISO8601 UTC).
5. Persist raw API JSON snapshots to data/raw/.
6. Ingest normalized records into SQLite with UNIQUE(product_id, collection_date) constraint.
7. Export cleaned, standardized CSV snapshots to data/cleaned/.
8. Never overwrite historical records or invent fake data.
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Tuple
import pandas as pd

from database import get_connection
from services.solescout_api import SoleScoutClient, SoleScoutAPIError

logger = logging.getLogger("solescout.collector")

RAW_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw"))
CLEANED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "cleaned"))

DEFAULT_QUERIES = ["Jordan", "Nike Dunk", "adidas Samba", "New Balance 990", "Yeezy"]

NORMALIZED_COLUMNS = [
    "product_id",
    "product_name",
    "brand",
    "model",
    "category",
    "price",
    "currency",
    "retail_price",
    "discount",
    "size",
    "condition",
    "seller",
    "availability",
    "marketplace",
    "product_url",
    "image_url",
    "collection_date",
    "collection_timestamp",
]


def save_raw(data: Any, label: str = "fetch") -> str:
    """Save raw API response to data/raw/ with a timestamped filename."""
    os.makedirs(RAW_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    clean_label = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in label)
    filename = f"raw_solescout_{clean_label}_{timestamp}.json"
    filepath = os.path.join(RAW_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

    logger.info("Raw API snapshot saved to: %s", filepath)
    return filepath


def normalize_record(
    item: Dict[str, Any],
    collection_date: str,
    collection_timestamp: str,
) -> Dict[str, Any]:
    """
    Normalize a raw SoleScout product record into the standard analytical schema.
    Rule: Only use fields that exist in the response. If missing, store None (SQL NULL).
    Never invent fake values.
    """
    # 1. Product Identifier: style_code is the primary manufacturer SKU; fallback to slug
    style_code = item.get("style_code")
    slug = item.get("slug")
    product_id = (style_code.strip() if style_code else None) or (slug.strip() if slug else None)

    # 2. Product Name / Title
    product_name = item.get("title") or item.get("name")
    if product_name:
        product_name = product_name.strip()

    # 3. Brand
    brand = item.get("brand")
    if brand:
        brand = brand.strip()

    # 4. Model (SoleScout returns model in title)
    model = product_name

    # 5. Category (shoes, clothing, accessories, etc.)
    category = item.get("category")

    # 6. Prices
    def _to_float(v: Any) -> Optional[float]:
        if v is None:
            return None
        try:
            val = float(v)
            return round(val, 2) if val > 0 else None
        except (ValueError, TypeError):
            return None

    price = _to_float(item.get("lowest_price_usd") or item.get("price"))
    retail_price = _to_float(item.get("retail_price_usd") or item.get("retail_price"))

    # 7. Currency
    currency = "USD" if (price is not None or retail_price is not None) else None

    # 8. Discount (retail_price - price if discounted below retail)
    discount = None
    if retail_price is not None and price is not None and retail_price > price:
        discount = round(retail_price - price, 2)

    # 9. Size, Seller, Condition (Search level is aggregate deadstock/new)
    size = None  # Specific size is under per-size detail
    condition = "new"
    seller = None  # Aggregate listing; specific store names under /product endpoint

    # 10. Availability & Marketplace
    availability = "in_stock" if price is not None else "out_of_stock"
    marketplace = "SoleScout Aggregator"

    # 11. URLs
    product_url = item.get("url")
    image_url = item.get("image")

    return {
        "product_id": product_id,
        "product_name": product_name,
        "brand": brand,
        "model": model,
        "category": category,
        "price": price,
        "currency": currency,
        "retail_price": retail_price,
        "discount": discount,
        "size": size,
        "condition": condition,
        "seller": seller,
        "availability": availability,
        "marketplace": marketplace,
        "product_url": product_url,
        "image_url": image_url,
        "collection_date": collection_date,
        "collection_timestamp": collection_timestamp,
    }


def save_to_sqlite(
    records: List[Dict[str, Any]],
    db_path: Optional[str] = None,
) -> Tuple[int, int]:
    """
    Save normalized records to SQLite database.
    Enforces:
    - UNIQUE(product_id, collection_date) to prevent duplicate snapshots.
    - Historical records are never overwritten (INSERT OR IGNORE).
    - Populates both `normalized_sneakers` and relational `sneakers`/`price_history`.

    Returns (inserted_count, ignored_duplicate_count).
    """
    if not records:
        return 0, 0

    conn = get_connection(db_path)
    cursor = conn.cursor()

    inserted_count = 0
    ignored_count = 0

    try:
        for r in records:
            pid = r.get("product_id")
            pname = r.get("product_name")
            cdate = r.get("collection_date")
            if not pid or not pname or not cdate:
                continue

            # 1. Insert into normalized_sneakers table
            cursor.execute(
                """
                INSERT OR IGNORE INTO normalized_sneakers (
                    product_id, product_name, brand, model, category,
                    price, currency, retail_price, discount, size,
                    condition, seller, availability, marketplace,
                    product_url, image_url, collection_date, collection_timestamp, is_demo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    pid,
                    pname,
                    r.get("brand"),
                    r.get("model"),
                    r.get("category"),
                    r.get("price"),
                    r.get("currency"),
                    r.get("retail_price"),
                    r.get("discount"),
                    r.get("size"),
                    r.get("condition"),
                    r.get("seller"),
                    r.get("availability"),
                    r.get("marketplace"),
                    r.get("product_url"),
                    r.get("image_url"),
                    cdate,
                    r.get("collection_timestamp"),
                ),
            )
            was_inserted = cursor.rowcount > 0

            # 2. Insert into relational sneakers table
            cursor.execute(
                """
                INSERT INTO sneakers (
                    product_id, sku, name, brand, retail_price, image_url, is_demo
                ) VALUES (?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT(product_id) DO UPDATE SET
                    retail_price = COALESCE(excluded.retail_price, sneakers.retail_price),
                    image_url = COALESCE(excluded.image_url, sneakers.image_url)
                """,
                (
                    pid,
                    pid,
                    pname,
                    r.get("brand"),
                    r.get("retail_price"),
                    r.get("image_url"),
                ),
            )
            sneaker_id = cursor.execute(
                "SELECT id FROM sneakers WHERE product_id = ?", (pid,)
            ).fetchone()[0]

            # 3. Insert into price_history table if price exists
            if r.get("price") is not None:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO price_history (
                        sneaker_id, product_id, platform, price,
                        condition, seller, collection_date, is_demo
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                    """,
                    (
                        sneaker_id,
                        pid,
                        r.get("marketplace", "SoleScout"),
                        r["price"],
                        r.get("condition", "new"),
                        r.get("seller"),
                        cdate,
                    ),
                )

            if was_inserted:
                inserted_count += 1
            else:
                ignored_count += 1

        conn.commit()
    finally:
        conn.close()

    return inserted_count, ignored_count


def export_cleaned_csv(records: List[Dict[str, Any]]) -> Tuple[str, str]:
    """
    Export normalized records to CSV in data/cleaned/.
    Creates both a timestamped archive CSV and updates `sneakers_cleaned_latest.csv`.
    """
    os.makedirs(CLEANED_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    df = pd.DataFrame(records)
    # Ensure all standard columns are present in consistent order
    for col in NORMALIZED_COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[NORMALIZED_COLUMNS]

    # Timestamped archive file
    archive_path = os.path.join(CLEANED_DIR, f"sneakers_cleaned_{timestamp}.csv")
    df.to_csv(archive_path, index=False, encoding="utf-8")

    # Latest overwrite pointer file
    latest_path = os.path.join(CLEANED_DIR, "sneakers_cleaned_latest.csv")
    df.to_csv(latest_path, index=False, encoding="utf-8")

    logger.info("Exported %d records to CSV: %s", len(df), archive_path)
    return archive_path, latest_path


def collect(
    query: Optional[Union[str, List[str]]] = None,
    limit: int = 10,
    max_pages: int = 1,
    db_path: Optional[str] = None,
    allow_anonymous: bool = False,
) -> Dict[str, Any]:
    """
    Main Data Collection Pipeline.

    Parameters:
    - query: A single search string (e.g. "Jordan") or list of queries/brands.
    - limit: Results per page (min 1, max 25).
    - max_pages: Number of pages to retrieve per query (for pagination).
    - db_path: Optional SQLite DB path (defaults to solescout.db).
    - allow_anonymous: If True, allows key-less access using SoleScout public tier.

    Process:
    1. Queries SoleScout API.
    2. Collects raw responses across pages and queries.
    3. Saves raw JSON snapshots to data/raw/.
    4. Normalizes every record with collection_date and timestamp.
    5. Saves records to SQLite (enforcing uniqueness, preventing overwrites).
    6. Exports cleaned CSV snapshots to data/cleaned/.
    """
    client = SoleScoutClient(allow_anonymous=allow_anonymous)

    # Required check: if unconfigured and anonymous access not requested, return guidance
    if not client.is_configured() and not allow_anonymous:
        return {
            "status": "unconfigured",
            "message": (
                "No SoleScout data has been collected yet. "
                "Configure the API and run the collector."
            ),
            "records_collected": 0,
            "raw_file": None,
        }

    # Normalize queries list
    if query is None:
        queries = ["Jordan 1"]
    elif isinstance(query, str):
        # Support comma-separated strings
        queries = [q.strip() for q in query.split(",") if q.strip()]
    else:
        queries = list(query)

    now_utc = datetime.now(timezone.utc)
    collection_date = now_utc.strftime("%Y-%m-%d")
    collection_timestamp = now_utc.isoformat()

    all_raw_items: List[Dict[str, Any]] = []
    saved_raw_files: List[str] = []
    total_pages_fetched = 0

    logger.info(
        "Starting data collection for %d queries (pages: %d, limit: %d)",
        len(queries), max_pages, limit
    )

    try:
        for q in queries:
            query_raw_items: List[Dict[str, Any]] = []

            for page in range(1, max_pages + 1):
                logger.info("Fetching query='%s', page=%d, limit=%d", q, page, limit)
                resp = client.search_products(query=q, page=page, limit=limit)
                total_pages_fetched += 1

                results = resp.get("results", [])
                if not results:
                    logger.info("No more results for query='%s' at page %d", q, page)
                    break

                query_raw_items.extend(results)
                all_raw_items.extend(results)

                # Stop early if we have fetched all catalog results for this query
                total_catalog = resp.get("total", 0)
                if len(query_raw_items) >= total_catalog:
                    break

            # Save raw snapshot for this query
            if query_raw_items:
                raw_payload = {
                    "query": q,
                    "collection_date": collection_date,
                    "collection_timestamp": collection_timestamp,
                    "pages_fetched": total_pages_fetched,
                    "count": len(query_raw_items),
                    "items": query_raw_items,
                    "source": "SoleScout",
                }
                raw_path = save_raw(raw_payload, label=f"query_{q.replace(' ', '_')}")
                saved_raw_files.append(raw_path)

        if not all_raw_items:
            return {
                "status": "success",
                "message": "Collector ran successfully but no matching products were returned.",
                "queries_used": queries,
                "records_collected": 0,
                "snapshots_inserted": 0,
                "snapshots_ignored": 0,
                "raw_file": None,
                "csv_file": None,
            }

        # Normalize all records
        normalized_records: List[Dict[str, Any]] = []
        for item in all_raw_items:
            norm = normalize_record(item, collection_date, collection_timestamp)
            if norm.get("product_id") and norm.get("product_name"):
                normalized_records.append(norm)

        # Ingest into SQLite database
        inserted_count, ignored_count = save_to_sqlite(normalized_records, db_path=db_path)

        # Export to CSV
        archive_csv, latest_csv = export_cleaned_csv(normalized_records)

        return {
            "status": "success",
            "message": f"Successfully collected {len(all_raw_items)} records ({inserted_count} new snapshots inserted, {ignored_count} duplicates ignored).",
            "queries_used": queries,
            "pages_fetched": total_pages_fetched,
            "records_collected": len(all_raw_items),
            "records_normalized": len(normalized_records),
            "snapshots_inserted": inserted_count,
            "snapshots_ignored": ignored_count,
            "raw_files": saved_raw_files,
            "raw_file": saved_raw_files[0] if saved_raw_files else None,
            "csv_file": archive_csv,
            "latest_csv_file": latest_csv,
            "normalized_sample": normalized_records[:3],
        }

    except SoleScoutAPIError as e:
        logger.error("SoleScout API Error during collection: %s", e)
        return {
            "status": "error",
            "message": f"SoleScout API Error: {str(e)}",
            "records_collected": 0,
            "raw_file": None,
        }
    except Exception as e:
        logger.error("Unexpected error during collection: %s", e, exc_info=True)
        return {
            "status": "error",
            "message": f"Unexpected error during collection: {str(e)}",
            "records_collected": 0,
            "raw_file": None,
        }


# ---------------------------------------------------------------------------
# Demo / Sample Data Generation (Isolated with is_demo=1)
# ---------------------------------------------------------------------------

def seed_demo_data(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Populate clearly marked sample data (is_demo=1).
    NON-NEGOTIABLE RULES:
    - Clearly labeled 'Demo/Sample Data'.
    - Must be switchable off.
    - Preserves UNIQUE(product_id, collection_date) constraint.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    demo_sneakers = [
        {
            "product_id": "DZ5485-612",
            "sku": "DZ5485-612",
            "name": "Air Jordan 1 Retro High OG 'Chicago Lost & Found'",
            "brand": "Air Jordan",
            "colorway": "Varsity Red/Black/Sail/Muslin",
            "retail_price": 180.0,
            "release_date": "2022-11-19",
            "image_url": "https://images.unsplash.com/photo-1552346154-21d32810aba3?auto=format&fit=crop&w=600&q=80",
            "is_demo": 1,
            "prices": [
                {"platform": "StockX", "price": 380.0, "date": "2026-02-15", "size": "10.5", "seller": "Verified SneakerHub"},
                {"platform": "GOAT", "price": 395.0, "date": "2026-02-16", "size": "10.5", "seller": "TopRatedKicks"},
                {"platform": "Flight Club", "price": 420.0, "date": "2026-02-17", "size": "10.5", "seller": "NYC Retail"},
                {"platform": "StockX", "price": 410.0, "date": "2026-02-20", "size": "10.5", "seller": "DirectSneakers"},
                {"platform": "GOAT", "price": 425.0, "date": "2026-02-25", "size": "10.5", "seller": "KicksEmpire"},
                {"platform": "StockX", "price": 435.0, "date": "2026-03-01", "size": "10.5", "seller": "ChicagoVault"},
                {"platform": "eBay", "price": 650.0, "date": "2026-03-02", "size": "10.5", "seller": "HypeBeastResell"},
            ],
        },
        {
            "product_id": "DH6927-140",
            "sku": "DH6927-140",
            "name": "Air Jordan 4 Retro 'Military Blue' (2024)",
            "brand": "Air Jordan",
            "colorway": "Off-White/Military Blue/Neutral Grey",
            "retail_price": 215.0,
            "release_date": "2024-05-04",
            "image_url": "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?auto=format&fit=crop&w=600&q=80",
            "is_demo": 1,
            "prices": [
                {"platform": "StockX", "price": 275.0, "date": "2026-02-10", "size": "10", "seller": "SoleTrader"},
                {"platform": "GOAT", "price": 285.0, "date": "2026-02-14", "size": "10", "seller": "SoleTrader"},
                {"platform": "Flight Club", "price": 310.0, "date": "2026-02-18", "size": "10", "seller": "FC Los Angeles"},
                {"platform": "StockX", "price": 290.0, "date": "2026-02-22", "size": "10", "seller": "QuickDrop"},
                {"platform": "GOAT", "price": 295.0, "date": "2026-02-26", "size": "10", "seller": "PrimePairs"},
                {"platform": "StockX", "price": 305.0, "date": "2026-03-01", "size": "10", "seller": "CollectorVault"},
            ],
        },
        {
            "product_id": "DD1391-100",
            "sku": "DD1391-100",
            "name": "Nike Dunk Low Retro 'White Black Panda'",
            "brand": "Nike",
            "colorway": "White/Black",
            "retail_price": 115.0,
            "release_date": "2021-03-10",
            "image_url": "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?auto=format&fit=crop&w=600&q=80",
            "is_demo": 1,
            "prices": [
                {"platform": "StockX", "price": 135.0, "date": "2026-02-01", "size": "9.5", "seller": "PandaWorld"},
                {"platform": "GOAT", "price": 140.0, "date": "2026-02-08", "size": "9.5", "seller": "KickStart"},
                {"platform": "StockX", "price": 130.0, "date": "2026-02-15", "size": "9.5", "seller": "StockSaver"},
                {"platform": "Flight Club", "price": 150.0, "date": "2026-02-20", "size": "9.5", "seller": "FC NYC"},
                {"platform": "StockX", "price": 125.0, "date": "2026-02-28", "size": "9.5", "seller": "ResellHub"},
                {"platform": "eBay", "price": 60.0, "date": "2026-03-01", "size": "9.5", "seller": "ClearanceStore"},
            ],
        },
        {
            "product_id": "B37571",
            "sku": "B37571",
            "name": "adidas Yeezy Boost 350 V2 'Blue Tint'",
            "brand": "adidas",
            "colorway": "Blue Tint/Grey Three/High Res Red",
            "retail_price": 230.0,
            "release_date": "2017-12-16",
            "image_url": "https://images.unsplash.com/photo-1608231387042-66d1773070a5?auto=format&fit=crop&w=600&q=80",
            "is_demo": 1,
            "prices": [
                {"platform": "StockX", "price": 310.0, "date": "2026-02-05", "size": "11", "seller": "YeezySupplyArch"},
                {"platform": "GOAT", "price": 320.0, "date": "2026-02-12", "size": "11", "seller": "BoostZone"},
                {"platform": "Flight Club", "price": 345.0, "date": "2026-02-19", "size": "11", "seller": "FC Miami"},
                {"platform": "StockX", "price": 315.0, "date": "2026-02-24", "size": "11", "seller": "YeezyPlug"},
                {"platform": "StockX", "price": 325.0, "date": "2026-03-01", "size": "11", "seller": "OGCollector"},
            ],
        },
        {
            "product_id": "M990GL6",
            "sku": "M990GL6",
            "name": "New Balance 990v6 Made in USA 'Grey'",
            "brand": "New Balance",
            "colorway": "Grey/Castlerock",
            "retail_price": 200.0,
            "release_date": "2022-11-04",
            "image_url": "https://images.unsplash.com/photo-1539185441755-769473a23570?auto=format&fit=crop&w=600&q=80",
            "is_demo": 1,
            "prices": [
                {"platform": "StockX", "price": 195.0, "date": "2026-02-02", "size": "10", "seller": "BostonRun"},
                {"platform": "GOAT", "price": 205.0, "date": "2026-02-10", "size": "10", "seller": "DadShoeCentral"},
                {"platform": "Flight Club", "price": 220.0, "date": "2026-02-18", "size": "10", "seller": "FC NYC"},
                {"platform": "StockX", "price": 200.0, "date": "2026-02-25", "size": "10", "seller": "NBDistributor"},
                {"platform": "StockX", "price": 210.0, "date": "2026-03-01", "size": "10", "seller": "SneakerOutlet"},
            ],
        },
    ]

    inserted_sneakers = 0
    inserted_snapshots = 0
    ignored_snapshots = 0

    try:
        for s in demo_sneakers:
            cursor.execute(
                """
                INSERT INTO sneakers (product_id, sku, name, brand, colorway, retail_price, release_date, image_url, is_demo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                ON CONFLICT(product_id) DO UPDATE SET
                    retail_price=excluded.retail_price,
                    image_url=excluded.image_url
                """,
                (
                    s["product_id"],
                    s["sku"],
                    s["name"],
                    s["brand"],
                    s["colorway"],
                    s["retail_price"],
                    s["release_date"],
                    s["image_url"],
                ),
            )
            sneaker_id = cursor.execute(
                "SELECT id FROM sneakers WHERE product_id = ?", (s["product_id"],)
            ).fetchone()[0]
            inserted_sneakers += 1

            for p in s["prices"]:
                # Insert to price_history
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO price_history
                    (sneaker_id, product_id, platform, price, size, seller, collection_date, is_demo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                    """,
                    (
                        sneaker_id,
                        s["product_id"],
                        p["platform"],
                        p["price"],
                        p.get("size"),
                        p.get("seller"),
                        p["date"],
                    ),
                )
                if cursor.rowcount > 0:
                    inserted_snapshots += 1
                else:
                    ignored_snapshots += 1

                # Also insert to normalized_sneakers
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO normalized_sneakers (
                        product_id, product_name, brand, model, category,
                        price, currency, retail_price, discount, size,
                        condition, seller, availability, marketplace,
                        product_url, image_url, collection_date, collection_timestamp, is_demo
                    ) VALUES (?, ?, ?, ?, 'shoes', ?, 'USD', ?, ?, ?, 'new', ?, 'in_stock', ?, ?, ?, ?, ?, 1)
                    """,
                    (
                        s["product_id"],
                        s["name"],
                        s["brand"],
                        s["name"],
                        p["price"],
                        s["retail_price"],
                        round(s["retail_price"] - p["price"], 2) if s["retail_price"] > p["price"] else None,
                        p.get("size"),
                        p.get("seller"),
                        p["platform"],
                        None,
                        s.get("image_url"),
                        p["date"],
                        f"{p['date']}T12:00:00Z",
                    ),
                )

        conn.commit()
    finally:
        conn.close()

    return {
        "status": "success",
        "label": "Demo/Sample Data",
        "demo_sneakers_loaded": inserted_sneakers,
        "demo_snapshots_loaded": inserted_snapshots,
        "duplicates_ignored": ignored_snapshots,
    }


def clear_demo_data(db_path: Optional[str] = None) -> int:
    """Removes all demo/sample records, leaving only real SoleScout data."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM normalized_sneakers WHERE is_demo = 1")
        cursor.execute("DELETE FROM price_history WHERE is_demo = 1")
        deleted_snapshots = cursor.rowcount
        cursor.execute("DELETE FROM sneakers WHERE is_demo = 1")
        deleted_sneakers = cursor.rowcount
        conn.commit()
        return deleted_sneakers
    finally:
        conn.close()
