"""
SoleScout FDS - Statistical Analytics & Hypothesis Testing Engine
Stage 5: Scientific Data Analysis using Pandas, NumPy, and SciPy

Disciplines implemented:
1. Rigorous Descriptive Statistics (Sample Variance ddof=1, Quantiles, Skewness, Kurtosis).
2. Frequency & Binned Price Distribution Analysis.
3. Brand-Wise Cross-Sectional Pricing Analysis.
4. Longitudinal Time-Series Price Trend Analysis (OLS Linear Regression).
5. Product-Level Price Trajectory & Velocity.
6. Formal Statistical Hypothesis Testing:
   - HYPOTHESIS 1 (Brand vs. Price): One-Way ANOVA (F-statistic, p-value, decision, non-dogmatic interpretation).
   - HYPOTHESIS 2 (Price Trend): OLS Regression & Pearson Correlation over collection dates.
   - HYPOTHESIS 3 (Price vs. Rating): Pearson Correlation; returns exact required string if unavailable.
7. Chart-Ready Data Transformation functions for React Recharts visualization.

NON-NEGOTIABLE RULE:
Never invent data or statistical results. Return None / Insufficient Data when sample size is inadequate.
Never state that the null hypothesis (H0) is 'proven true'.
"""

import os
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy import stats

from database import get_connection

logger = logging.getLogger("solescout.analytics")

CLEANED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "cleaned"))


# ---------------------------------------------------------------------------
# Data Loading Helper
# ---------------------------------------------------------------------------

def load_cleaned_data(
    csv_path: Optional[str] = None,
    db_path: Optional[str] = None,
    include_demo: bool = False,
) -> pd.DataFrame:
    """
    Load cleaned dataset into a Pandas DataFrame.
    - If csv_path is explicitly provided, loads that CSV.
    - If include_demo is True and no csv_path is provided, loads from SQLite normalized_sneakers (including sample data).
    - Otherwise loads cleaned real data from data/cleaned/sneakers_cleaned_latest.csv (falling back to SQLite is_demo = 0).
    """
    if csv_path:
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            if not include_demo and "is_demo" in df.columns:
                df = df[df["is_demo"] == 0].copy()
            return df
        logger.warning("Specified CSV path does not exist: %s", csv_path)

    # If demo data is explicitly requested, load from SQLite normalized_sneakers table
    if include_demo:
        conn = get_connection(db_path)
        try:
            df = pd.read_sql_query("SELECT * FROM normalized_sneakers", conn)
            logger.info("Loaded %d records (including demo) from SQLite", len(df))
            return df
        finally:
            conn.close()

    # Default: Load real cleaned data from latest CSV
    target_csv = os.path.join(CLEANED_DIR, "sneakers_cleaned_latest.csv")
    if os.path.exists(target_csv):
        try:
            df = pd.read_csv(target_csv)
            if not df.empty:
                if not include_demo and "is_demo" in df.columns:
                    df = df[df["is_demo"] == 0].copy()
                logger.info("Loaded %d cleaned real records from CSV: %s", len(df), target_csv)
                return df
        except Exception as e:
            logger.warning("Could not read cleaned CSV (%s), falling back to DB: %s", target_csv, e)

    # Fallback to SQLite normalized_sneakers table
    conn = get_connection(db_path)
    try:
        query = "SELECT * FROM normalized_sneakers WHERE is_demo = 0"
        df = pd.read_sql_query(query, conn)
        logger.info("Loaded %d real records from SQLite normalized_sneakers table", len(df))
        return df
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 1. Descriptive Statistics
# ---------------------------------------------------------------------------

