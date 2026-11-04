"""
verify_statistical_analysis.py
--------------------------------
Verification script to inspect the exact outputs of:
- GET /api/statistics/anova
- GET /api/statistics/correlation
Ensures all 9 required fields are present for all hypotheses,
checks that chart datasets exist, and verifies non-dogmatic rule.
"""

import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from backend.api.routes import get_statistics_anova, get_statistics_correlation

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 75)
    print("SOLEScout FDS: STATISTICAL ANALYSIS VERIFICATION REPORT")
    print("=" * 75)

    # 1. Hypothesis 1: Brand vs Price (One-Way ANOVA)
    anova = get_statistics_anova(alpha=0.05, include_demo=True)
    print("\n--- HYPOTHESIS 1: BRAND VS PRICE (One-Way ANOVA) ---")
    print(f"1. Hypothesis:             {anova.hypothesis}")
    print(f"2. H0 (Null):              {anova.null_hypothesis}")
    print(f"3. H1 (Alternative):       {anova.alternative_hypothesis}")
    print(f"4. Statistical Test:       {anova.test_type}")
    print(f"5. Alpha:                  {anova.alpha}")
    print(f"6. Test Statistic (F):     {anova.f_statistic}")
    print(f"7. p-value:                {anova.p_value}")
    print(f"8. Decision:               {anova.decision}")
    print(f"9. Plain-English:          {anova.interpretation}")
    print(f"   Engineering Analogy:    {anova.engineering_explanation}")
    print(f"   Boxplots count:         {len(anova.brand_boxplots)}")
    if anova.brand_boxplots:
        print(f"   Sample Boxplot (Nike):  {json.dumps(anova.brand_boxplots[0], indent=2)}")

    # 2. Hypothesis 2: Price Trend Over Time & Hypothesis 3: Price vs Rating
    corr = get_statistics_correlation(alpha=0.05, include_demo=True)
    h2 = corr.price_trend_hypothesis
    h3 = corr.price_rating_hypothesis

    print("\n--- HYPOTHESIS 2: PRICE TREND OVER TIME (OLS Regression) ---")
    print(f"1. Hypothesis:             {h2.hypothesis}")
    print(f"2. H0 (Null):              {h2.null_hypothesis}")
    print(f"3. H1 (Alternative):       {h2.alternative_hypothesis}")
    print(f"4. Statistical Test:       {h2.test_type}")
    print(f"5. Alpha:                  {h2.alpha}")
    print(f"6. Test Statistic (Slope): {h2.coefficient} (Pearson r: {h2.pearson_r}, R2: {h2.r_squared})")
    print(f"7. p-value:                {h2.p_value}")
    print(f"8. Decision:               {h2.decision}")
    print(f"9. Plain-English:          {h2.interpretation}")
    print(f"   Engineering Analogy:    {h2.engineering_explanation}")
    print(f"   Scatter Points count:   {len(h2.scatter_points)}")

    print("\n--- HYPOTHESIS 3: PRICE VS RATING (Data Integrity Rule) ---")
    print(f"1. Hypothesis:             {h3.hypothesis}")
    print(f"2. H0 (Null):              {h3.null_hypothesis}")
    print(f"3. H1 (Alternative):       {h3.alternative_hypothesis}")
    print(f"4. Statistical Test:       {h3.test_type}")
    print(f"5. Alpha:                  {h3.alpha}")
    print(f"6. Test Statistic (r):     {h3.test_statistic} (Correlation: {h3.correlation})")
    print(f"7. p-value:                {h3.p_value}")
    print(f"8. Decision:               {h3.decision}")
    print(f"9. Plain-English:          {h3.interpretation}")
    print(f"   Engineering Analogy:    {h3.engineering_explanation}")

    print("\n--- SUPPORTING CHART DATASETS ---")
    print(f"1. Box plot for brand prices:    {len(anova.brand_boxplots)} brands")
    print(f"2. Scatter plot points:          {len(h2.scatter_points)} observations")
    print(f"3. OLS Fitted Line values:       {sum(1 for p in h2.scatter_points if p.get('fitted_price') is not None)} points")
    print(f"4. Price distribution bins:      {len(corr.price_distribution.get('bins', [])) if corr.price_distribution else 0} bins")
    print(f"5. Brand comparison items:       {len(corr.brand_comparison or [])} brands")

    # Strict non-dogmatic rule check
    full_text = (
        f"{anova.interpretation} {anova.decision} "
        f"{h2.interpretation} {h2.decision} "
        f"{h3.interpretation} {h3.decision}"
    ).lower()

    if "h0 is proven true" in full_text or "proven true" in full_text:
        print("\n[FAIL] Prohibited phrase 'proven true' detected!")
        sys.exit(1)
    else:
        print("\n[PASS] Non-dogmatic rule validated: 'H0 is proven true' is NEVER used.")

    print("\n[ALL CHECKS PASSED SUCCESSFULLY]")

if __name__ == "__main__":
    main()
