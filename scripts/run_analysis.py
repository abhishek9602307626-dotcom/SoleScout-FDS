"""
SoleScout FDS - Statistical Analysis & Hypothesis Testing CLI Script
Stage 5: Scientific Statistical Analysis & Modeling on Cleaned Data

Usage:
    # 1. Run full statistical analysis on cleaned dataset:
    python scripts/run_analysis.py

    # 2. Run analysis on a specific cleaned CSV file:
    python scripts/run_analysis.py --csv data/cleaned/sneakers_cleaned_latest.csv

    # 3. Include Demo/Sample Data for multi-brand / temporal hypothesis testing:
    python scripts/run_analysis.py --include-demo

Analysis Components:
1. Parametric & Non-Parametric Descriptive Statistics.
2. Price Frequency Distribution & Binned Histogram.
3. Brand-Wise Cross-Sectional Pricing Analysis.
4. Temporal Price Trends & OLS Linear Regression.
5. Product-Level Price Trajectory & Velocity.
6. Formal FDS Hypotheses:
   - HYPOTHESIS 1: Brand vs. Price (One-Way ANOVA, alpha=0.05)
   - HYPOTHESIS 2: Price Trend Over Time (Linear Regression & Pearson Correlation)
   - HYPOTHESIS 3: Price vs. Rating (Pearson Correlation or "Insufficient reliable rating data.")
7. Chart-Ready Data Export for React / Recharts visualization.
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

from services.analytics import (
    load_cleaned_data,
    compute_descriptive_stats,
    compute_price_distribution,
    analyze_brand_prices,
    analyze_price_trends_over_time,
    analyze_product_price_changes,
    test_hypothesis_1_brand_vs_price,
    test_hypothesis_2_price_trend,
    test_hypothesis_3_price_vs_rating,
    get_chart_ready_data,
    CLEANED_DIR,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="SoleScout Statistical Analysis & Hypothesis Testing Engine (Stage 5)"
    )
    parser.add_argument(
        "--csv",
        type=str,
        default=None,
        help="Path to specific cleaned CSV file (default: data/cleaned/sneakers_cleaned_latest.csv)",
    )
    parser.add_argument(
        "--include-demo",
        action="store_true",
        help="Include clearly marked Demo/Sample Data to test multi-brand and temporal hypotheses",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level for hypothesis tests (default: 0.05)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 78)
    print("SoleScout Sneaker Price Intelligence & Analytics")
    print("STAGE 5: FDS Statistical Analysis & Hypothesis Testing")
    print("=" * 78)

    # 1. Load Cleaned Data
    df = load_cleaned_data(csv_path=args.csv, include_demo=args.include_demo)

    if df.empty:
        print("\n[!] Cleaned dataset is empty.")
        print("    Run the data cleaner first: python scripts/clean_data.py")
        sys.exit(0)

    total_records = len(df)
    valid_prices = df[df["price"].notna() & (df["price"] > 0)]["price"].values
    unique_brands = df["brand"].dropna().unique().tolist() if "brand" in df.columns else []

    print(f"\n[1] Cleaned Dataset Overview:")
    print(f"    - Cleaned Records Loaded: {total_records}")
    print(f"    - Valid Price Points    : {len(valid_prices)}")
    print(f"    - Unique Brands Tracked : {len(unique_brands)} ({', '.join(unique_brands[:6])})")

    # 2. Descriptive Statistics
    desc = compute_descriptive_stats(valid_prices)
    print("\n" + "=" * 78)
    print("📊 1. DESCRIPTIVE STATISTICS (Price in USD)")
    print("=" * 78)
    print(f"    • Count (N)             : {desc['count']}")
    print(f"    • Mean Price (x̄)        : ${desc['mean']:.2f}" if desc['mean'] else "    • Mean Price (x̄)        : N/A")
    print(f"    • Median Price (M)      : ${desc['median']:.2f}" if desc['median'] else "    • Median Price (M)      : N/A")
    print(f"    • Mode Price            : ${desc['mode']:.2f}" if desc['mode'] else "    • Mode Price            : N/A")
    print(f"    • Standard Deviation (s): ${desc['std_dev']:.2f}" if desc['std_dev'] else "    • Standard Deviation (s): N/A")
    print(f"    • Sample Variance (s²)  : {desc['variance']:.2f}" if desc['variance'] else "    • Sample Variance (s²)  : N/A")
    print(f"    • Minimum Price         : ${desc['min_price']:.2f}" if desc['min_price'] else "    • Minimum Price         : N/A")
    print(f"    • Maximum Price         : ${desc['max_price']:.2f}" if desc['max_price'] else "    • Maximum Price         : N/A")
    print(f"    • Quartile 1 (25%)      : ${desc['q1']:.2f}" if desc['q1'] else "    • Quartile 1 (25%)      : N/A")
    print(f"    • Quartile 2 (Median)   : ${desc['q2']:.2f}" if desc['q2'] else "    • Quartile 2 (Median)   : N/A")
    print(f"    • Quartile 3 (75%)      : ${desc['q3']:.2f}" if desc['q3'] else "    • Quartile 3 (75%)      : N/A")
    print(f"    • Interquartile Range   : ${desc['iqr']:.2f}" if desc['iqr'] else "    • Interquartile Range   : N/A")
    print(f"    • Coefficient of Var CV : {desc['volatility_cv']:.2f}%" if desc['volatility_cv'] else "    • Coefficient of Var CV : N/A")
    if desc.get("skewness") is not None:
        print(f"    • Skewness              : {desc['skewness']:.4f}")
    if desc.get("kurtosis") is not None:
        print(f"    • Kurtosis (Excess)     : {desc['kurtosis']:.4f}")

    # 3. Price Distribution
    dist = compute_price_distribution(df)
    print("\n" + "=" * 78)
    print("📈 2. PRICE DISTRIBUTION & HISTOGRAM BINS")
    print("=" * 78)
    print(f"    • Skewness Interpretation: {dist.get('skewness_interpretation', 'N/A')}")
    print("-" * 78)
    print(f"    {'Price Range':<22} | {'Count':<8} | {'Percentage':<12}")
    print("-" * 78)
    for b in dist.get("bins", []):
        bar = "█" * max(1, int(b["percentage"] / 5))
        print(f"    {b['bin_label']:<22} | {b['count']:<8} | {b['percentage']:>5.1f}% {bar}")
    print("-" * 78)

    # 4. Brand-Wise Price Analysis
    brands = analyze_brand_prices(df)
    print("\n" + "=" * 78)
    print("🏷️  3. BRAND-WISE PRICE ANALYSIS")
    print("=" * 78)
    print(f"    {'Brand':<18} | {'Count':<6} | {'Mean ($)':<10} | {'Median ($)':<10} | {'Std Dev':<10} | {'IQR ($)':<10}")
    print("-" * 78)
    for b in brands:
        mean_s = f"${b['mean_price']:.2f}" if b['mean_price'] else "N/A"
        med_s = f"${b['median_price']:.2f}" if b['median_price'] else "N/A"
        std_s = f"${b['std_dev']:.2f}" if b['std_dev'] else "N/A"
        iqr_s = f"${b['iqr']:.2f}" if b['iqr'] else "N/A"
        print(f"    {b['brand']:<18} | {b['count']:<6} | {mean_s:<10} | {med_s:<10} | {std_s:<10} | {iqr_s:<10}")
    print("-" * 78)

    # 5. Price Trends Over Time
    trends = analyze_price_trends_over_time(df)
    daily = trends.get("daily_trends", [])
    reg = trends.get("regression", {})
    print("\n" + "=" * 78)
    print("⏳ 4. PRICE TRENDS OVER TIME (Longitudinal Analysis)")
    print("=" * 78)
    if daily:
        print(f"    {'Date':<14} | {'Count':<6} | {'Mean Price ($)':<16} | {'Median Price ($)':<16}")
        print("-" * 78)
        for d in daily:
            print(f"    {d['date']:<14} | {d['count']:<6} | ${d['mean_price']:<15.2f} | ${d['median_price']:<15.2f}")
        print("-" * 78)
    if reg and reg.get("slope") is not None:
        print(f"    • OLS Regression Slope  : ${reg.get('slope'):.4f} / day")
        print(f"    • OLS Intercept (Base)  : ${reg.get('intercept'):.2f}")
        print(f"    • Pearson Correlation r : {reg.get('r_value')}")
        print(f"    • Coefficient Det. (R²): {reg.get('r_squared')}")
        print(f"    • Regression p-value    : {reg.get('p_value')}")
        print(f"    • Market Trend Direction: {reg.get('direction').upper()}")
    else:
        print("    • Trend Status          : Insufficient temporal snapshots for regression slope.")

    # 6. Product-Level Price Trajectory
    changes = analyze_product_price_changes(df)
    print("\n" + "=" * 78)
    print("👟 5. PRODUCT-LEVEL PRICE CHANGES")
    print("=" * 78)
    if changes:
        print(f"    {'Product Name':<32} | {'Initial':<9} | {'Latest':<9} | {'Change ($)':<11} | {'Trajectory':<10}")
        print("-" * 78)
        for c in changes[:5]:
            p_name = c['product_name'][:30]
            print(f"    {p_name:<32} | ${c['initial_price']:<8.2f} | ${c['latest_price']:<8.2f} | {c['absolute_change']:>+7.2f} ({c['percentage_change']:>+5.1f}%) | {c['trajectory']}")
        print("-" * 78)
    else:
        print("    • Status: No multi-snapshot products recorded yet.")

    # 7. Hypothesis 1: Brand vs. Price (One-Way ANOVA)
    h1 = test_hypothesis_1_brand_vs_price(df, alpha=args.alpha)
    print("\n" + "=" * 78)
    print("🔬 6. HYPOTHESIS TESTING 1 — BRAND VS PRICE (One-Way ANOVA)")
    print("=" * 78)
    print(f"    • H0: {h1['null_hypothesis']}")
    print(f"    • H1: {h1['alternative_hypothesis']}")
    print(f"    • Significance Level (α): {h1['alpha']}")
    if h1.get("f_statistic") is not None:
        print(f"    • F-Statistic           : {h1['f_statistic']:.4f}")
        print(f"    • p-value               : {h1['p_value']:.6f}")
        print(f"    • Statistical Decision  : {h1['decision']}")
    else:
        print(f"    • F-Statistic / p-value : N/A ({h1['decision']})")
    print(f"    • Scientific Interpretation:\n      \"{h1['interpretation']}\"")
    if h1.get("brand_means"):
        print(f"    • Evaluated Brand Means : {h1['brand_means']}")

    # 8. Hypothesis 2: Price Trend Over Time
    h2 = test_hypothesis_2_price_trend(df, alpha=args.alpha)
    print("\n" + "=" * 78)
    print("🔬 7. HYPOTHESIS TESTING 2 — PRICE TREND OVER TIME")
    print("=" * 78)
    print(f"    • H0: {h2['null_hypothesis']}")
    print(f"    • H1: {h2['alternative_hypothesis']}")
    print(f"    • Significance Level (α): {h2['alpha']}")
    if h2.get("coefficient") is not None:
        print(f"    • Slope Coefficient (β) : ${h2['coefficient']:.4f} / day")
        print(f"    • Pearson Correlation (r): {h2['pearson_r']}")
        print(f"    • p-value               : {h2['p_value']}")
        print(f"    • Statistical Decision  : {h2['decision']}")
    else:
        print(f"    • Test Status           : {h2['decision']}")
    print(f"    • Scientific Interpretation:\n      \"{h2['interpretation']}\"")

    # 9. Hypothesis 3: Price vs. Rating
    h3 = test_hypothesis_3_price_vs_rating(df)
    print("\n" + "=" * 78)
    print("🔬 8. HYPOTHESIS TESTING 3 — PRICE VS RATING")
    print("=" * 78)
    print(f"    • Result                : {h3['message']}")
    print(f"    • Scientific Note       :\n      \"{h3['interpretation']}\"")

    # 10. Chart-Ready Data Export
    chart_data = get_chart_ready_data(df)
    chart_export_path = os.path.join(CLEANED_DIR, "chart_data_latest.json")
    with open(chart_export_path, "w", encoding="utf-8") as f:
        json.dump(chart_data, f, indent=2)

    rel_chart = os.path.relpath(chart_export_path, PROJECT_ROOT)
    print("\n" + "=" * 78)
    print(f"[EXPORT] Chart-ready JSON saved to: {rel_chart}")
    print("=" * 78)
    print("STAGE 5 STATISTICAL ANALYSIS COMPLETE [SUCCESS]")
    print("=" * 78)


if __name__ == "__main__":
    main()
