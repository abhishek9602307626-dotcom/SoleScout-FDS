"""
Unit tests for SoleScout API Client & Data Collector (Phase 2)
"""

import os
import sys
import json
import unittest
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import init_db, get_connection
from services.solescout_api import SoleScoutClient, SoleScoutAPIError
from services.collector import save_raw, collect, seed_demo_data, clear_demo_data


class TestCollectorAndAPI(unittest.TestCase):
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

    def test_api_client_unconfigured_behavior(self):
        """Verify client correctly reports unconfigured status and blocks requests without leaking."""
        client = SoleScoutClient(api_key="your_api_key_here")
        self.assertFalse(client.is_configured())

        with self.assertRaises(SoleScoutAPIError) as ctx:
            client._get("sneakers")
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertNotIn("your_api_key_here", str(ctx.exception))

    def test_collect_unconfigured_returns_required_message(self):
        """
        NON-NEGOTIABLE RULE:
        If there is no data, show:
        'No SoleScout data has been collected yet. Configure the API and run the collector.'
        """
        result = collect(query="Jordan 1")
        # Since .env has placeholder key:
        self.assertEqual(result["status"], "unconfigured")
        self.assertEqual(
            result["message"],
            "No SoleScout data has been collected yet. Configure the API and run the collector.",
        )
        self.assertEqual(result["records_collected"], 0)

    def test_save_raw_json(self):
        """Verify raw snapshots are saved to data/raw with valid JSON."""
        test_data = {"test_sku": "DZ5485-612", "price": 350.0}
        filepath = save_raw(test_data, label="test_unit")
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        self.assertEqual(loaded["test_sku"], "DZ5485-612")
        # Clean up test file
        try:
            os.remove(filepath)
        except Exception:
            pass

    def test_demo_dataset_flagged_and_switchable(self):
        """
        NON-NEGOTIABLE RULE:
        Any sample data must be clearly labeled 'Demo/Sample Data' and must be switchable off.
        """
        res = seed_demo_data(self.temp_db_path)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["label"], "Demo/Sample Data")
        self.assertGreater(res["demo_sneakers_loaded"], 0)
        self.assertGreater(res["demo_snapshots_loaded"], 0)

        conn = get_connection(self.temp_db_path)
        # Verify all seeded records have is_demo = 1
        sneaker_demos = conn.execute("SELECT COUNT(*) FROM sneakers WHERE is_demo = 1").fetchone()[0]
        self.assertEqual(sneaker_demos, res["demo_sneakers_loaded"])

        real_count = conn.execute("SELECT COUNT(*) FROM sneakers WHERE is_demo = 0").fetchone()[0]
        self.assertEqual(real_count, 0)

        # Verify idempotence & snapshot integrity: running seed again does not duplicate or overwrite snapshots
        res_repeat = seed_demo_data(self.temp_db_path)
        self.assertGreater(res_repeat["duplicates_ignored"], 0)
        self.assertEqual(res_repeat["demo_snapshots_loaded"], 0)

        # Test switch off (clearing demo data leaves 0 records)
        deleted = clear_demo_data(self.temp_db_path)
        self.assertEqual(deleted, sneaker_demos)

        after_clean = conn.execute("SELECT COUNT(*) FROM sneakers").fetchone()[0]
        self.assertEqual(after_clean, 0)
        conn.close()


if __name__ == "__main__":
    unittest.main()
