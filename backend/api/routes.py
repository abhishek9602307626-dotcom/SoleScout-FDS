"""
SoleScout FDS - Production API Routes (Stage 6)

Comprehensive RESTful endpoints for sneaker price intelligence,
statistical modeling, outlier detection, hypothesis testing, and pipeline controls.

Endpoints Implemented:
1.  GET  /api/health
2.  GET  /api/products
3.  GET  /api/products/{product_id}
4.  GET  /api/brands
5.  GET  /api/dashboard
6.  GET  /api/price-history/{product_id}
7.  GET  /api/analytics/brands
8.  GET  /api/analytics/price-trends
9.  GET  /api/statistics/anova
10. GET  /api/statistics/correlation
11. GET  /api/data-quality
12. POST /api/collector/run

NON-NEGOTIABLE DATA INTEGRITY RULES:
- Never invent SoleScout data, prices, ratings, sellers, historical values or statistical results.
- Missing fields are stored as NULL and returned as None / null in JSON.
- Never overwrite historical snapshots; keep the UNIQUE(product_id, collection_date) constraint.
- API key only in backend .env, never in frontend code, responses, or logs.
- If there is no data, show: "No SoleScout data has been collected yet. Configure the API and run the collector."
- Any sample data must be clearly labeled "Demo/Sample Data" and must be switchable off.
- In ANOVA / Hypothesis testing, never state that H0 is 'proven true'.
"""

import os
import sys
import json
import math
import logging
from datetime import datetime, timezone
from typing import List, Optional, Annotated, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import FileResponse
from pydantic import BaseModel

from database import get_connection
from schemas import (
    SneakerResponse,
    PriceHistoryResponse,
    StatsResponse,
    SneakerAnalyticsResponse,
    OutlierAnalysisResponse,
    PlatformPriceStats,
    CollectorRunResponse,
    CollectorRunRequest,
    DescriptiveStats,
    PriceTrendRegression,
    HealthResponse,
    PaginatedProductsResponse,
    BrandItem,
    BrandsListResponse,
    PriceSnapshotDetail,
    ProductPriceHistoryResponse,
    BrandAnalyticsItem,
    BrandAnalyticsResponse,
    DailyTrendItem,
    PriceTrendsResponse,
    AnovaResponse,
    Hypothesis2TrendResult,
    Hypothesis3RatingResult,
    CorrelationResponse,
    DataQualityMetrics,
    DataQualityResponse,
    RemovedRecordItem,
    PipelineStageItem,
    DashboardResponse,
)
from services.solescout_api import SoleScoutClient
from services.collector import collect, seed_demo_data, clear_demo_data, RAW_DIR
from services.cleaning import run_cleaning_pipeline, CLEANED_DIR, export_raw_data_csv
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
    detect_price_outliers,
    compute_price_trend,
    compare_platforms,
)

logger = logging.getLogger("solescout.routes")
router = APIRouter()

NO_DATA_MESSAGE = "No SoleScout data has been collected yet. Configure the API and run the collector."


def _val(param: Any, default: Any) -> Any:
    """Safe unwrap for FastAPI Annotated Query defaults during direct unit test calls."""
    if hasattr(param, "default"):
        return param.default
    return param if param is not None else default


def _resolve_sneaker(conn, identifier: str) -> Optional[Dict[str, Any]]:
    """Resolve sneaker record by integer primary key ID, product_id, or SKU."""
    if identifier.isdigit():
        row = conn.execute("SELECT * FROM sneakers WHERE id = ?", (int(identifier),)).fetchone()
        if row:
            return dict(row)

    row = conn.execute(
        "SELECT * FROM sneakers WHERE product_id = ? OR sku = ?", (identifier, identifier)
    ).fetchone()
    if row:
        return dict(row)
    return None


# ---------------------------------------------------------------------------
# 1. Health Endpoint
# ---------------------------------------------------------------------------

@router.get("/health", response_model=HealthResponse, tags=["Health"])
def get_health():
    """Verify backend API operational status and SQLite database connectivity."""
    conn = get_connection()
    try:
        conn.execute("SELECT 1").fetchone()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    finally:
        conn.close()

    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        database=db_status,
        version="2.0.0",
        environment="production",
    )


# ---------------------------------------------------------------------------
# 2. Products Catalog & Search (Paginated)
# ---------------------------------------------------------------------------

