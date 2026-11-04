"""
Unit tests for SoleScout Statistical Analytics Engine (Phase 4)
"""

import os
import sys
import unittest
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.analytics import (
    compute_descriptive_stats,
    detect_price_outliers,
    compute_price_trend,
    compare_platforms,
    compute_price_distribution,
    analyze_brand_prices,
    analyze_price_trends_over_time,
    analyze_product_price_changes,
    test_hypothesis_1_brand_vs_price,
    test_hypothesis_2_price_trend,
    test_hypothesis_3_price_vs_rating,
    get_chart_ready_data,
)


class TestAnalyticsEngine(unittest.TestCase):
    def test_descriptive_stats_empty(self):
        """Empty input must return None for metrics, never invent values."""
        res = compute_descriptive_stats([])
        self.assertEqual(res["count"], 0)
        self.assertIsNone(res["mean"])
        self.assertIsNone(res["median"])
        self.assertIsNone(res["std_dev"])

    def test_descriptive_stats_known_distribution(self):
        """Test calculations on known values: [100, 200, 300, 400, 500], retail 200."""
        prices = [100.0, 200.0, 300.0, 400.0, 500.0]
        res = compute_descriptive_stats(prices, retail_price=200.0)

        self.assertEqual(res["count"], 5)
        self.assertEqual(res["mean"], 300.0)
        self.assertEqual(res["median"], 300.0)
        self.assertEqual(res["min_price"], 100.0)
        self.assertEqual(res["max_price"], 500.0)
        self.assertEqual(res["q1"], 200.0)
        self.assertEqual(res["q3"], 400.0)
        self.assertEqual(res["iqr"], 200.0)
        # Resale premium: ((300 - 200) / 200) * 100 = 50.0%
        self.assertEqual(res["resale_premium_pct"], 50.0)

    def test_outlier_detection_iqr_and_zscore(self):
        """Test detection of statistical outliers using Tukey IQR and Z-scores."""
        # 10 prices around 300-320, plus one massive outlier at 800
        records = [
            {"id": i, "price": 300.0 + (i * 2), "collection_date": f"2026-03-0{i+1}", "platform": "StockX"}
            for i in range(1, 10)
        ]
        records.append({"id": 99, "price": 800.0, "collection_date": "2026-03-10", "platform": "eBay"})

        res = detect_price_outliers(records, z_threshold=2.0)
        self.assertEqual(res["total_records"], 10)
        self.assertGreaterEqual(res["outliers_count"], 1)

        outlier_ids = [o["id"] for o in res["outliers"]]
        self.assertIn(99, outlier_ids)

        outlier_record = next(o for o in res["outliers"] if o["id"] == 99)
        self.assertEqual(outlier_record["price"], 800.0)
        self.assertIn(outlier_record["method"], ["IQR", "Z-score", "Both"])

    def test_price_trend_linear_regression(self):
        """Verify SciPy linear regression price trends and direction."""
        # 1 point -> insufficient data
        single = [{"price": 200.0, "collection_date": "2026-03-01"}]
        self.assertEqual(compute_price_trend(single)["direction"], "insufficient_data")

        # Strongly appreciating trend (prices going up by 10/day)
        appreciating = [
            {"price": 200.0, "collection_date": "2026-03-01"},
            {"price": 220.0, "collection_date": "2026-03-03"},
            {"price": 240.0, "collection_date": "2026-03-05"},
            {"price": 260.0, "collection_date": "2026-03-07"},
            {"price": 280.0, "collection_date": "2026-03-09"},
        ]
        res = compute_price_trend(appreciating)
        self.assertEqual(res["direction"], "appreciating")
        self.assertGreater(res["slope"], 0)
        self.assertAlmostEqual(res["r_squared"], 1.0, places=2)

    def test_platform_comparison(self):
        """Test platform aggregation and metrics."""
        records = [
            {"platform": "StockX", "price": 300.0},
            {"platform": "StockX", "price": 320.0},
            {"platform": "GOAT", "price": 310.0},
            {"platform": "Flight Club", "price": 350.0},
        ]
        comparison = compare_platforms(records)
        self.assertEqual(len(comparison), 3)

        stockx = next(p for p in comparison if p["platform"] == "StockX")
        self.assertEqual(stockx["listing_count"], 2)
        self.assertEqual(stockx["mean_price"], 310.0)
        self.assertEqual(stockx["min_price"], 300.0)
        self.assertEqual(stockx["max_price"], 320.0)

    def test_price_distribution_bins(self):
        """Verify histogram binning and percentage calculations."""
        df = pd.DataFrame({"price": [100.0, 150.0, 200.0, 250.0, 300.0, 350.0, 400.0, 450.0]})
        dist = compute_price_distribution(df, num_bins=4)
        self.assertEqual(dist["count"], 8)
        self.assertEqual(len(dist["bins"]), 4)
        total_pct = sum(b["percentage"] for b in dist["bins"])
        self.assertAlmostEqual(total_pct, 100.0, places=1)

    def test_analyze_brand_prices(self):
        """Verify brand-wise grouping, means, medians, and IQR."""
        df = pd.DataFrame({
            "brand": ["Nike", "Nike", "Adidas", "Adidas", "Adidas"],
            "price": [120.0, 180.0, 80.0, 100.0, 120.0],
        })
        brands = analyze_brand_prices(df)
        self.assertEqual(len(brands), 2)
        nike = next(b for b in brands if b["brand"] == "Nike")
        self.assertEqual(nike["count"], 2)
        self.assertEqual(nike["mean_price"], 150.0)
        self.assertEqual(nike["median_price"], 150.0)

        adidas = next(b for b in brands if b["brand"] == "Adidas")
        self.assertEqual(adidas["count"], 3)
        self.assertEqual(adidas["mean_price"], 100.0)
        self.assertEqual(adidas["median_price"], 100.0)

    def test_analyze_price_trends_over_time(self):
        """Verify temporal aggregation across collection dates."""
        df = pd.DataFrame({
            "collection_date": ["2026-11-01", "2026-11-01", "2026-11-02"],
            "price": [100.0, 200.0, 180.0],
        })
        trends = analyze_price_trends_over_time(df)
        self.assertIn("daily_trends", trends)
        self.assertEqual(len(trends["daily_trends"]), 2)
        d1 = next(t for t in trends["daily_trends"] if t["date"] == "2026-11-01")
        self.assertEqual(d1["count"], 2)
        self.assertEqual(d1["mean_price"], 150.0)

    def test_analyze_product_price_changes(self):
        """Verify individual product trajectory tracking."""
        df = pd.DataFrame({
            "product_id": ["P1", "P1", "P2"],
            "product_name": ["Shoe 1", "Shoe 1", "Shoe 2"],
            "collection_date": ["2026-11-01", "2026-11-02", "2026-11-01"],
            "price": [100.0, 120.0, 200.0],
        })
        changes = analyze_product_price_changes(df)
        self.assertEqual(len(changes), 2)
        p1 = next(c for c in changes if c["product_id"] == "P1")
        self.assertEqual(p1["initial_price"], 100.0)
        self.assertEqual(p1["latest_price"], 120.0)
        self.assertEqual(p1["price_change"], 20.0)
        self.assertEqual(p1["percent_change"], 20.0)
        self.assertEqual(p1["trajectory"], "increased")

    def test_hypothesis_1_brand_vs_price_anova(self):
        """Verify One-Way ANOVA execution, alpha threshold, and scientific non-dogmatic rule."""
        # Case A: Insufficient data (< 2 eligible brands)
        df_single = pd.DataFrame({"brand": ["Nike", "Nike"], "price": [100.0, 120.0]})
        res_single = test_hypothesis_1_brand_vs_price(df_single, alpha=0.05)
        self.assertEqual(res_single["decision"], "Insufficient Data")
        self.assertIsNone(res_single["f_statistic"])

        # Case B: Significant difference among brands (Reject H0)
        df_sig = pd.DataFrame({
            "brand": ["Luxury", "Luxury", "Luxury", "Budget", "Budget", "Budget"],
            "price": [1000.0, 1050.0, 980.0, 50.0, 60.0, 55.0],
        })
        res_sig = test_hypothesis_1_brand_vs_price(df_sig, alpha=0.05)
        self.assertEqual(res_sig["decision"], "Reject H0")
        self.assertLess(res_sig["p_value"], 0.05)
        self.assertIsNotNone(res_sig["f_statistic"])
        self.assertNotIn("proven true", res_sig["interpretation"].lower())

        # Case C: No significant difference (Fail to reject H0)
        df_nonsig = pd.DataFrame({
            "brand": ["BrandA", "BrandA", "BrandA", "BrandB", "BrandB", "BrandB"],
            "price": [100.0, 101.0, 99.0, 100.5, 99.5, 101.0],
        })
        res_nonsig = test_hypothesis_1_brand_vs_price(df_nonsig, alpha=0.05)
        self.assertEqual(res_nonsig["decision"], "Fail to reject H0")
        self.assertGreaterEqual(res_nonsig["p_value"], 0.05)
        # CRITICAL RULE: Never say H0 is proven true
        self.assertNotIn("proven true", res_nonsig["interpretation"].lower())

    def test_hypothesis_2_price_trend(self):
        """Verify Hypothesis 2 trend regression and non-dogmatic rule."""
        df = pd.DataFrame({
            "collection_date": ["2026-11-01", "2026-11-02", "2026-11-03", "2026-11-04"],
            "price": [100.0, 110.0, 120.0, 130.0],
        })
        res = test_hypothesis_2_price_trend(df, alpha=0.05)
        self.assertIn(res["decision"], ["Reject H0", "Fail to reject H0"])
        self.assertIsNotNone(res["coefficient"])
        self.assertIsNotNone(res["p_value"])
        self.assertNotIn("proven true", res["interpretation"].lower())

    def test_hypothesis_3_price_vs_rating_integrity(self):
        """
        NON-NEGOTIABLE RULE:
        If rating data is unavailable or insufficient, return exact string:
        'Insufficient reliable rating data.'
        Never generate fake ratings.
        """
        # When column is missing entirely
        df_no_rating = pd.DataFrame({"brand": ["Nike"], "price": [150.0]})
        res = test_hypothesis_3_price_vs_rating(df_no_rating)
        self.assertEqual(res["message"], "Insufficient reliable rating data.")
        self.assertIsNone(res["correlation"])

        # When column exists but all null or insufficient variance
        df_null_rating = pd.DataFrame({"brand": ["Nike", "Adidas"], "price": [150.0, 200.0], "rating": [None, None]})
        res2 = test_hypothesis_3_price_vs_rating(df_null_rating)
        self.assertEqual(res2["message"], "Insufficient reliable rating data.")

    def test_chart_ready_data_structure(self):
        """Verify get_chart_ready_data returns expected keys for Recharts."""
        df = pd.DataFrame({
            "product_id": ["P1", "P2"],
            "product_name": ["Sneaker A", "Sneaker B"],
            "brand": ["Nike", "Adidas"],
            "price": [120.0, 180.0],
            "collection_date": ["2026-11-01", "2026-11-02"],
        })
        chart_data = get_chart_ready_data(df)
        self.assertIn("price_distribution", chart_data)
        self.assertIn("brand_comparison", chart_data)
        self.assertIn("price_trends", chart_data)
        self.assertIn("outliers_scatter", chart_data)


if __name__ == "__main__":
    unittest.main()
