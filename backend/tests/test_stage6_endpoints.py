"""
Unit Tests for Stage 6: FastAPI Backend Endpoints
Directly tests all 12 required endpoints and their Pydantic schemas:
1.  GET  /api/health                     -> get_health()
2.  GET  /api/products                   -> get_products()
3.  GET  /api/products/{product_id}      -> get_product()
4.  GET  /api/brands                     -> get_brands()
5.  GET  /api/dashboard                  -> get_dashboard()
6.  GET  /api/price-history/{product_id} -> get_price_history()
7.  GET  /api/analytics/brands           -> get_analytics_brands()
8.  GET  /api/analytics/price-trends     -> get_analytics_price_trends()
9.  GET  /api/statistics/anova           -> get_statistics_anova()
10. GET  /api/statistics/correlation     -> get_statistics_correlation()
11. GET  /api/data-quality               -> get_data_quality()
12. POST /api/collector/run              -> run_collector()
"""

import os
import sys
import unittest
import tempfile
from fastapi import HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database
from api.routes import (
    get_health,
    get_products,
    get_product,
    get_brands,
    get_dashboard,
    get_price_history,
    get_analytics_brands,
    get_analytics_price_trends,
    get_statistics_anova,
    get_statistics_correlation,
    get_data_quality,
    run_collector,
)
from schemas import (
    HealthResponse,
    PaginatedProductsResponse,
    SneakerResponse,
    BrandsListResponse,
    DashboardResponse,
    ProductPriceHistoryResponse,
    BrandAnalyticsResponse,
    PriceTrendsResponse,
    AnovaResponse,
    CorrelationResponse,
    DataQualityResponse,
    CollectorRunResponse,
    CollectorRunRequest,
)
from services.collector import seed_demo_data


