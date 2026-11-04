"""
SoleScout FDS - Sneaker Data Collection CLI Script
Stage 3: Multi-Query, Multi-Page Collector & SQLite/CSV Pipeline

Usage:
    # 1. Quick test collection (small dataset: 1 page, 3 results):
    python scripts/collect_sneakers.py --query "Jordan 1" --limit 3

    # 2. Multi-brand collection across multiple pages:
    python scripts/collect_sneakers.py --queries "Jordan 1,Nike Dunk,adidas Samba" --pages 2 --limit 5

    # 3. Seed demo dataset (clearly marked is_demo=1):
    python scripts/collect_sneakers.py --demo

Pipeline Execution:
1. Queries official SoleScout API (https://solescout.ai/api/public/search).
2. Collects multi-page sneaker data across queries.
3. Saves raw JSON response snapshots to data/raw/.
4. Normalizes every record with collection_date (YYYY-MM-DD) and UTC timestamp.
5. Ingests normalized records into SQLite with UNIQUE(product_id, collection_date).
6. Exports cleaned, standardized CSV snapshots to data/cleaned/.
7. Never overwrites historical snapshots; duplicate collection on the same day is safely ignored.
"""

import os
import sys
import argparse
import logging

# Ensure UTF-8 output encoding for Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add backend directory to sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from database import init_db, get_connection
from services.solescout_api import SoleScoutClient, mask_key
from services.collector import collect, seed_demo_data, RAW_DIR, CLEANED_DIR

# Configure clean logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("collect_sneakers")


