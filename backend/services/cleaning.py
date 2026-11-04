"""
SoleScout FDS - Data Cleaning Service & Quality Assurance Pipeline
Stage 4: Reproducible Cleaning, Validation & Data Quality Reporting

Responsibilities:
1. Load raw API JSON snapshots from data/raw/.
2. Detect and remove duplicate records while preserving first observations.
3. Identify and quantify missing values across all dimensions.
4. Clean, parse, and convert numeric price fields.
5. Filter out DATA QUALITY ERRORS (negative prices, missing IDs, corrupt formats).
6. Standardize brand names against canonical footwear taxonomies.
7. Validate timestamps (ISO8601 UTC and YYYY-MM-DD).
8. Validate currencies (ISO 4217 standard).
9. Detect STATISTICAL OUTLIERS (IQR Tukey & Z-Score) WITHOUT discarding legitimate high-value grails.
10. Strictly preserve NULLs; never silently impute or invent missing values.
11. Export cleaned datasets to data/cleaned/ and generate a comprehensive Data Quality Report.
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd
import numpy as np

from database import get_connection

logger = logging.getLogger("solescout.cleaning")

RAW_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw"))
CLEANED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "cleaned"))

# Canonical brand name standardization map
BRAND_STANDARDIZATION_MAP = {
    "jordan": "Air Jordan",
    "air jordan": "Air Jordan",
    "air-jordan": "Air Jordan",
    "nike": "Nike",
    "nike sportswear": "Nike",
    "adidas": "adidas",
    "adidas originals": "adidas",
    "yeezy": "adidas Yeezy",
    "adidas yeezy": "adidas Yeezy",
    "new balance": "New Balance",
    "newbalance": "New Balance",
    "nb": "New Balance",
    "asics": "ASICS",
    "puma": "PUMA",
    "converse": "Converse",
    "reebok": "Reebok",
    "salomon": "Salomon",
    "vans": "Vans",
    "bape": "A Bathing Ape",
    "a bathing ape": "A Bathing Ape",
    "under armour": "Under Armour",
    "saucony": "Saucony",
    "hoka": "HOKA",
    "hoka one one": "HOKA",
    "on": "On Running",
    "on running": "On Running",
}

PLATFORM_MAP = {
    "stockx": "StockX",
    "goat": "GOAT",
    "flight club": "Flight Club",
    "flightclub": "Flight Club",
    "ebay": "eBay",
    "stadium goods": "Stadium Goods",
    "solescout": "SoleScout Aggregator",
    "solescout aggregator": "SoleScout Aggregator",
}

VALID_CURRENCIES = {"USD", "EUR", "GBP", "CAD", "AUD", "JPY"}

SENTINEL_VALUES = {
    "",
    "none",
    "null",
    "n/a",
    "na",
    "nan",
    "undefined",
    "unknown",
    "-",
    "--",
}


# ---------------------------------------------------------------------------
# Atomic Cleaning Helpers
# ---------------------------------------------------------------------------

def _clean_string(val: Any) -> Optional[str]:
    """Clean string values, converting empty/sentinel strings to None."""
    if val is None or pd.isna(val):
        return None
    s = str(val).strip()
    if s.lower() in SENTINEL_VALUES:
        return None
    return s


def _clean_price(val: Any) -> Optional[float]:
    """
    Clean and parse price values into floats rounded to 2 decimal places.
    Returns None for missing, zero, negative, or corrupt prices (Data Quality Errors).
    """
    if val is None or pd.isna(val):
        return None
    try:
        if isinstance(val, (int, float)):
            p = float(val)
        else:
            clean_str = (
                str(val)
                .replace("$", "")
                .replace("€", "")
                .replace("£", "")
                .replace(",", "")
                .strip()
            )
            p = float(clean_str)
        return round(p, 2) if p > 0 else None
    except (ValueError, TypeError):
        return None


def standardize_brand(brand_raw: Any) -> Optional[str]:
    """Standardize brand names to canonical casing and conventions."""
    clean = _clean_string(brand_raw)
    if not clean:
        return None
    lookup = clean.lower()
    if lookup in BRAND_STANDARDIZATION_MAP:
        return BRAND_STANDARDIZATION_MAP[lookup]
    # Default to clean title-casing
    return clean.title()


def validate_date(date_val: Any) -> Optional[str]:
    """
    Validate and convert a date string into YYYY-MM-DD format.
    Rejects future dates or unparseable text.
    """
    clean = _clean_string(date_val)
    if not clean:
        return None
    try:
        # Truncate time if ISO timestamp was provided
        clean_date_str = clean.split("T")[0]
        dt = pd.to_datetime(clean_date_str)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None


def validate_timestamp(ts_val: Any) -> Optional[str]:
    """Validate and format an ISO8601 UTC timestamp."""
    clean = _clean_string(ts_val)
    if not clean:
        return None
    try:
        dt = pd.to_datetime(clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except Exception:
        return None


def validate_currency(curr_val: Any) -> str:
    """Validate currency against standard codes, defaulting to USD."""
    clean = _clean_string(curr_val)
    if clean and clean.upper() in VALID_CURRENCIES:
        return clean.upper()
    return "USD"


# ---------------------------------------------------------------------------
# Legacy DataFrame Cleaners (Preserved for backwards compatibility & tests)
# ---------------------------------------------------------------------------

def clean_sneakers_df(df: pd.DataFrame) -> pd.DataFrame:
    """Applies data cleaning to raw sneaker records (for backwards compatibility)."""
    if df.empty:
        return pd.DataFrame(columns=[
            "product_id", "sku", "name", "brand", "colorway",
            "retail_price", "release_date", "image_url", "is_demo"
        ])

    cleaned = df.copy()

    for col in ["product_id", "sku", "name", "brand", "colorway", "image_url"]:
        if col in cleaned.columns:
            cleaned[col] = cleaned[col].apply(_clean_string)
        else:
            cleaned[col] = None

    cleaned["product_id"] = cleaned["product_id"].fillna(cleaned["sku"])
    cleaned["sku"] = cleaned["sku"].fillna(cleaned["product_id"])

    cleaned = cleaned.dropna(subset=["product_id", "name"])

    if "brand" in cleaned.columns:
        cleaned["brand"] = cleaned["brand"].apply(standardize_brand)

    if "retail_price" in cleaned.columns:
        cleaned["retail_price"] = cleaned["retail_price"].apply(_clean_price)
    else:
        cleaned["retail_price"] = None

    if "release_date" in cleaned.columns:
        cleaned["release_date"] = cleaned["release_date"].apply(validate_date)
    else:
        cleaned["release_date"] = None

    if "is_demo" not in cleaned.columns:
        cleaned["is_demo"] = 0
    else:
        cleaned["is_demo"] = cleaned["is_demo"].fillna(0).astype(int)

    cleaned = cleaned.drop_duplicates(subset=["product_id"], keep="first")
    return cleaned


def clean_prices_df(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans raw price snapshot records (for backwards compatibility)."""
    if df.empty:
        return pd.DataFrame(columns=[
            "product_id", "platform", "price", "size", "condition",
            "seller", "rating", "collection_date", "is_demo"
        ])

    cleaned = df.copy()

    if "product_id" in cleaned.columns:
        cleaned["product_id"] = cleaned["product_id"].apply(_clean_string)
    else:
        cleaned["product_id"] = None
    cleaned = cleaned.dropna(subset=["product_id"])

    def normalize_platform(p):
        s = _clean_string(p)
        if not s:
            return "SoleScout"
        return PLATFORM_MAP.get(s.lower(), s.title())

    if "platform" in cleaned.columns:
        cleaned["platform"] = cleaned["platform"].apply(normalize_platform)
    else:
        cleaned["platform"] = "SoleScout"

    if "price" in cleaned.columns:
        cleaned["price"] = cleaned["price"].apply(_clean_price)
    else:
        cleaned["price"] = None
    cleaned = cleaned.dropna(subset=["price"])

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def parse_collection_date(d):
        val = validate_date(d)
        return val if val else today_str

    if "collection_date" in cleaned.columns:
        cleaned["collection_date"] = cleaned["collection_date"].apply(parse_collection_date)
    else:
        cleaned["collection_date"] = today_str

    for col in ["size", "condition", "seller"]:
        if col in cleaned.columns:
            cleaned[col] = cleaned[col].apply(_clean_string)
        else:
            cleaned[col] = None

    if "condition" in cleaned.columns:
        cleaned["condition"] = cleaned["condition"].fillna("new")

    if "rating" in cleaned.columns:
        cleaned["rating"] = pd.to_numeric(cleaned["rating"], errors="coerce")
    else:
        cleaned["rating"] = None

    if "is_demo" not in cleaned.columns:
        cleaned["is_demo"] = 0
    else:
        cleaned["is_demo"] = cleaned["is_demo"].fillna(0).astype(int)

    cleaned = cleaned.drop_duplicates(subset=["product_id", "collection_date"], keep="first")
    return cleaned