@router.get("/products", response_model=PaginatedProductsResponse, tags=["Products"])
def get_products(
    page: Annotated[int, Query(ge=1, description="Page number (1-based)")] = 1,
    limit: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    search: Annotated[Optional[str], Query(description="Search keyword across title, brand, SKU")] = None,
    brand: Annotated[Optional[str], Query(description="Filter by canonical brand")] = None,
    sort_by: Annotated[str, Query(description="Sort by id, name, retail_price")] = "id",
    order: Annotated[str, Query(description="Sort order: asc or desc")] = "desc",
    include_demo: Annotated[bool, Query(description="Include clearly marked Demo/Sample Data")] = True,
):
    """
    Retrieve paginated sneaker products catalog with search, brand filtering,
    latest market price enrichment, and demo mode switchability.
    """
    p = max(1, int(_val(page, 1)))
    lim = max(1, min(100, int(_val(limit, 20))))
    s = _val(search, None)
    b = _val(brand, None)
    s_by = _val(sort_by, "id")
    ord_dir = str(_val(order, "desc")).upper()
    inc_demo = bool(_val(include_demo, True))

    if ord_dir not in ["ASC", "DESC"]:
        ord_dir = "DESC"

    conn = get_connection()
    try:
        where_clauses = []
        params = []

        if not inc_demo:
            where_clauses.append("s.is_demo = 0")

        if s:
            pattern = f"%{str(s).strip()}%"
            where_clauses.append("(s.name LIKE ? OR s.sku LIKE ? OR s.product_id LIKE ? OR s.brand LIKE ?)")
            params.extend([pattern, pattern, pattern, pattern])

        if b:
            where_clauses.append("s.brand = ?")
            params.append(str(b).strip())

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        # Count total matching rows
        count_sql = f"SELECT COUNT(*) FROM sneakers s {where_sql}"
        total = conn.execute(count_sql, params).fetchone()[0]
        total_pages = math.ceil(total / lim) if total > 0 else 1

        offset = (p - 1) * lim
        query = f"""
            SELECT
                s.*,
                (
                    SELECT p.price
                    FROM price_history p
                    WHERE p.sneaker_id = s.id
                    ORDER BY p.collection_date DESC, p.id DESC
                    LIMIT 1
                ) AS latest_price,
                (
                    SELECT COUNT(*)
                    FROM price_history p
                    WHERE p.sneaker_id = s.id
                ) AS snapshot_count
            FROM sneakers s
            {where_sql}
            ORDER BY s.id {ord_dir}
            LIMIT ? OFFSET ?
        """
        query_params = list(params) + [lim, offset]
        rows = conn.execute(query, query_params).fetchall()

        items = []
        for r in rows:
            d = dict(r)
            retail = d.get("retail_price")
            latest = d.get("latest_price")
            premium = None
            if retail is not None and retail > 0 and latest is not None and latest > 0:
                premium = round(((latest - retail) / retail) * 100.0, 2)
            d["resale_premium_pct"] = premium
            items.append(SneakerResponse(**d))

        return PaginatedProductsResponse(
            total=total,
            page=p,
            limit=lim,
            total_pages=total_pages,
            items=items,
        )
    finally:
        conn.close()


