"""
Unit tests for SoleScout FastAPI Endpoints (Phase 5)
"""

import os
import sys
import unittest
import tempfile
from fastapi import HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database
from services.collector import seed_demo_data, clear_demo_data
from api.routes import (
    get_stats,
    list_sneakers,
    get_sneaker,
    get_sneaker_prices,
    get_sneaker_analytics,
    get_sneaker_outliers,
    trigger_collection,
    CollectRequest,
    NO_DATA_MESSAGE,
)


class TestApiRoutes(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db_path = self.temp_db.name
        self.temp_db.close()

        # Patch database.DB_PATH to use our isolated temp DB
        self.orig_db_path = database.DB_PATH
        database.DB_PATH = self.temp_db_path
        database.init_db(self.temp_db_path)

    def tearDown(self):
        database.DB_PATH = self.orig_db_path
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except PermissionError:
                pass

    def test_stats_empty_state_message(self):
        """
        NON-NEGOTIABLE RULE:
        If there is no data, show:
        'No SoleScout data has been collected yet. Configure the API and run the collector.'
        """
        stats = get_stats(include_demo=False)
        self.assertEqual(stats.total_sneakers, 0)
        self.assertEqual(stats.total_price_records, 0)
        self.assertTrue(stats.is_empty)
        self.assertEqual(stats.message, NO_DATA_MESSAGE)

    def test_stats_with_demo_data(self):
        """Verify stats properly distinguish demo data and respect switch."""
        seed_demo_data(self.temp_db_path)

        stats_demo = get_stats(include_demo=True)
        self.assertGreater(stats_demo.total_sneakers, 0)
        self.assertTrue(stats_demo.demo_mode_active)
        self.assertIn("Demo/Sample Data", stats_demo.message)

        # Switched off:
        stats_off = get_stats(include_demo=False)
        self.assertEqual(stats_off.total_sneakers, 0)
        self.assertEqual(stats_off.message, NO_DATA_MESSAGE)

    def test_list_and_search_sneakers(self):
        """Test search, filtering, and missing field handling."""
        seed_demo_data(self.temp_db_path)

        # Search for Chicago
        results = list_sneakers(search="Chicago", include_demo=True)
        self.assertGreaterEqual(len(results), 1)
        self.assertIn("Chicago", results[0].name)
        self.assertIsNotNone(results[0].latest_price)

        # Brand filter
        nike_results = list_sneakers(brand="Nike", include_demo=True)
        for s in nike_results:
            self.assertEqual(s.brand, "Nike")

        # Exclude demo returns empty when only demo data exists
        no_demos = list_sneakers(include_demo=False)
        self.assertEqual(len(no_demos), 0)

    def test_get_sneaker_and_prices(self):
        """Test single sneaker retrieval by product_id and price series."""
        seed_demo_data(self.temp_db_path)

        sneaker = get_sneaker("DZ5485-612")
        self.assertEqual(sneaker.product_id, "DZ5485-612")
        self.assertEqual(sneaker.retail_price, 180.0)

        prices = get_sneaker_prices("DZ5485-612", include_demo=True)
        self.assertGreater(len(prices), 0)
        self.assertEqual(prices[0].product_id, "DZ5485-612")

        # Non-existent sneaker throws 404
        with self.assertRaises(HTTPException) as ctx:
            get_sneaker("NON-EXISTENT-SKU")
        self.assertEqual(ctx.exception.status_code, 404)

    def test_analytics_and_outliers_endpoints(self):
        """Verify analytics endpoint computes statistical models and detects outliers."""
        seed_demo_data(self.temp_db_path)

        analytics = get_sneaker_analytics("DZ5485-612", include_demo=True)
        self.assertEqual(analytics.product_id, "DZ5485-612")
        self.assertIsNotNone(analytics.descriptive_stats.mean)
        self.assertIsNotNone(analytics.trend.direction)
        self.assertGreater(len(analytics.platform_comparison), 0)

        outliers = get_sneaker_outliers("DZ5485-612", z_threshold=2.0, include_demo=True)
        self.assertIsNotNone(outliers.total_records)

    def test_trigger_collector_unconfigured(self):
        """Verify collector endpoint responds cleanly when unconfigured."""
        resp = trigger_collection(CollectRequest(query="Jordan 4"))
        self.assertEqual(resp.status, "unconfigured")
        self.assertEqual(resp.message, NO_DATA_MESSAGE)


if __name__ == "__main__":
    unittest.main()