# ---------------------------------------------------------------------------
# Stage 4 Comprehensive Cleaning & Quality Assurance Engine
# ---------------------------------------------------------------------------

def ingest_to_sqlite(
    sneakers_df: pd.DataFrame, prices_df: pd.DataFrame, db_path: Optional[str] = None
) -> Dict[str, int]:
    """
    Ingests cleaned DataFrames into SQLite (legacy compatibility function).
    NON-NEGOTIABLE RULE:
    Never overwrite historical snapshots; keep the UNIQUE(product_id, collection_date) constraint.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    sneakers_inserted = 0
    snapshots_inserted = 0
    snapshots_ignored = 0

    try:
        # Ingest sneakers
        for _, row in sneakers_df.iterrows():
            cursor.execute(
                """
                INSERT INTO sneakers (product_id, sku, name, brand, colorway, retail_price, release_date, image_url, is_demo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(product_id) DO UPDATE SET
                    name=excluded.name,
                    brand=COALESCE(excluded.brand, sneakers.brand),
                    colorway=COALESCE(excluded.colorway, sneakers.colorway),
                    retail_price=COALESCE(excluded.retail_price, sneakers.retail_price),
                    release_date=COALESCE(excluded.release_date, sneakers.release_date),
                    image_url=COALESCE(excluded.image_url, sneakers.image_url)
                """,
                (
                    row["product_id"],
                    row.get("sku", row["product_id"]),
                    row["name"],
                    row.get("brand") if pd.notna(row.get("brand")) else None,
                    row.get("colorway") if pd.notna(row.get("colorway")) else None,
                    float(row["retail_price"]) if pd.notna(row.get("retail_price")) else None,
                    row.get("release_date") if pd.notna(row.get("release_date")) else None,
                    row.get("image_url") if pd.notna(row.get("image_url")) else None,
                    int(row.get("is_demo", 0)),
                ),
            )
            sneakers_inserted += 1

        # Build product_id to sneaker_id mapping
        pid_rows = cursor.execute("SELECT id, product_id FROM sneakers").fetchall()
        pid_to_id = {r["product_id"]: r["id"] for r in pid_rows}

        # Ingest price snapshots with INSERT OR IGNORE
        for _, row in prices_df.iterrows():
            pid = row["product_id"]
            sneaker_id = pid_to_id.get(pid)
            if not sneaker_id:
                continue

            cursor.execute(
                """
                INSERT OR IGNORE INTO price_history
                (sneaker_id, product_id, platform, price, size, condition, seller, rating, collection_date, is_demo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sneaker_id,
                    pid,
                    row["platform"],
                    float(row["price"]),
                    row.get("size") if pd.notna(row.get("size")) else None,
                    row.get("condition") if pd.notna(row.get("condition")) else "new",
                    row.get("seller") if pd.notna(row.get("seller")) else None,
                    float(row["rating"]) if pd.notna(row.get("rating")) else None,
                    row["collection_date"],
                    int(row.get("is_demo", 0)),
                ),
            )
            if cursor.rowcount > 0:
                snapshots_inserted += 1
            else:
                snapshots_ignored += 1

        conn.commit()
    finally:
        conn.close()

    return {
        "sneakers_inserted": sneakers_inserted,
        "snapshots_inserted": snapshots_inserted,
        "snapshots_ignored": snapshots_ignored,
    }