class TestStage6Endpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.temp_db_path = cls.temp_db.name
        cls.temp_db.close()

        cls.orig_db_path = database.DB_PATH
        database.DB_PATH = cls.temp_db_path
        database.init_db(cls.temp_db_path)

        # Seed sample data for multi-brand and temporal validation
        seed_demo_data(cls.temp_db_path)

    @classmethod
    def tearDownClass(cls):
        database.DB_PATH = cls.orig_db_path
        if os.path.exists(cls.temp_db_path):
            try:
                os.remove(cls.temp_db_path)
            except PermissionError:
                pass

    # 1. GET /api/health
    def test_01_health_endpoint(self):
        res = get_health()
        self.assertIsInstance(res, HealthResponse)
        self.assertEqual(res.status, "healthy")
        self.assertEqual(res.database, "connected")
        self.assertEqual(res.version, "2.0.0")
        self.assertIsNotNone(res.timestamp)

    # 2. GET /api/products (Paginated)
    def test_02_products_pagination_and_filtering(self):
        # Pagination
        res = get_products(page=1, limit=2, include_demo=True)
        self.assertIsInstance(res, PaginatedProductsResponse)
        self.assertGreaterEqual(res.total, 5)
        self.assertEqual(res.page, 1)
        self.assertEqual(res.limit, 2)
        self.assertGreaterEqual(res.total_pages, 3)
        self.assertLessEqual(len(res.items), 2)

        # Item schema
        item = res.items[0]
        self.assertIsInstance(item, SneakerResponse)
        self.assertIsNotNone(item.product_id)
        self.assertIsNotNone(item.latest_price)

        # Search filtering
        search_res = get_products(search="Chicago", include_demo=True)
        self.assertGreaterEqual(search_res.total, 1)
        self.assertIn("Chicago", search_res.items[0].name)

        # Brand filtering
        brand_res = get_products(brand="Nike", include_demo=True)
        self.assertGreaterEqual(brand_res.total, 1)
        for p in brand_res.items:
            self.assertEqual(p.brand, "Nike")

    # 3. GET /api/products/{product_id}
    def test_03_product_detail_and_404(self):
        prod = get_product("DZ5485-612")
        self.assertIsInstance(prod, SneakerResponse)
        self.assertEqual(prod.product_id, "DZ5485-612")
        self.assertEqual(prod.retail_price, 180.0)
        self.assertIsNotNone(prod.latest_price)

        # 404 for non-existent product
        with self.assertRaises(HTTPException) as ctx:
            get_product("UNKNOWN-STYLE-CODE-999")
        self.assertEqual(ctx.exception.status_code, 404)

    # 4. GET /api/brands
    def test_04_brands_endpoint(self):
        res = get_brands(include_demo=True)
        self.assertIsInstance(res, BrandsListResponse)
        self.assertGreater(res.total_brands, 0)

        brand_names = [b.brand for b in res.brands]
        self.assertIn("Air Jordan", brand_names)

        b0 = res.brands[0]
        self.assertGreater(b0.product_count, 0)
        self.assertIsNotNone(b0.avg_price)

    # 5. GET /api/dashboard
    def test_05_dashboard_endpoint(self):
        res = get_dashboard(include_demo=True)
        self.assertIsInstance(res, DashboardResponse)
        self.assertGreater(res.total_products, 0)
        self.assertGreater(res.total_snapshots, 0)
        self.assertGreater(res.unique_brands, 0)
        self.assertIsNotNone(res.descriptive_summary.mean)
        self.assertIsNotNone(res.descriptive_summary.median)
        self.assertIsInstance(res.price_distribution, list)
        self.assertIsInstance(res.brand_comparison, list)
        self.assertIsInstance(res.price_trends, list)

    # 6. GET /api/price-history/{product_id}
    def test_06_price_history_and_404(self):
        res = get_price_history("DZ5485-612", include_demo=True)
        self.assertIsInstance(res, ProductPriceHistoryResponse)
        self.assertEqual(res.product_id, "DZ5485-612")
        self.assertGreater(res.total_snapshots, 0)
        self.assertGreater(len(res.snapshots), 0)

        s0 = res.snapshots[0]
        self.assertGreater(s0.price, 0)
        self.assertIsNotNone(s0.collection_date)
        self.assertIsNotNone(s0.platform)

        # 404 test
        with self.assertRaises(HTTPException) as ctx:
            get_price_history("UNKNOWN-STYLE-CODE-999")
        self.assertEqual(ctx.exception.status_code, 404)

    # 7. GET /api/analytics/brands
    def test_07_analytics_brands(self):
        res = get_analytics_brands(include_demo=True)
        self.assertIsInstance(res, BrandAnalyticsResponse)
        self.assertGreater(res.total_brands_analyzed, 0)
        b0 = res.brands[0]
        self.assertIsNotNone(b0.brand)
        self.assertIsNotNone(b0.mean_price)
        self.assertIsNotNone(b0.median_price)

    # 8. GET /api/analytics/price-trends
    def test_08_analytics_price_trends(self):
        res = get_analytics_price_trends(include_demo=True)
        self.assertIsInstance(res, PriceTrendsResponse)
        self.assertIsInstance(res.daily_trends, list)
        self.assertIn(res.direction, ["appreciating", "depreciating", "stable", "insufficient_data"])

    # 9. GET /api/statistics/anova
    def test_09_statistics_anova(self):
        res = get_statistics_anova(alpha=0.05, include_demo=True)
        self.assertIsInstance(res, AnovaResponse)
        self.assertEqual(res.hypothesis, "HYPOTHESIS 1 — BRAND VS PRICE")
        self.assertEqual(res.test_type, "One-Way ANOVA")
        self.assertIn(res.decision, ["Reject H0", "Fail to reject H0", "Insufficient Data"])
        # Scientific Rule: Never say H0 is proven true
        self.assertNotIn("proven true", res.interpretation.lower())

    # 10. GET /api/statistics/correlation
    def test_10_statistics_correlation(self):
        res = get_statistics_correlation(alpha=0.05, include_demo=True)
        self.assertIsInstance(res, CorrelationResponse)

        # Hypothesis 2
        h2 = res.price_trend_hypothesis
        self.assertEqual(h2.hypothesis, "HYPOTHESIS 2 — PRICE TREND")
        self.assertIn(h2.decision, ["Reject H0", "Fail to reject H0"])
        self.assertNotIn("proven true", h2.interpretation.lower())

        # Hypothesis 3 - NON-NEGOTIABLE RULE
        h3 = res.price_rating_hypothesis
        self.assertEqual(h3.message, "Insufficient reliable rating data.")

    # 11. GET /api/data-quality
    def test_11_data_quality(self):
        res = get_data_quality()
        self.assertIsInstance(res, DataQualityResponse)
        self.assertIn(res.status, ["success", "info"])
        self.assertGreaterEqual(res.metrics.clean_records, 0)
        self.assertGreaterEqual(res.metrics.cleaning_percentage, 0.0)

    # 12. POST /api/collector/run
    def test_12_collector_run(self):
        # Demo seed execution
        req = CollectorRunRequest(demo=True)
        res = run_collector(req)
        self.assertIsInstance(res, CollectorRunResponse)
        self.assertEqual(res.status, "success")
        self.assertGreater(res.records_collected, 0)
        self.assertGreaterEqual(res.snapshots_inserted + res.snapshots_ignored_duplicates, 20)

        # Unconfigured behavior test
        orig_key = os.environ.get("SOLESCOUT_API_KEY")
        if "SOLESCOUT_API_KEY" in os.environ:
            del os.environ["SOLESCOUT_API_KEY"]
        try:
            req_live = CollectorRunRequest(queries="Jordan", demo=False)
            res_live = run_collector(req_live)
            self.assertIn(res_live.status, ["unconfigured", "success", "error"])
            # Never leak secrets
            self.assertNotIn("api_key", str(res_live.model_dump()).lower())
        finally:
            if orig_key:
                os.environ["SOLESCOUT_API_KEY"] = orig_key


if __name__ == "__main__":
    unittest.main()
