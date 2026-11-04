"""
Unit tests for SoleScout Database Schema & Integrity Constraints (Phase 1)
"""

import os
import unittest
import sqlite3
import tempfile
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import init_db, get_connection


class TestDatabaseIntegrity(unittest.TestCase):
    def setUp(self):
        """Create a temporary database file for each test."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db_path = self.temp_db.name
        self.temp_db.close()
        init_db(self.temp_db_path)

    def tearDown(self):
        """Clean up temporary database file."""
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except PermissionError:
                pass

    def test_schema_creation(self):
        """Verify tables and unique constraints exist in the initialized schema."""
        conn = get_connection(self.temp_db_path)
        tables = [
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        ]
        self.assertIn("sneakers", tables)
        self.assertIn("price_history", tables)
        conn.close()

    def test_unique_snapshot_constraint(self):
        """
        NON-NEGOTIABLE RULE:
        Never overwrite historical snapshots; keep the UNIQUE(product_id, collection_date) constraint.
        """
        conn = get_connection(self.temp_db_path)
        cursor = conn.cursor()

        # Insert a parent sneaker
        cursor.execute(
            """
            INSERT INTO sneakers (product_id, sku, name, brand, retail_price)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("DZ5485-612", "DZ5485-612", "Air Jordan 1 Lost & Found", "Jordan", 180.0),
        )
        sneaker_id = cursor.lastrowid

        # Insert snapshot 1 for product_id on 2026-03-01
        cursor.execute(
            """
            INSERT INTO price_history (sneaker_id, product_id, platform, price, collection_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sneaker_id, "DZ5485-612", "StockX", 320.0, "2026-03-01"),
        )
        conn.commit()

        # Attempt to insert a second snapshot with the exact same (product_id, collection_date)
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute(
                """
                INSERT INTO price_history (sneaker_id, product_id, platform, price, collection_date)
                VALUES (?, ?, ?, ?, ?)
                """,
                (sneaker_id, "DZ5485-612", "StockX", 350.0, "2026-03-01"),
            )
            conn.commit()

        # Verify historical snapshot was preserved and never overwritten
        row = cursor.execute(
            "SELECT price FROM price_history WHERE product_id = ? AND collection_date = ?",
            ("DZ5485-612", "2026-03-01"),
        ).fetchone()
        self.assertEqual(row["price"], 320.0)

        # Inserting a snapshot for a DIFFERENT collection_date succeeds
        cursor.execute(
            """
            INSERT INTO price_history (sneaker_id, product_id, platform, price, collection_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sneaker_id, "DZ5485-612", "StockX", 325.0, "2026-03-02"),
        )
        conn.commit()

        count = cursor.execute(
            "SELECT COUNT(*) FROM price_history WHERE product_id = ?", ("DZ5485-612",)
        ).fetchone()[0]
        self.assertEqual(count, 2)
        conn.close()

    def test_missing_fields_stored_as_null(self):
        """
        NON-NEGOTIABLE RULE:
        Missing fields are stored as NULL (None in Python).
        """
        conn = get_connection(self.temp_db_path)
        cursor = conn.cursor()

        # Insert with missing optional fields
        cursor.execute(
            """
            INSERT INTO sneakers (product_id, sku, name, brand, colorway, retail_price, release_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("CT8012-005", "CT8012-005", "Air Jordan 11 Cool Grey", None, None, None, None),
        )
        sneaker_id = cursor.lastrowid
        conn.commit()

        row = cursor.execute(
            "SELECT * FROM sneakers WHERE id = ?", (sneaker_id,)
        ).fetchone()

        self.assertIsNone(row["brand"])
        self.assertIsNone(row["colorway"])
        self.assertIsNone(row["retail_price"])
        self.assertIsNone(row["release_date"])

        # Price history with null optional fields
        cursor.execute(
            """
            INSERT INTO price_history (sneaker_id, product_id, platform, price, collection_date, size, seller, rating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (sneaker_id, "CT8012-005", "GOAT", 290.0, "2026-03-01", None, None, None),
        )
        conn.commit()

        price_row = cursor.execute(
            "SELECT * FROM price_history WHERE product_id = ?", ("CT8012-005",)
        ).fetchone()
        self.assertIsNone(price_row["size"])
        self.assertIsNone(price_row["seller"])
        self.assertIsNone(price_row["rating"])
        conn.close()


if __name__ == "__main__":
    unittest.main()