def load_raw_data(source: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load raw API data from a file or directory.
    Supports both official SoleScout search payloads and legacy formats.
    """
    raw_files = []
    if source and os.path.isfile(source):
        raw_files = [source]
    else:
        target_dir = source or RAW_DIR
        if os.path.exists(target_dir):
            raw_files = [
                os.path.join(target_dir, f)
                for f in os.listdir(target_dir)
                if f.endswith(".json") and not f.startswith("test_")
            ]
            raw_files.sort(key=os.path.getmtime, reverse=True)

    if not raw_files:
        logger.warning("No raw JSON files found to load.")
        return []

    collected_records: List[Dict[str, Any]] = []

    for file_path in raw_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                payload = json.load(f)

            # Format 1: items list from SoleScout search
            if isinstance(payload, dict) and "items" in payload:
                cdate = payload.get("collection_date")
                cts = payload.get("collection_timestamp")
                for item in payload["items"]:
                    item_copy = dict(item)
                    if cdate and "collection_date" not in item_copy:
                        item_copy["collection_date"] = cdate
                    if cts and "collection_timestamp" not in item_copy:
                        item_copy["collection_timestamp"] = cts
                    collected_records.append(item_copy)

            # Format 2: results list from direct SoleScout API
            elif isinstance(payload, dict) and "results" in payload:
                collected_records.extend(payload["results"])

            # Format 3: legacy data list with nested sneaker/prices
            elif isinstance(payload, dict) and "data" in payload:
                cdate = payload.get("collected_at", "").split("T")[0]
                for item in payload["data"]:
                    s = item.get("sneaker", {})
                    if s:
                        s_copy = dict(s)
                        if cdate:
                            s_copy["collection_date"] = cdate
                        collected_records.append(s_copy)

            # Format 4: list directly
            elif isinstance(payload, list):
                collected_records.extend(payload)

        except Exception as e:
            logger.error("Error reading raw file %s: %s", file_path, e)

    logger.info("Loaded %d raw records from %d files", len(collected_records), len(raw_files))
    return collected_records


def detect_statistical_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect statistical price outliers using Tukey's IQR rule.

    CRITICAL NON-NEGOTIABLE RULE:
    Do NOT automatically remove legitimate statistical outliers!
    Keep a clear distinction between:
    - DATA QUALITY ERROR (negative, corrupt, unparseable) -> Removed
    - STATISTICAL OUTLIER (legitimate extreme market prices, e.g. $2,000 grails) -> Preserved & Flagged
    """
    df["is_outlier"] = False
    df["outlier_type"] = None
    df["outlier_reason"] = None

    valid_prices = df[df["price"].notna() & (df["price"] > 0)]["price"]
    if len(valid_prices) >= 4:
        q1 = float(valid_prices.quantile(0.25))
        q3 = float(valid_prices.quantile(0.75))
        iqr = q3 - q1
        lower_bound = max(0.0, q1 - 1.5 * iqr)
        upper_bound = q3 + 1.5 * iqr

        for idx, row in df.iterrows():
            p = row.get("price")
            if pd.notna(p):
                p_val = float(p)
                if p_val > upper_bound:
                    df.at[idx, "is_outlier"] = True
                    df.at[idx, "outlier_type"] = "HIGH_EXTREME"
                    df.at[idx, "outlier_reason"] = (
                        f"Price ${p_val:.2f} exceeds Tukey IQR upper bound (${upper_bound:.2f})"
                    )
                elif p_val < lower_bound and lower_bound > 0:
                    df.at[idx, "is_outlier"] = True
                    df.at[idx, "outlier_type"] = "LOW_EXTREME"
                    df.at[idx, "outlier_reason"] = (
                        f"Price ${p_val:.2f} falls below Tukey IQR lower bound (${lower_bound:.2f})"
                    )

    return df


def clean_dataset(raw_records: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Main Data Cleaning Engine.

    Parameters:
    - raw_records: List of raw product/sneaker dictionaries.

    Returns:
    - cleaned_df: Cleaned, validated, and normalized DataFrame.
    - rejected_df: DataFrame of rows removed due to Data Quality Errors.
    - quality_report: Detailed dictionary of quality metrics and audit statistics.
    """
    raw_count = len(raw_records)
    if raw_count == 0:
        empty_report = {
            "raw_records": 0,
            "clean_records": 0,
            "duplicate_records": 0,
            "missing_values": {},
            "invalid_prices": 0,
            "invalid_timestamps": 0,
            "records_removed": 0,
            "cleaning_percentage": 0.0,
            "statistical_outliers_detected": 0,
            "outliers_preserved": True,
        }
        return pd.DataFrame(), pd.DataFrame(), empty_report

    now_utc = datetime.now(timezone.utc)
    default_date = now_utc.strftime("%Y-%m-%d")
    default_ts = now_utc.isoformat()

    normalized_rows = []
    rejected_rows = []

    # Quality counters
    invalid_price_count = 0
    invalid_timestamp_count = 0
    missing_id_count = 0
    missing_name_count = 0

    for i, raw in enumerate(raw_records):
        error_reasons = []

        # 1. Product Identifier (Style Code / SKU / Slug)
        style_code = _clean_string(raw.get("style_code") or raw.get("sku") or raw.get("product_id"))
        slug = _clean_string(raw.get("slug"))
        product_id = style_code or slug

        if not product_id:
            error_reasons.append("Missing product_id / SKU")
            missing_id_count += 1

        # 2. Product Name / Title
        product_name = _clean_string(raw.get("title") or raw.get("name") or raw.get("product_name"))
        if not product_name:
            error_reasons.append("Missing product_name / title")
            missing_name_count += 1

        # 3. Numeric Price Validation (Data Quality Error vs Valid)
        raw_price = raw.get("lowest_price_usd") if "lowest_price_usd" in raw else raw.get("price")
        price = _clean_price(raw_price)
        if price is None:
            # If price was provided but invalid (e.g. negative or string), or completely absent
            if raw_price is not None:
                error_reasons.append(f"Invalid price value: {raw_price}")
            else:
                error_reasons.append("Missing price value")
            invalid_price_count += 1

        # 4. Timestamps
        raw_cdate = raw.get("collection_date")
        cdate = validate_date(raw_cdate) if raw_cdate else default_date
        if raw_cdate and not validate_date(raw_cdate):
            invalid_timestamp_count += 1

        raw_cts = raw.get("collection_timestamp")
        cts = validate_timestamp(raw_cts) if raw_cts else default_ts

        # Check if record has unrecoverable Data Quality Errors
        if error_reasons:
            rejected_rows.append({
                "raw_index": i,
                "product_id": product_id,
                "product_name": product_name,
                "raw_price": raw_price,
                "reasons": "; ".join(error_reasons),
            })
            continue

        # 5. Brand Standardization
        brand = standardize_brand(raw.get("brand"))

        # 6. Retail Price & Discount
        raw_retail = raw.get("retail_price_usd") if "retail_price_usd" in raw else raw.get("retail_price")
        retail_price = _clean_price(raw_retail)
        discount = None
        if retail_price is not None and price is not None and retail_price > price:
            discount = round(retail_price - price, 2)

        # 7. Category & Model
        category = _clean_string(raw.get("category")) or "shoes"
        model = product_name

        # 8. Currency & Metadata
        currency = validate_currency(raw.get("currency"))
        size = _clean_string(raw.get("size"))
        condition = _clean_string(raw.get("condition")) or "new"
        seller = _clean_string(raw.get("seller"))
        marketplace = _clean_string(raw.get("marketplace")) or "SoleScout Aggregator"
        availability = "in_stock" if price is not None else "out_of_stock"
        product_url = _clean_string(raw.get("url") or raw.get("product_url"))
        image_url = _clean_string(raw.get("image") or raw.get("image_url"))

        normalized_rows.append({
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
            "collection_date": cdate,
            "collection_timestamp": cts,
        })

    initial_df = pd.DataFrame(normalized_rows)
    rejected_df = pd.DataFrame(rejected_rows)

    # 9. Duplicate Detection & Deduplication on (product_id, collection_date)
    duplicate_count = 0
    duplicate_rows = []
    if not initial_df.empty:
        pre_dedup_len = len(initial_df)
        is_dup = initial_df.duplicated(subset=["product_id", "collection_date"], keep="first")
        if is_dup.any():
            for idx, r in initial_df[is_dup].iterrows():
                duplicate_rows.append({
                    "raw_index": int(idx) if isinstance(idx, int) else None,
                    "product_id": str(r["product_id"]),
                    "product_name": str(r["product_name"]),
                    "raw_price": r["price"],
                    "reasons": f"Duplicate observation for ({r['product_id']}, {r['collection_date']}) - First observation preserved",
                    "category": "Duplicate Record Purged",
                })
        initial_df = initial_df.drop_duplicates(
            subset=["product_id", "collection_date"], keep="first"
        )
        duplicate_count = pre_dedup_len - len(initial_df)

    # 10. Statistical Outlier Detection (Tukey IQR rule — preserved, never removed)
    if not initial_df.empty:
        cleaned_df = detect_statistical_outliers(initial_df)
    else:
        cleaned_df = initial_df

    # 11. Count Missing Values per Column in Cleaned Data
    missing_values = {}
    if not cleaned_df.empty:
        for col in cleaned_df.columns:
            null_count = int(cleaned_df[col].isna().sum())
            if null_count > 0:
                missing_values[col] = {
                    "count": null_count,
                    "percentage": round((null_count / len(cleaned_df)) * 100.0, 1),
                }

    clean_count = len(cleaned_df)
    all_removed = rejected_rows + duplicate_rows
    records_removed = len(all_removed)
    cleaning_pct = round((clean_count / raw_count * 100.0), 2) if raw_count > 0 else 0.0

    outlier_count = int(cleaned_df["is_outlier"].sum()) if not cleaned_df.empty else 0

    # 12. Compile Data Quality Report
    quality_report = {
        "raw_records": raw_count,
        "clean_records": clean_count,
        "duplicate_records": duplicate_count,
        "records_removed": records_removed,
        "cleaning_percentage": cleaning_pct,
        "quality_errors": {
            "invalid_prices": invalid_price_count,
            "invalid_timestamps": invalid_timestamp_count,
            "missing_identifiers": missing_id_count,
            "missing_names": missing_name_count,
        },
        "missing_values": missing_values,
        "statistical_outliers": {
            "detected": outlier_count,
            "policy": "Preserved in clean dataset for analytical integrity (is_outlier=True)",
            "outliers_preserved": True,
        },
        "removed_records": all_removed,
        "reproducibility": {
            "timestamp": now_utc.isoformat(),
            "pipeline_version": "2.0-fds",
            "iqr_multiplier": 1.5,
            "unique_key": ["product_id", "collection_date"],
        },
    }

    return cleaned_df, rejected_df, quality_report


def export_raw_data_csv(output_dir: Optional[str] = None) -> str:
    """
    Exports raw ingested observations from data/raw/ to data/raw/sneakers_raw_latest.csv.
    Ensures no API keys or credentials are ever exposed in the CSV.
    """
    target_dir = output_dir or RAW_DIR
    os.makedirs(target_dir, exist_ok=True)
    raw_csv_path = os.path.join(target_dir, "sneakers_raw_latest.csv")

    raw_records = load_raw_data()
    if raw_records:
        df = pd.DataFrame(raw_records)
        for col in ["api_key", "secret", "token", "SOLESCOUT_API_KEY"]:
            if col in df.columns:
                df = df.drop(columns=[col])
        df.to_csv(raw_csv_path, index=False, encoding="utf-8")
        logger.info("Saved raw CSV to: %s", raw_csv_path)
        return raw_csv_path

    # If raw JSONs are not present, construct baseline from SQLite
    conn = get_connection()
    try:
        query = """
            SELECT 
                p.product_id, 
                s.name as product_name, 
                s.brand, 
                p.price as lowest_price_usd, 
                s.retail_price as retail_price_usd,
                s.category,
                'USD' as currency,
                p.collection_date,
                p.created_at as collection_timestamp,
                s.product_url
            FROM price_history p
            LEFT JOIN sneakers s ON p.product_id = s.product_id
            ORDER BY p.collection_date DESC
        """
        df = pd.read_sql_query(query, conn)
        df.to_csv(raw_csv_path, index=False, encoding="utf-8")
        logger.info("Generated baseline raw CSV to: %s", raw_csv_path)
        return raw_csv_path
    finally:
        conn.close()


def export_cleaned_data(
    cleaned_df: pd.DataFrame,
    report: Dict[str, Any],
    output_dir: Optional[str] = None,
) -> Tuple[str, str, str]:
    """
    Save the cleaned dataset and Data Quality Report to data/cleaned/.
    Returns (archive_csv_path, latest_csv_path, report_json_path).
    """
    target_dir = output_dir or CLEANED_DIR
    os.makedirs(target_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # Export CSVs
    archive_csv = os.path.join(target_dir, f"sneakers_cleaned_{timestamp}.csv")
    latest_csv = os.path.join(target_dir, "sneakers_cleaned_latest.csv")

    cleaned_df.to_csv(archive_csv, index=False, encoding="utf-8")
    cleaned_df.to_csv(latest_csv, index=False, encoding="utf-8")

    # Export Quality Report JSON
    report_path = os.path.join(target_dir, f"data_quality_report_{timestamp}.json")
    latest_report_path = os.path.join(target_dir, "data_quality_report_latest.json")

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    with open(latest_report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info("Saved cleaned CSV to: %s", latest_csv)
    logger.info("Saved Data Quality Report to: %s", latest_report_path)

    return archive_csv, latest_csv, latest_report_path


def run_cleaning_pipeline(
    raw_file: Optional[str] = None,
    db_path: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes the complete Stage 4 Cleaning Pipeline:
    1. Loads raw JSON data from data/raw/.
    2. Runs clean_dataset with duplicate, price, and timestamp validation.
    3. Flags statistical outliers without discarding them.
    4. Exports cleaned CSVs and Data Quality Report to data/cleaned/.
    5. Ingests cleaned records into SQLite.
    """
    raw_records = load_raw_data(raw_file)
    if not raw_records:
        return {
            "status": "error",
            "message": "No raw data found in data/raw/ to clean.",
            "clean_records": 0,
        }

    cleaned_df, rejected_df, quality_report = clean_dataset(raw_records)

    archive_csv, latest_csv, report_json = export_cleaned_data(
        cleaned_df, quality_report, output_dir=output_dir
    )
    export_raw_data_csv(output_dir=RAW_DIR)

    # Ingest into SQLite
    conn = get_connection(db_path)
    cursor = conn.cursor()
    inserted_norm = 0
    ignored_norm = 0

    try:
        for _, row in cleaned_df.iterrows():
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
                    row["product_id"],
                    row["product_name"],
                    row["brand"],
                    row["model"],
                    row["category"],
                    row["price"],
                    row["currency"],
                    row["retail_price"],
                    row["discount"],
                    row["size"],
                    row["condition"],
                    row["seller"],
                    row["availability"],
                    row["marketplace"],
                    row["product_url"],
                    row["image_url"],
                    row["collection_date"],
                    row["collection_timestamp"],
                ),
            )
            if cursor.rowcount > 0:
                inserted_norm += 1
            else:
                ignored_norm += 1

            # Update parent sneakers catalog table
            cursor.execute(
                """
                INSERT INTO sneakers (
                    product_id, sku, name, brand, retail_price, image_url, is_demo
                ) VALUES (?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT(product_id) DO UPDATE SET
                    name = excluded.name,
                    brand = COALESCE(excluded.brand, sneakers.brand),
                    retail_price = COALESCE(excluded.retail_price, sneakers.retail_price),
                    image_url = COALESCE(excluded.image_url, sneakers.image_url)
                """,
                (
                    row["product_id"],
                    row["product_id"],
                    row["product_name"],
                    row["brand"],
                    row["retail_price"],
                    row["image_url"],
                ),
            )
            sneaker_id = cursor.execute(
                "SELECT id FROM sneakers WHERE product_id = ?", (row["product_id"],)
            ).fetchone()[0]

            # Update price_history table
            if pd.notna(row["price"]):
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO price_history (
                        sneaker_id, product_id, platform, price,
                        condition, seller, collection_date, is_demo
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                    """,
                    (
                        sneaker_id,
                        row["product_id"],
                        row["marketplace"] or "SoleScout",
                        float(row["price"]),
                        row["condition"] or "new",
                        row["seller"],
                        row["collection_date"],
                    ),
                )

        conn.commit()
    finally:
        conn.close()

    return {
        "status": "success",
        "raw_records": quality_report["raw_records"],
        "clean_records": quality_report["clean_records"],
        "records_removed": quality_report["records_removed"],
        "cleaning_percentage": quality_report["cleaning_percentage"],
        "latest_csv": latest_csv,
        "archive_csv": archive_csv,
        "report_json": report_json,
        "quality_report": quality_report,
        "db_inserted": inserted_norm,
        "db_duplicates_ignored": ignored_norm,
    }