def compute_descriptive_stats(
    prices: Union[List[float], np.ndarray, pd.Series],
    retail_price: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Computes rigorous parametric and non-parametric descriptive statistics.
    Uses unbiased sample variance (N-1 degrees of freedom, Bessel's correction).
    """
    if prices is None:
        clean_prices = []
    elif isinstance(prices, (pd.Series, np.ndarray)):
        clean_prices = [float(p) for p in prices if pd.notna(p) and p > 0]
    else:
        clean_prices = [float(p) for p in prices if p is not None and not np.isnan(p) and p > 0]

    n = len(clean_prices)
    if n == 0:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "mode": None,
            "std_dev": None,
            "variance": None,
            "min_price": None,
            "max_price": None,
            "q1": None,
            "q2": None,
            "q3": None,
            "iqr": None,
            "skewness": None,
            "kurtosis": None,
            "volatility_cv": None,
            "resale_premium_pct": None,
        }

    arr = np.array(clean_prices, dtype=np.float64)

    mean_val = float(np.mean(arr))
    median_val = float(np.median(arr))
    min_val = float(np.min(arr))
    max_val = float(np.max(arr))

    # Sample variance & standard deviation (ddof=1)
    if n > 1:
        variance_val = float(np.var(arr, ddof=1))
        std_val = float(np.std(arr, ddof=1))
        volatility_cv = float((std_val / mean_val) * 100.0) if mean_val > 0 else 0.0
    else:
        variance_val = 0.0
        std_val = 0.0
        volatility_cv = 0.0

    # Mode calculation
    mode_val = None
    try:
        mode_res = stats.mode(arr, keepdims=False)
        mode_val = float(mode_res.mode)
    except Exception:
        mode_val = None

    # Quartiles (25%, 50%, 75%) and Interquartile Range (IQR)
    q1_val = float(np.percentile(arr, 25))
    q2_val = median_val
    q3_val = float(np.percentile(arr, 75))
    iqr_val = float(q3_val - q1_val)

    # Shape: Skewness & Kurtosis
    skewness_val = float(stats.skew(arr)) if n >= 3 else None
    kurtosis_val = float(stats.kurtosis(arr)) if n >= 4 else None

    # Resale premium vs MSRP if retail price is provided
    premium_pct = None
    if retail_price is not None and retail_price > 0:
        premium_pct = float(((mean_val - retail_price) / retail_price) * 100.0)

    return {
        "count": n,
        "mean": round(mean_val, 2),
        "median": round(median_val, 2),
        "mode": round(mode_val, 2) if mode_val is not None else None,
        "std_dev": round(std_val, 2),
        "variance": round(variance_val, 2),
        "min_price": round(min_val, 2),
        "max_price": round(max_val, 2),
        "q1": round(q1_val, 2),
        "q2": round(q2_val, 2),
        "q3": round(q3_val, 2),
        "iqr": round(iqr_val, 2),
        "skewness": round(skewness_val, 4) if skewness_val is not None else None,
        "kurtosis": round(kurtosis_val, 4) if kurtosis_val is not None else None,
        "volatility_cv": round(volatility_cv, 2),
        "resale_premium_pct": round(premium_pct, 2) if premium_pct is not None else None,
    }


# ---------------------------------------------------------------------------
# 2. Price Distribution Analysis
# ---------------------------------------------------------------------------

def compute_price_distribution(
    df: pd.DataFrame, num_bins: int = 8
) -> Dict[str, Any]:
    """
    Computes frequency bins and distribution metrics for sneaker prices.
    Generates chart-ready histogram intervals for frontend visualization.
    """
    if df.empty or "price" not in df.columns:
        return {"total": 0, "bins": [], "skewness": None, "kurtosis": None}

    valid_prices = df[df["price"].notna() & (df["price"] > 0)]["price"].astype(float).values
    n = len(valid_prices)
    if n == 0:
        return {"total": 0, "bins": [], "skewness": None, "kurtosis": None}

    min_p = float(np.min(valid_prices))
    max_p = float(np.max(valid_prices))

    # Single price or narrow range edge-case
    if min_p == max_p:
        bins = [{
            "bin_start": min_p,
            "bin_end": max_p,
            "bin_label": f"${min_p:.0f}",
            "count": n,
            "percentage": 100.0,
        }]
    else:
        counts, bin_edges = np.histogram(valid_prices, bins=num_bins)
        bins = []
        for i in range(len(counts)):
            b_start = round(float(bin_edges[i]), 2)
            b_end = round(float(bin_edges[i + 1]), 2)
            bins.append({
                "bin_start": b_start,
                "bin_end": b_end,
                "bin_label": f"${b_start:.0f} - ${b_end:.0f}",
                "count": int(counts[i]),
                "percentage": round(float(counts[i] / n) * 100.0, 1),
            })

    skewness = round(float(stats.skew(valid_prices)), 4) if n >= 3 else None
    kurtosis = round(float(stats.kurtosis(valid_prices)), 4) if n >= 4 else None

    # Qualitative shape interpretation
    if skewness is not None:
        if skewness > 0.5:
            skew_desc = "Right-skewed (positive): majority of products at accessible prices with high-priced luxury/grail outliers."
        elif skewness < -0.5:
            skew_desc = "Left-skewed (negative): concentration toward higher market prices."
        else:
            skew_desc = "Approximately symmetric."
    else:
        skew_desc = "Insufficient data to compute skewness."

    return {
        "total": n,
        "count": n,
        "min_price": round(min_p, 2),
        "max_price": round(max_p, 2),
        "skewness": skewness,
        "kurtosis": kurtosis,
        "skewness_interpretation": skew_desc,
        "bins": bins,
    }


# ---------------------------------------------------------------------------
# 3. Brand-Wise Price Analysis
# ---------------------------------------------------------------------------

def analyze_brand_prices(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Cross-sectional price analysis aggregated across canonical footwear brands.
    Computes count, mean, median, standard deviation, quartiles, and IQR per brand.
    """
    if df.empty or "brand" not in df.columns or "price" not in df.columns:
        return []

    valid = df[df["brand"].notna() & df["price"].notna() & (df["price"] > 0)].copy()
    if valid.empty:
        return []

    results = []
    for brand_name, group in valid.groupby("brand"):
        prices = group["price"].astype(float).values
        brand_stats = compute_descriptive_stats(prices)
        results.append({
            "brand": str(brand_name),
            "count": brand_stats["count"],
            "mean_price": brand_stats["mean"],
            "median_price": brand_stats["median"],
            "std_dev": brand_stats["std_dev"],
            "min_price": brand_stats["min_price"],
            "max_price": brand_stats["max_price"],
            "q1": brand_stats["q1"],
            "q3": brand_stats["q3"],
            "iqr": brand_stats["iqr"],
            "volatility_cv": brand_stats["volatility_cv"],
        })

    # Sort descending by listing volume, then median price
    results.sort(key=lambda x: (x["count"], x["median_price"] or 0), reverse=True)
    return results


# ---------------------------------------------------------------------------
# 4. Price Trends Over Time
# ---------------------------------------------------------------------------

def analyze_price_trends_over_time(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Aggregates cleaned sneaker price observations by collection_date.
    Fits an Ordinary Least Squares (OLS) regression line across dates.
    """
    if df.empty or "collection_date" not in df.columns or "price" not in df.columns:
        return {
            "daily_trends": [],
            "regression": None,
            "direction": "insufficient_data",
        }

    valid = df[df["collection_date"].notna() & df["price"].notna() & (df["price"] > 0)].copy()
    if valid.empty:
        return {
            "daily_trends": [],
            "regression": None,
            "direction": "insufficient_data",
        }

    # Group by collection_date
    daily = (
        valid.groupby("collection_date")["price"]
        .agg(["count", "mean", "median", "min", "max", "std"])
        .reset_index()
        .sort_values("collection_date")
    )

    daily_trends = []
    for _, row in daily.iterrows():
        daily_trends.append({
            "date": str(row["collection_date"]),
            "count": int(row["count"]),
            "mean_price": round(float(row["mean"]), 2),
            "median_price": round(float(row["median"]), 2),
            "min_price": round(float(row["min"]), 2),
            "max_price": round(float(row["max"]), 2),
            "std_dev": round(float(row["std"]), 2) if pd.notna(row["std"]) else 0.0,
        })

    # Linear regression across individual observations
    records_list = valid[["collection_date", "price"]].to_dict(orient="records")
    regression_stats = compute_price_trend(records_list)

    return {
        "daily_trends": daily_trends,
        "regression": regression_stats,
        "direction": regression_stats.get("direction", "stable"),
    }


def compute_price_trend(price_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Fits Ordinary Least Squares (OLS) Linear Regression using SciPy on historical snapshots.
    Maps collection_date to days elapsed since initial collection date.
    """
    if not price_records or len(price_records) < 2:
        return {
            "slope": None,
            "intercept": None,
            "r_value": None,
            "r_squared": None,
            "p_value": None,
            "std_err": None,
            "direction": "insufficient_data",
            "data_points": len(price_records) if price_records else 0,
        }

    sorted_records = sorted(
        [r for r in price_records if r.get("collection_date") and r.get("price")],
        key=lambda x: str(x["collection_date"]),
    )

    if len(sorted_records) < 2:
        return {
            "slope": None,
            "intercept": None,
            "r_value": None,
            "r_squared": None,
            "p_value": None,
            "std_err": None,
            "direction": "insufficient_data",
            "data_points": len(sorted_records),
        }

    try:
        t0 = datetime.strptime(str(sorted_records[0]["collection_date"])[:10], "%Y-%m-%d")
        days = []
        prices = []
        for r in sorted_records:
            d = datetime.strptime(str(r["collection_date"])[:10], "%Y-%m-%d")
            delta_days = (d - t0).days
            days.append(float(delta_days))
            prices.append(float(r["price"]))

        x = np.array(days, dtype=np.float64)
        y = np.array(prices, dtype=np.float64)

        # If all records belong to the exact same day
        if np.all(x == x[0]):
            return {
                "slope": 0.0,
                "intercept": round(float(np.mean(y)), 2),
                "r_value": 0.0,
                "r_squared": 0.0,
                "p_value": 1.0,
                "std_err": 0.0,
                "direction": "stable (single date)",
                "data_points": len(prices),
            }

        res = stats.linregress(x, y)
        slope = float(res.slope)
        intercept = float(res.intercept)
        r_val = float(res.rvalue)
        r2 = float(r_val ** 2)
        p_val = float(res.pvalue)
        std_err = float(res.stderr) if res.stderr is not None else 0.0

        if p_val < 0.05:
            direction = "appreciating" if slope > 0 else "depreciating"
        else:
            direction = "stable"

        return {
            "slope": round(slope, 4),
            "intercept": round(intercept, 2),
            "r_value": round(r_val, 4),
            "r_squared": round(r2, 4),
            "p_value": round(p_val, 4),
            "std_err": round(std_err, 4),
            "direction": direction,
            "data_points": len(prices),
        }
    except Exception as e:
        logger.warning("Linear regression failed: %s", e)
        return {
            "slope": None,
            "intercept": None,
            "r_value": None,
            "r_squared": None,
            "p_value": None,
            "std_err": None,
            "direction": "insufficient_data",
            "data_points": len(sorted_records),
        }


# ---------------------------------------------------------------------------
# 5. Product-Level Price Trajectory & Velocity
# ---------------------------------------------------------------------------

def analyze_product_price_changes(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Calculates product-level price changes across temporal snapshots:
    - First observed price vs. latest observed price
    - Absolute difference ($)
    - Percentage difference (%)
    """
    if df.empty or "product_id" not in df.columns or "price" not in df.columns:
        return []

    valid = df[df["product_id"].notna() & df["price"].notna() & (df["price"] > 0)].copy()
    if valid.empty:
        return []

    changes = []
    for pid, group in valid.groupby("product_id"):
        sorted_group = group.sort_values("collection_date")
        n_obs = len(sorted_group)

        first_row = sorted_group.iloc[0]
        latest_row = sorted_group.iloc[-1]

        first_price = float(first_row["price"])
        latest_price = float(latest_row["price"])
        abs_change = round(latest_price - first_price, 2)
        pct_change = round(((latest_price - first_price) / first_price) * 100.0, 2) if first_price > 0 else 0.0

        if abs_change > 0.01:
            trajectory = "increased"
        elif abs_change < -0.01:
            trajectory = "decreased"
        else:
            trajectory = "unchanged"

        changes.append({
            "product_id": str(pid),
            "product_name": str(latest_row.get("product_name") or latest_row.get("name") or pid),
            "brand": str(latest_row.get("brand") or "Unknown"),
            "snapshots_count": n_obs,
            "initial_price": first_price,
            "latest_price": latest_price,
            "absolute_change": abs_change,
            "price_change": abs_change,
            "percentage_change": pct_change,
            "percent_change": pct_change,
            "trajectory": trajectory,
            "first_observed_date": str(first_row.get("collection_date")),
            "latest_observed_date": str(latest_row.get("collection_date")),
        })

    # Sort by absolute percentage change descending
    changes.sort(key=lambda x: abs(x["percentage_change"]), reverse=True)
    return changes


# ---------------------------------------------------------------------------
# 6. Formal Hypothesis Testing
# ---------------------------------------------------------------------------

def test_hypothesis_1_brand_vs_price(
    df: pd.DataFrame, alpha: float = 0.05
) -> Dict[str, Any]:
    """
    HYPOTHESIS 1 — BRAND VS PRICE (One-Way ANOVA)

    H0: There is no statistically significant difference in mean sneaker prices
        among the selected brands. (mu_1 = mu_2 = ... = mu_k)
    H1: At least one brand has a statistically significantly different mean sneaker price.

    Statistical Method: One-Way Analysis of Variance (ANOVA, scipy.stats.f_oneway).
    Significance Level: alpha = 0.05
    Decision:
        p < 0.05  -> Reject H0
        p >= 0.05 -> Fail to reject H0
    CRITICAL RULE: Never state that H0 is 'proven true'.
    """
    valid = df[df["brand"].notna() & df["price"].notna() & (df["price"] > 0)].copy()

    # Filter to brands with at least 2 price observations
    brand_groups: Dict[str, List[float]] = {}
    for brand_name, grp in valid.groupby("brand"):
        prices = [float(p) for p in grp["price"].values if p > 0]
        if len(prices) >= 2:
            brand_groups[str(brand_name)] = prices

    k_groups = len(brand_groups)
    total_samples = sum(len(v) for v in brand_groups.values())

    if k_groups < 2:
        return {
            "hypothesis": "HYPOTHESIS 1 — BRAND VS PRICE",
            "test_type": "One-Way ANOVA",
            "null_hypothesis": "There is no statistically significant difference in mean sneaker prices among the selected brands.",
            "alternative_hypothesis": "At least one brand has a statistically significantly different mean sneaker price.",
            "alpha": alpha,
            "f_statistic": None,
            "test_statistic": None,
            "p_value": None,
            "decision": "Insufficient Data",
            "interpretation": (
                f"One-Way ANOVA requires at least 2 distinct brands each with >= 2 observations. "
                f"Currently available: {k_groups} eligible brand groups with {total_samples} total observations. "
                f"Collect more multi-brand data to perform this test."
            ),
            "engineering_explanation": (
                "In circuit design and signals/systems, think of One-Way ANOVA as calculating the Signal-to-Noise Ratio (SNR). "
                "The 'Signal' is the variance between different brand price means (systematic brand effect). "
                "The 'Noise' is the random variance of sneaker prices within the same brand. "
                "The F-statistic is the ratio: F = Variance Between / Variance Within. "
                "When F is large and p < 0.05, the brand signal significantly exceeds random market noise."
            ),
            "brands_evaluated": list(brand_groups.keys()),
            "brand_sample_sizes": {b: len(v) for b, v in brand_groups.items()},
            "brand_means": {b: round(float(np.mean(v)), 2) for b, v in brand_groups.items()},
            "brand_boxplots": [],
        }

    # Compute boxplot parameters for each brand
    brand_boxplots = []
    for b_name, prices in brand_groups.items():
        arr = np.array(prices, dtype=np.float64)
        q1 = float(np.percentile(arr, 25))
        med = float(np.median(arr))
        q3 = float(np.percentile(arr, 75))
        iqr = q3 - q1
        min_w = float(max(np.min(arr), q1 - 1.5 * iqr))
        max_w = float(min(np.max(arr), q3 + 1.5 * iqr))
        brand_boxplots.append({
            "brand": b_name,
            "q1": round(q1, 2),
            "median": round(med, 2),
            "q3": round(q3, 2),
            "min_whisker": round(min_w, 2),
            "max_whisker": round(max_w, 2),
            "mean": round(float(np.mean(arr)), 2),
            "sample_size": len(arr),
        })

    # Execute One-Way ANOVA
    f_stat, p_val = stats.f_oneway(*brand_groups.values())
    f_stat = float(f_stat) if pd.notna(f_stat) else None
    p_val = float(p_val) if pd.notna(p_val) else None

    if p_val is not None:
        if p_val < alpha:
            decision = "Reject H0"
            interpretation = (
                f"With p = {p_val:.4f} < {alpha}, we reject the null hypothesis. "
                f"There is a statistically significant difference in mean sneaker prices among the brands tested "
                f"(F = {f_stat:.4f}, p = {p_val:.4f}). At least one brand's mean price differs significantly."
            )
        else:
            decision = "Fail to reject H0"
            interpretation = (
                f"With p = {p_val:.4f} >= {alpha}, we fail to reject the null hypothesis. "
                f"There is insufficient statistical evidence to conclude a significant difference in mean sneaker prices "
                f"among the evaluated brands (F = {f_stat:.4f}, p = {p_val:.4f}). "
                f"Note: This does not prove the null hypothesis is true; it indicates current data does not detect an effect."
            )
    else:
        decision = "Indeterminate"
        interpretation = "ANOVA calculation produced undefined variance (e.g., zero intra-group variance)."

    return {
        "hypothesis": "HYPOTHESIS 1 — BRAND VS PRICE",
        "test_type": "One-Way ANOVA",
        "null_hypothesis": "There is no statistically significant difference in mean sneaker prices among the selected brands.",
        "alternative_hypothesis": "At least one brand has a statistically significantly different mean sneaker price.",
        "alpha": alpha,
        "f_statistic": round(f_stat, 4) if f_stat is not None else None,
        "test_statistic": round(f_stat, 4) if f_stat is not None else None,
        "p_value": round(p_val, 6) if p_val is not None else None,
        "decision": decision,
        "interpretation": interpretation,
        "engineering_explanation": (
            "In circuit design and signals/systems, think of One-Way ANOVA as calculating the Signal-to-Noise Ratio (SNR). "
            "The 'Signal' is the variance between different brand price means (systematic brand effect). "
            "The 'Noise' is the random variance of sneaker prices within the same brand. "
            "The F-statistic is the ratio: F = Variance Between / Variance Within. "
            "When F is large and p < 0.05, the brand signal significantly exceeds random market noise, "
            "proving that brand prestige meaningfully drives market pricing."
        ),
        "brands_evaluated": list(brand_groups.keys()),
        "brand_sample_sizes": {b: len(v) for b, v in brand_groups.items()},
        "brand_means": {b: round(float(np.mean(v)), 2) for b, v in brand_groups.items()},
        "brand_boxplots": brand_boxplots,
    }


def test_hypothesis_2_price_trend(
    df: pd.DataFrame, alpha: float = 0.05
) -> Dict[str, Any]:
    """
    HYPOTHESIS 2 — PRICE TREND OVER TIME

    H0: There is no statistically significant relationship between collection date and sneaker price. (beta = 0)
    H1: There is a statistically significant relationship between collection date and sneaker price. (beta != 0)

    Statistical Method: Ordinary Least Squares (OLS) Linear Regression & Pearson Correlation.
    """
    valid = df[df["collection_date"].notna() & df["price"].notna() & (df["price"] > 0)].copy()

    records = valid[["collection_date", "price"]].to_dict(orient="records")
    trend = compute_price_trend(records)

    p_val = trend.get("p_value")
    slope = trend.get("slope")
    r_val = trend.get("r_value")
    n_points = trend.get("data_points", 0)

    if p_val is None or n_points < 3:
        return {
            "hypothesis": "HYPOTHESIS 2 — PRICE TREND",
            "test_type": "OLS Linear Regression & Pearson Correlation",
            "null_hypothesis": "There is no statistically significant relationship between collection date and sneaker price.",
            "alternative_hypothesis": "There is a statistically significant relationship between collection date and sneaker price.",
            "alpha": alpha,
            "test_statistic": slope,
            "coefficient": slope,
            "pearson_r": r_val,
            "p_value": p_val,
            "trend_information": trend.get("direction", "insufficient_data"),
            "decision": "Insufficient Data",
            "interpretation": (
                f"Testing temporal price trend requires multi-day longitudinal observations (>= 3 points). "
                f"Currently available: {n_points} observations. Run collection across multiple days."
            ),
            "engineering_explanation": (
                "In kinematics and dynamic systems, the regression slope (beta) represents price velocity dy/dt (dollars per day). "
                "A slope near 0 with p >= 0.05 indicates steady-state market equilibrium with stationary pricing. "
                "If p < 0.05 and beta > 0, the market demonstrates upward momentum; beta < 0 demonstrates depreciation."
            ),
            "sample_size": n_points,
            "scatter_points": [],
        }

    if p_val < alpha:
        decision = "Reject H0"
        direction = "upward appreciation" if (slope and slope > 0) else "downward depreciation"
        interpretation = (
            f"With p = {p_val:.4f} < {alpha}, we reject the null hypothesis. "
            f"There is a statistically significant relationship between collection date and sneaker price. "
            f"Observed trend exhibits {direction} with slope = ${slope:.2f}/day and Pearson r = {r_val:.4f}."
        )
    else:
        decision = "Fail to reject H0"
        interpretation = (
            f"With p = {p_val:.4f} >= {alpha}, we fail to reject the null hypothesis. "
            f"There is insufficient statistical evidence of a relationship between collection date and price "
            f"(p = {p_val:.4f}, r = {r_val:.4f}). "
            f"Note: This does not prove the null hypothesis is true; prices appear stationary over the observed window."
        )

    scatter_points = []
    if not valid.empty:
        sorted_valid = valid.sort_values("collection_date")
        t0_str = str(sorted_valid.iloc[0]["collection_date"])[:10]
        try:
            t0 = datetime.strptime(t0_str, "%Y-%m-%d")
        except Exception:
            t0 = None

        for _, row in sorted_valid.iterrows():
            d_str = str(row["collection_date"])[:10]
            days_elapsed = 0.0
            if t0:
                try:
                    days_elapsed = float((datetime.strptime(d_str, "%Y-%m-%d") - t0).days)
                except Exception:
                    pass
            p = float(row["price"])
            fitted = None
            if slope is not None and trend.get("intercept") is not None:
                fitted = round(float(trend["intercept"] + slope * days_elapsed), 2)
            scatter_points.append({
                "date": d_str,
                "days_elapsed": days_elapsed,
                "price": p,
                "fitted_price": fitted,
                "brand": str(row.get("brand") or "Unknown"),
                "product_name": str(row.get("product_name") or row.get("name") or "Sneaker"),
            })

    return {
        "hypothesis": "HYPOTHESIS 2 — PRICE TREND",
        "test_type": "OLS Linear Regression & Pearson Correlation",
        "null_hypothesis": "There is no statistically significant relationship between collection date and sneaker price.",
        "alternative_hypothesis": "There is a statistically significant relationship between collection date and sneaker price.",
        "alpha": alpha,
        "test_statistic": slope,
        "coefficient": slope,
        "pearson_r": r_val,
        "r_squared": trend.get("r_squared"),
        "p_value": p_val,
        "trend_information": trend.get("direction"),
        "decision": decision,
        "interpretation": interpretation,
        "engineering_explanation": (
            "In kinematics and dynamic systems, the regression slope (beta) represents price velocity dy/dt (dollars per day). "
            "A slope near 0 with p >= 0.05 indicates steady-state market equilibrium with stationary pricing "
            "(analogous to a DC voltage signal with minor thermal noise). "
            "If p < 0.05 and beta > 0, the market demonstrates positive momentum (appreciation); "
            "beta < 0 demonstrates market depreciation."
        ),
        "sample_size": n_points,
        "scatter_points": scatter_points,
    }


def test_hypothesis_3_price_vs_rating(df: pd.DataFrame, alpha: float = 0.05) -> Dict[str, Any]:
    """
    HYPOTHESIS 3 — PRICE VS RATING

    NON-NEGOTIABLE RULE:
    Only implement this if reliable rating data actually exists in the SoleScout dataset.
    If rating data is unavailable or insufficient, return:
    'Insufficient reliable rating data.'
    Do not generate fake ratings.
    """
    # Check if a rating column exists and contains non-null values
    if "rating" not in df.columns:
        return {
            "hypothesis": "HYPOTHESIS 3 — PRICE VS RATING",
            "test_type": "Pearson Product-Moment Correlation",
            "null_hypothesis": "There is no linear correlation between sneaker market price and product rating (rho = 0).",
            "alternative_hypothesis": "There is a statistically significant linear correlation between sneaker market price and product rating (rho != 0).",
            "alpha": alpha,
            "test_statistic": None,
            "correlation": None,
            "p_value": None,
            "status": "unavailable",
            "message": "Insufficient reliable rating data.",
            "decision": "Insufficient Data (Not Executed)",
            "interpretation": (
                "Insufficient reliable rating data. "
                "The SoleScout API indexes live retailer pricing, in-stock US sizes, and store availability; "
                "it does not collect user subjective rating scores. "
                "Per FDS integrity rules, no synthetic ratings are invented."
            ),
            "engineering_explanation": (
                "In electrical engineering and telemetry, you cannot measure circuit impedance without connecting an ammeter and voltmeter. "
                "The retailer API does not track user review rating scores. "
                "Academic engineering ethics strictly forbid synthesizing fake telemetry into our dataset."
            ),
        }

    valid = df[df["rating"].notna() & df["price"].notna() & (df["price"] > 0)]
    ratings = [float(r) for r in valid["rating"].values if pd.notna(r)]
    prices = [float(p) for p in valid["price"].values if pd.notna(p)]

    # Must have at least 3 points with actual variance to perform Pearson correlation
    if len(ratings) < 3 or np.std(ratings) < 1e-6 or np.std(prices) < 1e-6:
        return {
            "hypothesis": "HYPOTHESIS 3 — PRICE VS RATING",
            "test_type": "Pearson Product-Moment Correlation",
            "null_hypothesis": "There is no linear correlation between sneaker market price and product rating (rho = 0).",
            "alternative_hypothesis": "There is a statistically significant linear correlation between sneaker market price and product rating (rho != 0).",
            "alpha": alpha,
            "test_statistic": None,
            "correlation": None,
            "p_value": None,
            "status": "unavailable",
            "message": "Insufficient reliable rating data.",
            "decision": "Insufficient Data (Not Executed)",
            "interpretation": (
                "Insufficient reliable rating data. "
                f"Available valid rating pairs: {len(ratings)}. "
                "Pearson correlation requires at least 3 pairs with variance. No synthetic ratings are generated."
            ),
            "engineering_explanation": (
                "In electrical engineering and telemetry, you cannot measure circuit impedance without connecting an ammeter and voltmeter. "
                "The retailer API does not track user review rating scores. "
                "Academic engineering ethics strictly forbid synthesizing fake telemetry into our dataset."
            ),
        }

    # If reliable rating data ever existed, calculate Pearson correlation
    r_val, p_val = stats.pearsonr(ratings, prices)
    decision = "Reject H0" if p_val < alpha else "Fail to reject H0"
    interpretation = (
        f"With p = {p_val:.4f} < {alpha}, we reject the null hypothesis. There is a statistically significant correlation (r = {r_val:.4f})."
        if p_val < alpha else
        f"With p = {p_val:.4f} >= {alpha}, we fail to reject the null hypothesis. There is insufficient statistical evidence of a correlation between rating and price (r = {r_val:.4f}). Note: This does not prove the null hypothesis is true."
    )
    return {
        "hypothesis": "HYPOTHESIS 3 — PRICE VS RATING",
        "test_type": "Pearson Product-Moment Correlation",
        "null_hypothesis": "There is no linear correlation between sneaker market price and product rating (rho = 0).",
        "alternative_hypothesis": "There is a statistically significant linear correlation between sneaker market price and product rating (rho != 0).",
        "alpha": alpha,
        "test_statistic": round(float(r_val), 4),
        "correlation": round(float(r_val), 4),
        "p_value": round(float(p_val), 4),
        "status": "success",
        "message": "Pearson correlation computed successfully.",
        "decision": decision,
        "interpretation": interpretation,
        "engineering_explanation": (
            f"Pearson correlation r = {r_val:.4f} measures linear association. "
            "R-squared represents the proportion of variance in sneaker prices explained by customer rating."
        ),
    }


# ---------------------------------------------------------------------------
# 7. Chart-Ready Data Preparation Functions
# ---------------------------------------------------------------------------

def get_chart_ready_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Transforms statistical outputs into JSON-ready format optimized
    for Recharts / Chart.js frontend visualization components.
    """
    if df.empty:
        return {
            "price_distribution": [],
            "brand_comparison": [],
            "price_trends": [],
            "outliers_scatter": [],
        }

    # 1. Price Distribution Histogram
    dist = compute_price_distribution(df, num_bins=8)
    chart_distribution = [
        {"range": b["bin_label"], "count": b["count"], "pct": b["percentage"]}
        for b in dist.get("bins", [])
    ]

    # 2. Brand Price Comparison (Bar Chart)
    brands = analyze_brand_prices(df)
    chart_brands = [
        {
            "brand": b["brand"],
            "mean_price": b["mean_price"],
            "median_price": b["median_price"],
            "min_price": b["min_price"],
            "max_price": b["max_price"],
            "count": b["count"],
        }
        for b in brands
    ]

    # 3. Time Series Trends (Line Chart)
    trends = analyze_price_trends_over_time(df)
    chart_trends = [
        {
            "date": d["date"],
            "avg_price": d["mean_price"],
            "median_price": d["median_price"],
            "volume": d["count"],
        }
        for d in trends.get("daily_trends", [])
    ]

    # 4. Outliers Scatter Plot Data
    chart_outliers = []
    if "price" in df.columns:
        for _, row in df.iterrows():
            if pd.notna(row.get("price")):
                chart_outliers.append({
                    "product_id": str(row.get("product_id")),
                    "name": str(row.get("product_name") or row.get("name") or "Unknown"),
                    "brand": str(row.get("brand") or "Unknown"),
                    "price": float(row["price"]),
                    "retail_price": float(row["retail_price"]) if pd.notna(row.get("retail_price")) else None,
                    "is_outlier": bool(row.get("is_outlier", False)),
                })

    return {
        "price_distribution": chart_distribution,
        "brand_comparison": chart_brands,
        "price_trends": chart_trends,
        "outliers_scatter": chart_outliers,
    }


# ---------------------------------------------------------------------------
# Outlier Detection (Tukey IQR & Z-score)
# ---------------------------------------------------------------------------

def detect_price_outliers(
    price_records: List[Dict[str, Any]], z_threshold: float = 2.5
) -> Dict[str, Any]:
    """
    Detects outlier price listings using Tukey's Fences and Standardized Z-Scores.
    """
    if not price_records:
        return {
            "total_records": 0,
            "outliers_count": 0,
            "iqr_lower_bound": None,
            "iqr_upper_bound": None,
            "z_threshold": z_threshold,
            "outliers": [],
        }

    prices = []
    valid_records = []
    for r in price_records:
        p = r.get("price")
        if p is not None and not np.isnan(p) and p > 0:
            prices.append(float(p))
            valid_records.append(r)

    n = len(prices)
    if n < 3:
        return {
            "total_records": n,
            "outliers_count": 0,
            "iqr_lower_bound": None,
            "iqr_upper_bound": None,
            "z_threshold": z_threshold,
            "outliers": [],
        }

    arr = np.array(prices, dtype=np.float64)
    q1 = float(np.percentile(arr, 25))
    q3 = float(np.percentile(arr, 75))
    iqr = q3 - q1
    iqr_lower = q1 - (1.5 * iqr)
    iqr_upper = q3 + (1.5 * iqr)

    mean_val = float(np.mean(arr))
    std_val = float(np.std(arr, ddof=1)) if n > 1 else 0.0

    outliers = []
    for record in valid_records:
        price = float(record["price"])
        is_iqr = price < iqr_lower or price > iqr_upper

        z_score = None
        is_z = False
        if std_val > 1e-9:
            z_score = float((price - mean_val) / std_val)
            is_z = abs(z_score) >= z_threshold

        if is_iqr or is_z:
            if is_iqr and is_z:
                method = "Both"
                reason = f"Violates IQR bounds [{iqr_lower:.2f}, {iqr_upper:.2f}] and |Z| = {abs(z_score):.2f} >= {z_threshold}"
            elif is_iqr:
                method = "IQR"
                reason = f"Violates Tukey IQR bounds [{iqr_lower:.2f}, {iqr_upper:.2f}]"
            else:
                method = "Z-score"
                reason = f"Standardized Z-score {z_score:.2f} exceeds threshold {z_threshold}"

            outliers.append({
                "id": record.get("id"),
                "collection_date": record.get("collection_date", "N/A"),
                "platform": record.get("platform", "Unknown"),
                "price": round(price, 2),
                "method": method,
                "reason": reason,
                "z_score": round(z_score, 2) if z_score is not None else None,
                "is_outlier": True,
            })

    return {
        "total_records": n,
        "outliers_count": len(outliers),
        "iqr_lower_bound": round(iqr_lower, 2),
        "iqr_upper_bound": round(iqr_upper, 2),
        "z_threshold": z_threshold,
        "outliers": outliers,
    }


def compare_platforms(price_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Groups price snapshots by platform and computes comparative metrics."""
    if not price_records:
        return []

    df = pd.DataFrame(price_records)
    if "platform" not in df.columns or "price" not in df.columns or df.empty:
        return []

    grouped = df.groupby("platform")["price"].agg(["count", "mean", "median", "min", "max"]).reset_index()

    result = []
    for _, row in grouped.iterrows():
        result.append({
            "platform": str(row["platform"]),
            "listing_count": int(row["count"]),
            "mean_price": round(float(row["mean"]), 2),
            "median_price": round(float(row["median"]), 2),
            "min_price": round(float(row["min"]), 2),
            "max_price": round(float(row["max"]), 2),
        })

    result.sort(key=lambda x: x["listing_count"], reverse=True)
    return result
