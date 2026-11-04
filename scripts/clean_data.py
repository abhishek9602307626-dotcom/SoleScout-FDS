"""
SoleScout FDS - Data Cleaning & Quality Assurance CLI Script
Stage 4: Automated Cleaning, Validation, and Quality Reporting

Usage:
    # 1. Clean the latest raw dataset in data/raw/:
    python scripts/clean_data.py

    # 2. Clean a specific raw JSON file:
    python scripts/clean_data.py --raw-file data/raw/raw_solescout_query_Jordan_1_20261103_135515.json

    # 3. Specify custom output directory:
    python scripts/clean_data.py --output-dir data/cleaned

Cleaning Pipeline Steps:
1. Load raw API JSON snapshots from data/raw/.
2. Detect and remove duplicate records while preserving first observations.
3. Quantify missing values across all columns.
4. Clean, parse, and convert numeric price fields.
5. Filter out DATA QUALITY ERRORS (negative prices, missing IDs, corrupt formats).
6. Standardize brand names against canonical footwear taxonomies.
7. Validate timestamps (ISO8601 UTC and YYYY-MM-DD).
8. Validate currencies (ISO 4217 standard).
9. Detect STATISTICAL OUTLIERS (IQR Tukey & Z-Score) WITHOUT discarding legitimate high-value grails.
10. Strictly preserve NULLs; never silently impute or invent missing values.
11. Save cleaned dataset and Data Quality Report to data/cleaned/.
"""

import os
import sys
import argparse
import json
import pandas as pd

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

from services.cleaning import (
    load_raw_data,
    clean_dataset,
    export_cleaned_data,
    run_cleaning_pipeline,
    RAW_DIR,
    CLEANED_DIR,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="SoleScout Sneaker Data Cleaning & Quality Assurance Pipeline (Stage 4)"
    )
    parser.add_argument(
        "--raw-file",
        type=str,
        default=None,
        help="Path to a specific raw JSON file (default: cleans all files in data/raw/)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Custom output directory for cleaned datasets and reports (default: data/cleaned/)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 76)
    print("SoleScout Sneaker Price Intelligence & Analytics")
    print("STAGE 4: Data Cleaning & Quality Assurance Pipeline")
    print("=" * 76)

    # 1. Load Raw Data
    source_desc = args.raw_file if args.raw_file else f"All JSON files in {os.path.relpath(RAW_DIR, PROJECT_ROOT)}"
    print(f"\n[1] Loading Raw Data:")
    print(f"    - Source                : {source_desc}")

    raw_records = load_raw_data(args.raw_file)
    if not raw_records:
        print("\n[!] No raw data found in data/raw/ to clean.")
        print("    Run the data collector first: python scripts/collect_sneakers.py")
        sys.exit(0)

    print(f"    - Total Raw Records     : {len(raw_records)}")

    # 2. Execute Cleaning Engine
    print(f"\n[2] Executing Cleaning Pipeline...")
    cleaned_df, rejected_df, report = clean_dataset(raw_records)

    # 3. Export Cleaned Dataset & Reports
    out_dir = args.output_dir or CLEANED_DIR
    archive_csv, latest_csv, report_json = export_cleaned_data(
        cleaned_df, report, output_dir=out_dir
    )

    # 4. Display Data Quality Report
    print("\n" + "=" * 76)
    print("[AUDIT] DATA QUALITY REPORT")
    print("=" * 76)

    print(f"\n[A] Pipeline Throughput & Efficiency:")
    print(f"    - Raw Records Processed : {report['raw_records']}")
    print(f"    - Clean Records Output  : {report['clean_records']}")
    print(f"    - Duplicate Records     : {report['duplicate_records']} (deduplicated on [product_id, date])")
    print(f"    - Records Removed       : {report['records_removed']}")
    print(f"    - Cleaning Percentage   : {report['cleaning_percentage']}% retained")

    print(f"\n[B] Data Quality Errors (Corrupted / Incomplete Records Removed):")
    errs = report.get("quality_errors", {})
    print(f"    - Invalid Prices (<=0 or non-numeric) : {errs.get('invalid_prices', 0)}")
    print(f"    - Invalid Timestamps                  : {errs.get('invalid_timestamps', 0)}")
    print(f"    - Missing Product Identifiers         : {errs.get('missing_identifiers', 0)}")
    print(f"    - Missing Product Names               : {errs.get('missing_names', 0)}")

    print(f"\n[C] Missing Values Audit (NULLs Preserved - Never Imputed):")
    missing_map = report.get("missing_values", {})
    if missing_map:
        for col, info in missing_map.items():
            print(f"    - {col:<22} : {info['count']} missing ({info['percentage']}%)")
    else:
        print("    - No missing values in retained fields.")

    print(f"\n[D] Statistical Outliers vs. Data Quality Errors:")
    outliers_info = report.get("statistical_outliers", {})
    print(f"    - Statistical Outliers Detected       : {outliers_info.get('detected', 0)}")
    print(f"    - Outliers Removal Policy             : NEVER REMOVED (flagged with is_outlier=True)")
    print(f"    - Outliers Preserved for Analytics    : {outliers_info.get('outliers_preserved', True)}")
    print(f"    [NOTE] Quality errors (bad data) were removed; legitimate market grails were preserved.")

    # 5. Display Cleaned Records Sample
    print(f"\n[E] Sample Cleaned Records ({min(3, len(cleaned_df))} shown):")
    print("-" * 76)
    if not cleaned_df.empty:
        for i, (_, row) in enumerate(cleaned_df.head(3).iterrows(), start=1):
            outlier_status = f"YES ({row.get('outlier_reason')})" if row.get("is_outlier") else "No"
            print(f"Record #{i}:")
            print(f"  - Product ID (SKU) : {row.get('product_id')}")
            print(f"  - Product Name     : {row.get('product_name')}")
            print(f"  - Canonical Brand  : {row.get('brand')}")
            print(f"  - Clean Price      : ${row.get('price')} {row.get('currency')}")
            print(f"  - Retail Price     : ${row.get('retail_price')}" if pd.notna(row.get('retail_price')) else "  - Retail Price     : N/A")
            print(f"  - Discount         : ${row.get('discount')}" if pd.notna(row.get('discount')) else "  - Discount         : N/A")
            print(f"  - Statistical Outlier: {outlier_status}")
            print(f"  - Collection Date  : {row.get('collection_date')}")
            print("-" * 76)

    # 6. Artifact Summary
    rel_csv = os.path.relpath(latest_csv, PROJECT_ROOT)
    rel_report = os.path.relpath(report_json, PROJECT_ROOT)
    print(f"\n[F] Output Artifacts Saved:")
    print(f"    - Cleaned CSV Dataset   : {rel_csv}")
    print(f"    - Quality Report (JSON) : {rel_report}")
    print("=" * 76)
    print("STAGE 4 DATA CLEANING PIPELINE COMPLETE [SUCCESS]")
    print("=" * 76)


if __name__ == "__main__":
    main()