# Backward compatible alias for /sneakers
@router.get("/sneakers", response_model=List[SneakerResponse], tags=["Sneakers"])
def list_sneakers(
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: Annotated[Optional[str], Query()] = None,
    brand: Annotated[Optional[str], Query()] = None,
    include_demo: Annotated[bool, Query()] = True,
    sort_by: Annotated[str, Query()] = "id",
    order: Annotated[str, Query()] = "desc",
):
    lim = int(_val(limit, 50))
    off = int(_val(offset, 0))
    page = (off // lim) + 1 if lim > 0 else 1
    res = get_products(page=page, limit=lim, search=search, brand=brand, sort_by=sort_by, order=order, include_demo=include_demo)
    return res.items


# ---------------------------------------------------------------------------
# 3. Product Detail by Product ID
# ---------------------------------------------------------------------------

@router.get("/products/{product_id}", response_model=SneakerResponse, tags=["Products"])
def get_product(product_id: str):
    """Retrieve detailed product specifications and latest price snapshot by product_id."""
    conn = get_connection()
    try:
        sneaker = _resolve_sneaker(conn, product_id)
        if not sneaker:
            raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found.")

        sid = sneaker["id"]
        latest_row = conn.execute(
            "SELECT price FROM price_history WHERE sneaker_id = ? ORDER BY collection_date DESC, id DESC LIMIT 1",
            (sid,),
        ).fetchone()
        latest_price = latest_row["price"] if latest_row else None

        count_row = conn.execute(
            "SELECT COUNT(*) FROM price_history WHERE sneaker_id = ?", (sid,)
        ).fetchone()
        snapshot_count = count_row[0] if count_row else 0

        retail = sneaker.get("retail_price")
        premium = None
        if retail and retail > 0 and latest_price:
            premium = round(((latest_price - retail) / retail) * 100.0, 2)

        sneaker["latest_price"] = latest_price
        sneaker["resale_premium_pct"] = premium
        sneaker["snapshot_count"] = snapshot_count

        return SneakerResponse(**sneaker)
    finally:
        conn.close()


# Backward compatible alias for /sneakers/{identifier}
@router.get("/sneakers/{identifier}", response_model=SneakerResponse, tags=["Sneakers"])
def get_sneaker(identifier: str):
    return get_product(identifier)


# ---------------------------------------------------------------------------
# 4. Brands List & Pricing Aggregation
# ---------------------------------------------------------------------------

@router.get("/brands", response_model=BrandsListResponse, tags=["Brands"])
def get_brands(include_demo: Annotated[bool, Query()] = True):
    """Retrieve all tracked sneaker brands with product counts and average pricing."""
    inc_demo = bool(_val(include_demo, True))
    conn = get_connection()
    try:
        where_clause = "" if inc_demo else "WHERE s.is_demo = 0"
        query = f"""
            SELECT
                s.brand,
                COUNT(DISTINCT s.id) AS product_count,
                COUNT(p.id) AS snapshot_count,
                ROUND(AVG(p.price), 2) AS avg_price,
                ROUND(MIN(p.price), 2) AS min_price,
                ROUND(MAX(p.price), 2) AS max_price
            FROM sneakers s
            LEFT JOIN price_history p ON s.id = p.sneaker_id
            {where_clause}
            GROUP BY s.brand
            HAVING s.brand IS NOT NULL
            ORDER BY product_count DESC, avg_price DESC
        """
        rows = conn.execute(query).fetchall()
        brands = [BrandItem(**dict(r)) for r in rows]
        return BrandsListResponse(total_brands=len(brands), brands=brands)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 5. Executive Dashboard Summary
# ---------------------------------------------------------------------------

@router.get("/dashboard", response_model=DashboardResponse, tags=["Dashboard"])
def get_dashboard(include_demo: Annotated[bool, Query()] = True):
    """
    Executive dashboard summary aggregating macro metrics, price distribution bins,
    brand comparisons, and temporal price trend charts.
    """
    inc_demo = bool(_val(include_demo, True))
    conn = get_connection()
    try:
        where_s = "" if inc_demo else "WHERE is_demo = 0"
        total_products = conn.execute(f"SELECT COUNT(*) FROM sneakers {where_s}").fetchone()[0]

        brand_sql = (
            f"SELECT COUNT(DISTINCT brand) FROM sneakers WHERE is_demo = 0 AND brand IS NOT NULL"
            if not inc_demo
            else "SELECT COUNT(DISTINCT brand) FROM sneakers WHERE brand IS NOT NULL"
        )
        unique_brands = conn.execute(brand_sql).fetchone()[0]

        where_p = "" if inc_demo else "WHERE is_demo = 0"
        total_snapshots = conn.execute(f"SELECT COUNT(*) FROM price_history {where_p}").fetchone()[0]
        dates = conn.execute(
            f"SELECT MIN(collection_date), MAX(collection_date) FROM price_history {where_p}"
        ).fetchone()
        start_date = dates[0] if dates and dates[0] else None
        end_date = dates[1] if dates and dates[1] else None

        df = load_cleaned_data(include_demo=inc_demo)
        prices = df["price"].dropna().tolist() if not df.empty and "price" in df.columns else []
        desc = compute_descriptive_stats(prices)
        chart_data = get_chart_ready_data(df)

        is_empty = (total_products == 0)
        demo_count = conn.execute("SELECT COUNT(*) FROM sneakers WHERE is_demo = 1").fetchone()[0]
        demo_active = bool(demo_count > 0 and inc_demo)

        if is_empty:
            message = NO_DATA_MESSAGE
        elif demo_active and total_products == demo_count:
            message = f"Displaying Demo/Sample Data ({demo_count} sample products, switchable off)."
        else:
            message = f"SoleScout Intelligence active with {total_products} products and {total_snapshots} snapshots."

        return DashboardResponse(
            total_products=total_products,
            total_snapshots=total_snapshots,
            unique_brands=unique_brands,
            date_range_start=start_date,
            date_range_end=end_date,
            is_empty=is_empty,
            demo_mode_active=demo_active,
            descriptive_summary=DescriptiveStats(**desc),
            price_distribution=chart_data.get("price_distribution", []),
            brand_comparison=chart_data.get("brand_comparison", []),
            price_trends=chart_data.get("price_trends", []),
            message=message,
        )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 6. Price History for a Specific Product
# ---------------------------------------------------------------------------

@router.get("/price-history/{product_id}", response_model=ProductPriceHistoryResponse, tags=["Price History"])
def get_price_history(product_id: str, include_demo: Annotated[bool, Query()] = True):
    """Retrieve full chronological price snapshot time-series for a specific sneaker product."""
    inc_demo = bool(_val(include_demo, True))
    conn = get_connection()
    try:
        sneaker = _resolve_sneaker(conn, product_id)
        if not sneaker:
            raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found.")

        sid = sneaker["id"]
        sql = "SELECT * FROM price_history WHERE sneaker_id = ?"
        params = [sid]
        if not inc_demo:
            sql += " AND is_demo = 0"
        sql += " ORDER BY collection_date ASC, id ASC"

        rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
        latest_price = rows[-1]["price"] if rows else None

        snapshots = [
            PriceSnapshotDetail(
                id=r["id"],
                product_id=sneaker["product_id"],
                platform=r["platform"],
                price=r["price"],
                collection_date=r["collection_date"],
                size=r.get("size"),
                condition=r.get("condition") or "new",
                seller=r.get("seller"),
                rating=r.get("rating"),
                is_demo=r.get("is_demo", 0),
            )
            for r in rows
        ]

        return ProductPriceHistoryResponse(
            product_id=sneaker["product_id"],
            sku=sneaker["sku"],
            name=sneaker["name"],
            brand=sneaker.get("brand"),
            retail_price=sneaker.get("retail_price"),
            latest_price=latest_price,
            total_snapshots=len(snapshots),
            snapshots=snapshots,
        )
    finally:
        conn.close()


# Backward compatible alias for /sneakers/{identifier}/prices
@router.get("/sneakers/{identifier}/prices", response_model=List[PriceHistoryResponse], tags=["Sneakers"])
def get_sneaker_prices(identifier: str, include_demo: Annotated[bool, Query()] = True):
    res = get_price_history(identifier, include_demo=include_demo)
    return [
        PriceHistoryResponse(
            id=s.id,
            sneaker_id=0,
            product_id=s.product_id,
            platform=s.platform,
            price=s.price,
            collection_date=s.collection_date,
            size=s.size,
            condition=s.condition or "new",
            seller=s.seller,
            rating=s.rating,
            is_demo=s.is_demo,
            recorded_at=None,
        )
        for s in res.snapshots
    ]


# ---------------------------------------------------------------------------
# 7. Brand-Wise Price Analytics
# ---------------------------------------------------------------------------

@router.get("/analytics/brands", response_model=BrandAnalyticsResponse, tags=["Analytics"])
def get_analytics_brands(include_demo: Annotated[bool, Query()] = True):
    """Retrieve brand-wise descriptive statistics (mean, median, IQR, std dev, range)."""
    inc_demo = bool(_val(include_demo, True))
    df = load_cleaned_data(include_demo=inc_demo)
    brands = analyze_brand_prices(df)
    items = [
        BrandAnalyticsItem(
            brand=b["brand"],
            count=b["count"],
            mean_price=b["mean_price"],
            median_price=b["median_price"],
            min_price=b["min_price"],
            max_price=b["max_price"],
            std_dev=b["std_dev"],
            iqr=b["iqr"],
        )
        for b in brands
    ]
    return BrandAnalyticsResponse(total_brands_analyzed=len(items), brands=items)


# ---------------------------------------------------------------------------
# 8. Longitudinal Price Trends
# ---------------------------------------------------------------------------

@router.get("/analytics/price-trends", response_model=PriceTrendsResponse, tags=["Analytics"])
def get_analytics_price_trends(include_demo: Annotated[bool, Query()] = True):
    """
    Retrieve longitudinal price trends over collection dates with
    SciPy OLS linear regression slope, R², and trend direction.
    """
    inc_demo = bool(_val(include_demo, True))
    df = load_cleaned_data(include_demo=inc_demo)
    trends = analyze_price_trends_over_time(df)
    daily_items = [
        DailyTrendItem(
            date=d["date"],
            count=d["count"],
            mean_price=d["mean_price"],
            median_price=d["median_price"],
            min_price=d["min_price"],
            max_price=d["max_price"],
            std_dev=d["std_dev"],
        )
        for d in trends.get("daily_trends", [])
    ]
    reg = trends.get("regression")
    reg_model = PriceTrendRegression(**reg) if reg else None
    return PriceTrendsResponse(
        daily_trends=daily_items,
        regression=reg_model,
        direction=trends.get("direction", "stable"),
    )


# ---------------------------------------------------------------------------
# 9. Hypothesis Testing 1 — Brand vs. Price (One-Way ANOVA)
# ---------------------------------------------------------------------------

@router.get("/statistics/anova", response_model=AnovaResponse, tags=["Statistics"])
def get_statistics_anova(
    alpha: Annotated[float, Query(ge=0.001, le=0.5, description="Significance level")] = 0.05,
    include_demo: Annotated[bool, Query(description="Include Demo/Sample Data")] = True,
):
    """
    FDS Hypothesis 1: One-Way ANOVA across brand mean sneaker prices.
    H0: No statistically significant difference in mean prices among brands.
    H1: At least one brand has a statistically significantly different mean price.
    """
    a = float(_val(alpha, 0.05))
    inc_demo = bool(_val(include_demo, True))
    df = load_cleaned_data(include_demo=inc_demo)
    res = test_hypothesis_1_brand_vs_price(df, alpha=a)
    return AnovaResponse(**res)


# ---------------------------------------------------------------------------
# 10. Hypothesis Testing 2 & 3 — Price Trend & Rating Correlation
# ---------------------------------------------------------------------------

@router.get("/statistics/correlation", response_model=CorrelationResponse, tags=["Statistics"])
def get_statistics_correlation(
    alpha: Annotated[float, Query(ge=0.001, le=0.5, description="Significance level")] = 0.05,
    include_demo: Annotated[bool, Query(description="Include Demo/Sample Data")] = True,
):
    """
    FDS Hypothesis 2 (Price vs. Date Regression & Correlation) and
    Hypothesis 3 (Price vs. Rating). Adheres strictly to the rule:
    returns 'Insufficient reliable rating data.' without inventing ratings.
    """
    a = float(_val(alpha, 0.05))
    inc_demo = bool(_val(include_demo, True))
    df = load_cleaned_data(include_demo=inc_demo)
    trend_res = test_hypothesis_2_price_trend(df, alpha=a)
    rating_res = test_hypothesis_3_price_vs_rating(df, alpha=a)
    dist = compute_price_distribution(df, num_bins=8)
    brand_comp = analyze_brand_prices(df)

    return CorrelationResponse(
        price_trend_hypothesis=Hypothesis2TrendResult(**trend_res),
        price_rating_hypothesis=Hypothesis3RatingResult(**rating_res),
        price_distribution=dist,
        brand_comparison=brand_comp,
    )


# ---------------------------------------------------------------------------
# 11. Data Cleaning & Quality Assurance Report
# ---------------------------------------------------------------------------

@router.get("/data-quality", response_model=DataQualityResponse, tags=["Data Quality"])
def get_data_quality():
    """Retrieve the latest Stage 4 data cleaning and quality audit report."""
    report_path = os.path.join(CLEANED_DIR, "data_quality_report_latest.json")

    # Gather pipeline context
    raw_file_count = len([f for f in os.listdir(RAW_DIR) if f.endswith(".json")]) if os.path.exists(RAW_DIR) else 0
    raw_csv_path = os.path.join(RAW_DIR, "sneakers_raw_latest.csv")
    cleaned_csv_path = os.path.join(CLEANED_DIR, "sneakers_cleaned_latest.csv")
    raw_csv_available = os.path.exists(raw_csv_path)
    cleaned_csv_available = os.path.exists(cleaned_csv_path)

    # Count SQLite snapshots for pipeline detail
    try:
        conn = get_connection()
        total_snapshots = conn.execute("SELECT COUNT(*) FROM price_history").fetchone()[0]
        conn.close()
    except Exception:
        total_snapshots = 0

    def _build_pipeline_stages(raw_files: int, snapshots: int) -> list:
        return [
            PipelineStageItem(
                stage_number=1, name="SoleScout API", icon="🌐",
                description="Live sneaker market data via SoleScout REST API. Returns JSON with product SKUs, prices, retail prices, condition, and URLs.",
                input_type="HTTP Request", output_type="JSON Response", status="Active",
            ),
            PipelineStageItem(
                stage_number=2, name="Raw Data Storage", icon="📦",
                description="Raw API responses saved to data/raw/ as timestamped JSON files. No API credentials stored in files.",
                input_type="JSON Response", output_type="JSON Files", status="Active",
                details=f"{raw_files} raw file(s) on disk",
            ),
            PipelineStageItem(
                stage_number=3, name="Validation", icon="🔍",
                description="Validates product IDs, product names, prices (must be positive numeric), and timestamps (ISO 8601 format). Rejects records failing validation.",
                input_type="JSON Records", output_type="Valid / Rejected Records", status="Active",
            ),
            PipelineStageItem(
                stage_number=4, name="Cleaning Pipeline", icon="🧹",
                description="Standardizes brand names, deduplicates on UNIQUE(product_id, collection_date), converts price fields to float, and flags statistical outliers (Tukey IQR) without removing them.",
                input_type="Valid Records", output_type="Clean DataFrame", status="Active",
            ),
            PipelineStageItem(
                stage_number=5, name="Clean Data Export", icon="📊",
                description="Cleaned records exported to data/cleaned/ as CSV. Data Quality Report generated as JSON. Missing fields stored as NULL — never imputed.",
                input_type="Clean DataFrame", output_type="CSV + JSON Report", status="Active",
            ),
            PipelineStageItem(
                stage_number=6, name="SQLite Database", icon="🗄️",
                description="Cleaned records ingested into solescout.db with UNIQUE(product_id, collection_date) constraint preventing duplicate historical snapshots.",
                input_type="Clean DataFrame", output_type="SQLite Rows", status="Active",
                details=f"{snapshots} snapshot(s) stored",
            ),
            PipelineStageItem(
                stage_number=7, name="Analysis & API", icon="📈",
                description="Pandas / NumPy / SciPy analytics + FastAPI serving statistical results to React frontend. No direct SQLite access from the frontend.",
                input_type="SQLite Data", output_type="JSON API Responses", status="Active",
            ),
        ]

    pipeline_stages = _build_pipeline_stages(raw_file_count, total_snapshots)

    if os.path.exists(report_path):
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            quality_errors = data.get("quality_errors", {})
            invalid_prices = quality_errors.get("invalid_prices", data.get("invalid_prices", 0))
            invalid_timestamps = quality_errors.get("invalid_timestamps", data.get("invalid_timestamps", 0))

            # Parse removed records from the quality report (added in cleaning.py v2.0)
            raw_removed = data.get("removed_records", [])
            removed_records = []
            for rr in raw_removed:
                try:
                    removed_records.append(RemovedRecordItem(
                        raw_index=rr.get("raw_index"),
                        product_id=str(rr.get("product_id")) if rr.get("product_id") is not None else None,
                        product_name=str(rr.get("product_name")) if rr.get("product_name") is not None else None,
                        raw_price=rr.get("raw_price"),
                        reasons=str(rr.get("reasons", "Unknown")),
                        category=str(rr.get("category", "Data Quality Error")),
                    ))
                except Exception as parse_err:
                    logger.warning("Skipping malformed removed_record entry: %s", parse_err)

            report_date = (
                data.get("reproducibility", {}).get("timestamp")
                or data.get("timestamp")
                or data.get("report_generated_at")
            )

            return DataQualityResponse(
                status="success",
                report_date=report_date,
                summary="SoleScout Stage 4 Data Cleaning & Quality Assurance Report",
                metrics=DataQualityMetrics(
                    raw_records=data.get("raw_records", 0),
                    clean_records=data.get("clean_records", 0),
                    duplicate_records=data.get("duplicate_records", 0),
                    missing_values=data.get("missing_values", {}),
                    invalid_prices=invalid_prices,
                    invalid_timestamps=invalid_timestamps,
                    records_removed=data.get("records_removed", 0),
                    cleaning_percentage=data.get("cleaning_percentage", 100.0),
                ),
                removed_records=removed_records,
                pipeline_stages=pipeline_stages,
                raw_csv_available=raw_csv_available,
                cleaned_csv_available=cleaned_csv_available,
            )
        except Exception as e:
            logger.warning("Could not parse quality report JSON (%s): %s", report_path, e)

    # Fallback: derive from SQLite
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM price_history").fetchone()[0]
        return DataQualityResponse(
            status="info",
            report_date=datetime.now(timezone.utc).isoformat(),
            summary="Cleaned SQLite baseline data metrics — run the cleaning pipeline for a full report.",
            metrics=DataQualityMetrics(
                raw_records=total,
                clean_records=total,
                duplicate_records=0,
                missing_values={},
                invalid_prices=0,
                invalid_timestamps=0,
                records_removed=0,
                cleaning_percentage=100.0,
            ),
            removed_records=[],
            pipeline_stages=pipeline_stages,
            raw_csv_available=raw_csv_available,
            cleaned_csv_available=cleaned_csv_available,
        )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 11b. Data Export Download Endpoints
# ---------------------------------------------------------------------------

@router.get("/download/raw-csv", tags=["Data Quality"])
def download_raw_csv():
    """
    Download the raw (pre-cleaning) sneaker data as CSV.
    Never exposes API credentials — the export function explicitly strips them.
    """
    # Re-export to guarantee a fresh CSV exists (no-op if already up to date)
    try:
        path = export_raw_data_csv(output_dir=RAW_DIR)
    except Exception as e:
        logger.warning("export_raw_data_csv failed: %s", e)
        path = None

    if not path or not os.path.exists(path):
        raise HTTPException(
            status_code=404,
            detail="Raw CSV not yet generated. Run the collector first, then call /api/collector/run.",
        )
    return FileResponse(path, media_type="text/csv", filename="solescout_raw_data.csv")


@router.get("/download/cleaned-csv", tags=["Data Quality"])
def download_cleaned_csv():
    """Download the cleaned sneaker dataset as CSV."""
    path = os.path.join(CLEANED_DIR, "sneakers_cleaned_latest.csv")
    if not os.path.exists(path):
        raise HTTPException(
            status_code=404,
            detail="Cleaned CSV not found. Run the cleaning pipeline first: POST /api/collector/run.",
        )
    return FileResponse(path, media_type="text/csv", filename="solescout_cleaned_data.csv")


# ---------------------------------------------------------------------------
# 12. Collector Pipeline Execution
# ---------------------------------------------------------------------------

@router.post("/collector/run", response_model=CollectorRunResponse, tags=["Collector"])
def run_collector(req: CollectorRunRequest = CollectorRunRequest()):
    """
    Trigger the Python sneaker data collector and automatic data cleaning pipeline.
    Never exposes API credentials. If unconfigured, provides actionable guidance.
    """
    if req.demo:
        seed_res = seed_demo_data()
        total_demo = seed_res.get("demo_snapshots_loaded", 0) + seed_res.get("duplicates_ignored", 0)
        return CollectorRunResponse(
            status="success",
            message="Populated clearly marked Demo/Sample Data (is_demo=1).",
            query_used="[DEMO_SEED]",
            records_collected=total_demo,
            records_cleaned=total_demo,
            snapshots_inserted=seed_res.get("demo_snapshots_loaded", 0),
            snapshots_ignored_duplicates=seed_res.get("duplicates_ignored", 0),
        )

    client = SoleScoutClient()
    if not client.is_configured():
        return CollectorRunResponse(
            status="unconfigured",
            message=NO_DATA_MESSAGE,
            query_used=req.queries,
            records_collected=0,
            records_cleaned=0,
            snapshots_inserted=0,
            snapshots_ignored_duplicates=0,
        )

    queries_list = [q.strip() for q in (req.queries or "Jordan").split(",") if q.strip()]
    total_raw = 0
    latest_raw_file = None

    for q in queries_list:
        collect_res = collect(query=q, limit=req.limit or 5, pages=req.pages or 1)
        if collect_res.get("status") == "success":
            total_raw += collect_res.get("records_collected", 0)
            latest_raw_file = collect_res.get("raw_file")

    clean_res = run_cleaning_pipeline(raw_file=latest_raw_file)
    ingest = clean_res.get("ingest_result", {})

    return CollectorRunResponse(
        status="success",
        message=f"Collection and cleaning completed for '{req.queries}'.",
        query_used=req.queries,
        raw_file=latest_raw_file,
        cleaned_file=clean_res.get("sneakers_csv"),
        records_collected=total_raw,
        records_cleaned=clean_res.get("sneakers_cleaned", 0),
        snapshots_inserted=ingest.get("snapshots_inserted", 0),
        snapshots_ignored_duplicates=ingest.get("snapshots_ignored", 0),
    )


# Backward-compatibility alias
class CollectRequest(BaseModel):
    query: Optional[str] = "Jordan 1"
    limit: int = 10


def trigger_collection(req: CollectRequest = CollectRequest()):
    return run_collector(CollectorRunRequest(queries=req.query, limit=req.limit))


# ---------------------------------------------------------------------------
# Additional Helper / Diagnostic Endpoints
# ---------------------------------------------------------------------------

@router.get("/stats", response_model=StatsResponse, tags=["Stats"])
def get_stats(include_demo: Annotated[bool, Query()] = True):
    """Return database stats and collector readiness."""
    inc_demo = bool(_val(include_demo, True))
    conn = get_connection()
    try:
        real_sneakers = conn.execute("SELECT COUNT(*) FROM sneakers WHERE is_demo = 0").fetchone()[0]
        demo_sneakers = conn.execute("SELECT COUNT(*) FROM sneakers WHERE is_demo = 1").fetchone()[0]
        total_sneakers = real_sneakers + (demo_sneakers if inc_demo else 0)

        price_query = "SELECT COUNT(*) FROM price_history"
        if not inc_demo:
            price_query += " WHERE is_demo = 0"
        total_price_records = conn.execute(price_query).fetchone()[0]

        date_query = "SELECT MIN(collection_date), MAX(collection_date) FROM price_history"
        if not inc_demo:
            date_query += " WHERE is_demo = 0"
        dates = conn.execute(date_query).fetchone()
        start_date = dates[0] if dates and dates[0] else None
        end_date = dates[1] if dates and dates[1] else None

        is_empty = (total_sneakers == 0)
        has_real_data = (real_sneakers > 0)

        if not has_real_data and not inc_demo:
            message = NO_DATA_MESSAGE
        elif not has_real_data and demo_sneakers > 0 and inc_demo:
            message = f"Displaying Demo/Sample Data ({demo_sneakers} sample sneakers, switchable off)."
        elif has_real_data:
            message = f"SoleScout intelligence database active: {real_sneakers} live sneakers tracked."
        else:
            message = NO_DATA_MESSAGE

        return StatsResponse(
            total_sneakers=total_sneakers,
            total_price_records=total_price_records,
            real_sneakers=real_sneakers,
            demo_sneakers=demo_sneakers,
            date_range_start=start_date,
            date_range_end=end_date,
            is_empty=is_empty,
            demo_mode_active=bool(demo_sneakers > 0 and inc_demo),
            message=message,
        )
    finally:
        conn.close()


@router.get("/sneakers/{identifier}/analytics", response_model=SneakerAnalyticsResponse, tags=["Analytics"])
def get_sneaker_analytics(
    identifier: str,
    z_threshold: Annotated[float, Query(ge=1.0, le=5.0)] = 2.5,
    include_demo: Annotated[bool, Query()] = True,
):
    z_th = float(_val(z_threshold, 2.5))
    inc_demo = bool(_val(include_demo, True))
    conn = get_connection()
    try:
        sneaker = _resolve_sneaker(conn, identifier)
        if not sneaker:
            raise HTTPException(status_code=404, detail=f"Sneaker '{identifier}' not found.")

        sid = sneaker["id"]
        sql = "SELECT * FROM price_history WHERE sneaker_id = ?"
        params = [sid]
        if not inc_demo:
            sql += " AND is_demo = 0"
        sql += " ORDER BY collection_date ASC"

        price_rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
        prices_list = [r["price"] for r in price_rows]

        retail = sneaker.get("retail_price")
        latest_price = price_rows[-1]["price"] if price_rows else None
        premium = None
        if retail and retail > 0 and latest_price:
            premium = round(((latest_price - retail) / retail) * 100.0, 2)

        desc_stats = compute_descriptive_stats(prices_list, retail_price=retail)
        trend = compute_price_trend(price_rows)
        outliers = detect_price_outliers(price_rows, z_threshold=z_th)
        platforms = compare_platforms(price_rows)

        return SneakerAnalyticsResponse(
            product_id=sneaker["product_id"],
            sku=sneaker["sku"],
            name=sneaker["name"],
            brand=sneaker.get("brand"),
            retail_price=retail,
            latest_price=latest_price,
            resale_premium_pct=premium,
            is_demo=sneaker.get("is_demo", 0),
            descriptive_stats=DescriptiveStats(**desc_stats),
            trend=PriceTrendRegression(**trend),
            outliers=OutlierAnalysisResponse(**outliers),
            platform_comparison=[PlatformPriceStats(**p) for p in platforms],
        )
    finally:
        conn.close()


@router.get("/sneakers/{identifier}/outliers", response_model=OutlierAnalysisResponse, tags=["Analytics"])
def get_sneaker_outliers(
    identifier: str,
    z_threshold: Annotated[float, Query(ge=1.0, le=5.0)] = 2.5,
    include_demo: Annotated[bool, Query()] = True,
):
    z_th = float(_val(z_threshold, 2.5))
    inc_demo = bool(_val(include_demo, True))
    conn = get_connection()
    try:
        sneaker = _resolve_sneaker(conn, identifier)
        if not sneaker:
            raise HTTPException(status_code=404, detail=f"Sneaker '{identifier}' not found.")

        sid = sneaker["id"]
        sql = "SELECT * FROM price_history WHERE sneaker_id = ?"
        params = [sid]
        if not inc_demo:
            sql += " AND is_demo = 0"
        sql += " ORDER BY collection_date ASC"

        rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
        outliers = detect_price_outliers(rows, z_threshold=z_th)
        return OutlierAnalysisResponse(**outliers)
    finally:
        conn.close()


@router.get("/analytics/platforms", response_model=List[PlatformPriceStats], tags=["Analytics"])
def get_global_platform_comparison(include_demo: Annotated[bool, Query()] = True):
    inc_demo = bool(_val(include_demo, True))
    conn = get_connection()
    try:
        sql = "SELECT platform, price FROM price_history"
        if not inc_demo:
            sql += " WHERE is_demo = 0"
        rows = [dict(r) for r in conn.execute(sql).fetchall()]
        platforms = compare_platforms(rows)
        return [PlatformPriceStats(**p) for p in platforms]
    finally:
        conn.close()


@router.get("/collector/status", tags=["Collector"])
def get_collector_status():
    client = SoleScoutClient()
    configured = client.is_configured()
    raw_files = []
    if os.path.exists(RAW_DIR):
        raw_files = [f for f in os.listdir(RAW_DIR) if f.endswith(".json")]

    return {
        "api_key_configured": configured,
        "base_url": client.base_url,
        "total_raw_files": len(raw_files),
        "guidance": None if configured else "Configure SOLESCOUT_API_KEY in backend .env to collect real data.",
    }


@router.post("/demo/seed", tags=["Demo"])
def seed_demo():
    return seed_demo_data()


@router.post("/demo/clear", tags=["Demo"])
def clear_demo():
    deleted = clear_demo_data()
    return {
        "status": "success",
        "message": f"Cleared {deleted} sample sneaker records and their snapshots.",
    }