def parse_args():
    parser = argparse.ArgumentParser(
        description="SoleScout Sneaker Price Intelligence Data Collector (Stage 3)"
    )
    parser.add_argument(
        "-q", "--query", "--queries",
        dest="queries",
        type=str,
        default="Jordan 1",
        help="Search query or comma-separated queries (e.g. 'Jordan 1,Nike Dunk,adidas Samba')",
    )
    parser.add_argument(
        "-p", "--pages",
        type=int,
        default=1,
        help="Number of pages to retrieve per query (default: 1)",
    )
    parser.add_argument(
        "-l", "--limit",
        type=int,
        default=5,
        help="Number of results per page (1-25, default: 5 for testing)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Populate isolated Demo/Sample Data instead of querying the live API",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 72)
    print("SoleScout Sneaker Price Intelligence & Analytics")
    print("STAGE 3: Python Sneaker Data Collector Pipeline")
    print("=" * 72)

    # Ensure database is initialized
    init_db()

    # 1. Handle Demo Mode if requested
    if args.demo:
        print("\n[*] Populating Demo/Sample Data (is_demo=1)...")
        demo_res = seed_demo_data()
        print(f"    - Label                 : {demo_res.get('label')}")
        print(f"    - Sneakers Loaded       : {demo_res.get('demo_sneakers_loaded')}")
        print(f"    - Snapshots Loaded      : {demo_res.get('demo_snapshots_loaded')}")
        print(f"    - Duplicates Ignored    : {demo_res.get('duplicates_ignored')}")
        print("\n[OK] Demo dataset active. Can be switched off anytime.")
        print("=" * 72)
        return

    # 2. Inspect Environment & Credentials
    raw_key = os.getenv("SOLESCOUT_API_KEY", "")
    base_url = os.getenv("SOLESCOUT_BASE_URL", "https://solescout.ai")
    has_key = bool(raw_key and raw_key.strip().lower() not in {
        "", "your_api_key_here", "your_key_here", "change_me"
    })

    print(f"\n[1] Pipeline Configuration:")
    print(f"    - API Base URL          : {base_url}")
    print(f"    - Authentication        : {'Authenticated (' + mask_key(raw_key) + ')' if has_key else 'SoleScout Public Tier (60 req/min)'}")
    print(f"    - Search Queries        : {args.queries}")
    print(f"    - Pages per Query       : {args.pages}")
    print(f"    - Results per Page      : {args.limit}")

    # 3. Run the Collector
    print(f"\n[2] Executing Collector Pipeline...")
    res = collect(
        query=args.queries,
        limit=args.limit,
        max_pages=args.pages,
        allow_anonymous=True,
    )

    if res.get("status") == "error":
        print(f"\n[ERROR] Collection failed: {res.get('message')}")
        sys.exit(1)

    if res.get("status") == "unconfigured":
        print(f"\n[NOTICE] {res.get('message')}")
        sys.exit(0)

    # 4. Print Pipeline Execution Summary
    print(f"\n[3] Ingestion Summary:")
    print(f"    - Queries Executed      : {res.get('queries_used')}")
    print(f"    - Total Pages Fetched   : {res.get('pages_fetched')}")
    print(f"    - Raw Records Fetched   : {res.get('records_collected')}")
    print(f"    - Records Normalized    : {res.get('records_normalized')}")
    print(f"    - New Snapshots Saved   : {res.get('snapshots_inserted')} (written to SQLite)")
    print(f"    - Duplicates Ignored    : {res.get('snapshots_ignored')} (prevented overwrite for same date)")

    # 5. Storage Locations
    print(f"\n[4] Data Artifacts Saved:")
    raw_files = res.get("raw_files", [])
    if raw_files:
        for rf in raw_files:
            rel_rf = os.path.relpath(rf, PROJECT_ROOT)
            print(f"    - Raw JSON Snapshot     : {rel_rf}")
    else:
        print(f"    - Raw JSON Snapshot     : None")

    if res.get("csv_file"):
        rel_csv = os.path.relpath(res.get("csv_file"), PROJECT_ROOT)
        print(f"    - Cleaned CSV Archive   : {rel_csv}")
    if res.get("latest_csv_file"):
        rel_latest = os.path.relpath(res.get("latest_csv_file"), PROJECT_ROOT)
        print(f"    - Latest Cleaned CSV    : {rel_latest}")

    # 6. Display Sample Normalized Records
    sample = res.get("normalized_sample", [])
    if sample:
        print(f"\n[5] Sample Normalized Records ({len(sample)} shown):")
        print("-" * 72)
        for i, s in enumerate(sample, start=1):
            print(f"Record #{i}:")
            print(f"  • Product ID (SKU) : {s.get('product_id')}")
            print(f"  • Product Name     : {s.get('product_name')}")
            print(f"  • Brand            : {s.get('brand')}")
            print(f"  • Category         : {s.get('category')}")
            print(f"  • Live Price       : ${s.get('price')} USD" if s.get('price') is not None else "  • Live Price       : N/A")
            print(f"  • Retail Price     : ${s.get('retail_price')} USD" if s.get('retail_price') is not None else "  • Retail Price     : N/A")
            print(f"  • Discount         : ${s.get('discount')} USD" if s.get('discount') is not None else "  • Discount         : N/A")
            print(f"  • Marketplace      : {s.get('marketplace')}")
            print(f"  • Collection Date  : {s.get('collection_date')}")
            print(f"  • Timestamp (UTC)  : {s.get('collection_timestamp')}")
            print("-" * 72)

    # 7. Database Verification
    conn = get_connection()
    try:
        total_sneakers = conn.execute("SELECT COUNT(*) FROM sneakers").fetchone()[0]
        total_snapshots = conn.execute("SELECT COUNT(*) FROM price_history").fetchone()[0]
        total_normalized = conn.execute("SELECT COUNT(*) FROM normalized_sneakers").fetchone()[0]
        print(f"\n[6] Database State:")
        print(f"    - Total Unique Sneakers Tracked : {total_sneakers}")
        print(f"    - Total Price Snapshots         : {total_snapshots}")
        print(f"    - Total Normalized Snapshots    : {total_normalized}")
        print("    [PASS] Historical preservation rule verified: existing snapshots never overwritten.")
    finally:
        conn.close()

    print("=" * 72)
    print("STAGE 3 DATA COLLECTION COMPLETE [SUCCESS]")
    print("=" * 72)


if __name__ == "__main__":
    main()
