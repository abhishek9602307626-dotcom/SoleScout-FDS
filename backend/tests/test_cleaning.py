"""
Unit tests for SoleScout Data Cleaning Pipeline (Phase 3)
"""

import os
import sys
import unittest
import tempfile
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import init_db, get_connection
from services.cleaning import (
    clean_sneakers_df,
    clean_prices_df,
    ingest_to_sqlite,
    _clean_price,
    _clean_string,
)


class TestCleaningPipeline(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db_path = self.temp_db.name
        self.temp_db.close()
        init_db(self.temp_db_path)

    def tearDown(self):
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except PermissionError:
                pass

    def test_clean_price_normalizer(self):
        """Verify currency strings and symbols are parsed cleanly to float, and invalid become None."""
        self.assertEqual(_clean_price("$180.00"), 180.0)
        self.assertEqual(_clean_price(" 220,500.50 "), 220500.5)
        self.assertEqual(_clean_price(195), 195.0)
        self.assertIsNone(_clean_price("invalid"))
        self.assertIsNone(_clean_price("-50"))
        self.assertIsNone(_clean_price(None))

    def test_clean_string_sentinels(self):
        """Verify sentinel strings (N/A, null, nan, empty) become None (SQL NULL)."""
        self.assertIsNone(_clean_string("  "))
        self.assertIsNone(_clean_string("N/A"))
        self.assertIsNone(_clean_string("null"))
        self.assertIsNone(_clean_string("None"))
        self.assertEqual(_clean_string("  Air Jordan 1  "), "Air Jordan 1")

    def test_clean_sneakers_df(self):
        """Test metadata cleaning, type conversion, and deduplication."""
        raw_df = pd.DataFrame([
            {
                "product_id": "DZ5485-612",
                "sku": "DZ5485-612",
                "name": "  Jordan 1 Lost & Found  ",
                "brand": "Jordan",
                "retail_price": "$180.00",
                "release_date": "November 19, 2022",
                "colorway": "null",
            },
            {
                # Duplicate product_id
                "product_id": "DZ5485-612",
                "sku": "DZ5485-612",
                "name": "Duplicate Entry",
                "brand": "Jordan",
                "retail_price": "190",
            },
            {
                # Missing name - should be dropped
                "product_id": "NO-NAME",
                "name": "  ",
            },
        ])

        cleaned = clean_sneakers_df(raw_df)
        self.assertEqual(len(cleaned), 1)
        row = cleaned.iloc[0]
        self.assertEqual(row["product_id"], "DZ5485-612")
        self.assertEqual(row["name"], "Jordan 1 Lost & Found")
        self.assertEqual(row["retail_price"], 180.0)
        self.assertEqual(row["release_date"], "2022-11-19")
        self.assertIsNone(row["colorway"])

    def test_clean_prices_and_deduplication(self):
        """
        NON-NEGOTIABLE RULE:
        Never overwrite historical snapshots; keep the UNIQUE(product_id, collection_date) constraint.
        """
        raw_prices = pd.DataFrame([
            {
                "product_id": "DZ5485-612",
                "platform": "stockx",
                "price": "$380.00",
                "collection_date": "2026-03-01",
                "size": " 10.5 ",
            },
            {
                # Duplicate snapshot on same collection date: should be dropped, preserving first
                "product_id": "DZ5485-612",
                "platform": "stockx",
                "price": "$400.00",
                "collection_date": "2026-03-01",
                "size": " 10.5 ",
            },
            {
                # Invalid price record
                "product_id": "DZ5485-612",
                "platform": "goat",
                "price": "N/A",
                "collection_date": "2026-03-02",
            },
        ])

        cleaned = clean_prices_df(raw_prices)
        self.assertEqual(len(cleaned), 1)
        row = cleaned.iloc[0]
        self.assertEqual(row["platform"], "StockX")
        self.assertEqual(row["price"], 380.0)
        self.assertEqual(row["collection_date"], "2026-03-01")

    def test_ingest_to_sqlite(self):
        """Verify cleaned data is inserted properly and duplicates are ignored without error."""
        sneakers_df = pd.DataFrame([{
            "product_id": "CT8012-005",
            "sku": "CT8012-005",
            "name": "Air Jordan 11 Cool Grey",
            "brand": "Jordan",
            "colorway": None,
            "retail_price": 225.0,
            "release_date": "2021-12-11",
            "image_url": None,
            "is_demo": 0,
        }])

        prices_df = pd.DataFrame([
            {
                "product_id": "CT8012-005",
                "platform": "StockX",
                "price": 310.0,
                "collection_date": "2026-03-01",
                "size": "10",
                "condition": "new",
                "seller": None,
                "rating": None,
                "is_demo": 0,
            },
            {
                "product_id": "CT8012-005",
                "platform": "GOAT",
                "price": 315.0,
                "collection_date": "2026-03-02",
                "size": "10",
                "condition": "new",
                "seller": None,
                "rating": None,
                "is_demo": 0,
            },
        ])

        res1 = ingest_to_sqlite(sneakers_df, prices_df, db_path=self.temp_db_path)
        self.assertEqual(res1["sneakers_inserted"], 1)
        self.assertEqual(res1["snapshots_inserted"], 2)
        self.assertEqual(res1["snapshots_ignored"], 0)

        # Ingest same prices again: must ignore duplicates and NOT overwrite
        res2 = ingest_to_sqlite(sneakers_df, prices_df, db_path=self.temp_db_path)
        self.assertEqual(res2["snapshots_inserted"], 0)
        self.assertEqual(res2["snapshots_ignored"], 2)

        conn = get_connection(self.temp_db_path)
        total_snapshots = conn.execute("SELECT COUNT(*) FROM price_history").fetchone()[0]
        self.assertEqual(total_snapshots, 2)
        conn.close()

    def test_stage4_clean_dataset_and_quality_report(self):
        """
        Stage 4 Requirement:
        - Detect duplicates.
        - Detect missing values.
        - Filter invalid prices (Quality Errors).
        - Preserve legitimate statistical outliers (Tukey IQR).
        - Standardize brand names.
        """
        from services.cleaning import clean_dataset, standardize_brand

        self.assertEqual(standardize_brand("air jordan"), "Air Jordan")
        self.assertEqual(standardize_brand("nike sportswear"), "Nike")
        self.assertEqual(standardize_brand("yeezy"), "adidas Yeezy")

        raw_sample = [
            # 1. Clean valid product
            {
                "product_id": "SKU-001",
                "title": "Air Jordan 1 High",
                "brand": "jordan",
                "price": 180.0,
                "retail_price": 180.0,
                "collection_date": "2026-11-03",
            },
            # 2. Duplicate snapshot for same product & date -> must be deduplicated
            {
                "product_id": "SKU-001",
                "title": "Air Jordan 1 High Duplicate",
                "brand": "jordan",
                "price": 190.0,
                "retail_price": 180.0,
                "collection_date": "2026-11-03",
            },
            # 3. Data Quality Error: Negative price -> must be REMOVED
            {
                "product_id": "SKU-BAD-PRICE",
                "title": "Corrupted Product",
                "brand": "nike",
                "price": -50.0,
                "collection_date": "2026-11-03",
            },
            # 4. Data Quality Error: Missing product title -> must be REMOVED
            {
                "product_id": "SKU-NO-NAME",
                "title": None,
                "brand": "nike",
                "price": 120.0,
                "collection_date": "2026-11-03",
            },
            # 5. Normal price 1
            {
                "product_id": "SKU-002",
                "title": "Nike Dunk Low",
                "brand": "nike",
                "price": 115.0,
                "retail_price": 115.0,
                "collection_date": "2026-11-03",
            },
            # 6. Normal price 2
            {
                "product_id": "SKU-003",
                "title": "adidas Samba",
                "brand": "adidas",
                "price": 100.0,
                "retail_price": 100.0,
                "collection_date": "2026-11-03",
            },
            # 7. Normal price 3
            {
                "product_id": "SKU-004",
                "title": "New Balance 550",
                "brand": "new balance",
                "price": 120.0,
                "retail_price": 110.0,
                "collection_date": "2026-11-03",
            },
            # 8. Statistical Outlier: Dior Air Jordan 1 ($3,500) -> MUST BE PRESERVED!
            {
                "product_id": "SKU-DIOR-001",
                "title": "Air Jordan 1 High Dior",
                "brand": "air jordan",
                "price": 3500.0,
                "retail_price": 2000.0,
                "collection_date": "2026-11-03",
            },
        ]

        cleaned_df, rejected_df, report = clean_dataset(raw_sample)

        # 8 raw records
        self.assertEqual(report["raw_records"], 8)
        # 2 rejected (negative price, missing title)
        self.assertEqual(len(rejected_df), 2)
        # 1 duplicate dropped
        self.assertEqual(report["duplicate_records"], 1)
        # 5 clean records remaining
        self.assertEqual(report["clean_records"], 5)

        # Statistical outlier check: Dior Jordan 1 MUST be retained
        dior_row = cleaned_df[cleaned_df["product_id"] == "SKU-DIOR-001"]
        self.assertEqual(len(dior_row), 1)
        self.assertTrue(bool(dior_row.iloc[0]["is_outlier"]))
        self.assertIn("IQR upper bound", dior_row.iloc[0]["outlier_reason"])
        self.assertTrue(report["statistical_outliers"]["outliers_preserved"])


if __name__ == "__main__":
    unittest.main()
