"""
SoleScout FDS - Pydantic Schemas

Rigorous request/response models with field validation and data integrity controls.
Follows non-negotiable rules:
- Never invent data.
- Missing fields are stored as None / null.
- Enforces types and clear labeling of Demo/Sample Data.
"""

from typing import List, Optional, Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Sneaker Models
# ---------------------------------------------------------------------------

class SneakerBase(BaseModel):
    product_id: str = Field(..., description="Unique product identifier / style code")
    sku: str = Field(..., description="Stock Keeping Unit")
    name: str = Field(..., description="Product official title / name")
    brand: Optional[str] = Field(None, description="Sneaker brand (e.g. Nike, Jordan, adidas)")
    colorway: Optional[str] = Field(None, description="Colorway description")
    retail_price: Optional[float] = Field(None, ge=0, description="MSRP / Retail price")
    release_date: Optional[str] = Field(None, description="Release date in YYYY-MM-DD format")
    image_url: Optional[str] = Field(None, description="Product image link")
    is_demo: int = Field(0, description="1 if sample demo data, 0 if collected SoleScout data")


class SneakerCreate(SneakerBase):
    pass


class SneakerResponse(SneakerBase):
    id: int
    latest_price: Optional[float] = None
    resale_premium_pct: Optional[float] = None
    snapshot_count: Optional[int] = 0
    fetched_at: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Price History & Snapshot Models
# ---------------------------------------------------------------------------

class PriceHistoryBase(BaseModel):
    product_id: str
    platform: str
    price: float = Field(..., ge=0, description="Snapshot price value")
    collection_date: str = Field(..., description="Snapshot date (YYYY-MM-DD)")
    size: Optional[str] = None
    condition: str = "new"
    seller: Optional[str] = None
    rating: Optional[float] = None
    is_demo: int = 0


class PriceHistoryCreate(PriceHistoryBase):
    sneaker_id: int


class PriceHistoryResponse(PriceHistoryBase):
    id: int
    sneaker_id: int
    recorded_at: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Statistical & Analytics Models
# ---------------------------------------------------------------------------

class DescriptiveStats(BaseModel):
    count: int = 0
    mean: Optional[float] = None
    median: Optional[float] = None
    mode: Optional[float] = None
    std_dev: Optional[float] = None
    variance: Optional[float] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    q1: Optional[float] = None
    q3: Optional[float] = None
    iqr: Optional[float] = None
    volatility_cv: Optional[float] = None
    resale_premium_pct: Optional[float] = None


class OutlierRecord(BaseModel):
    id: Optional[int] = None
    collection_date: str
    platform: str
    price: float
    method: str  # "IQR", "Z-score", or "Both"
    reason: str
    z_score: Optional[float] = None
    is_outlier: bool = True


class OutlierAnalysisResponse(BaseModel):
    total_records: int = 0
    outliers_count: int = 0
    iqr_lower_bound: Optional[float] = None
    iqr_upper_bound: Optional[float] = None
    z_threshold: float = 2.5
    outliers: List[OutlierRecord] = []


class PriceTrendRegression(BaseModel):
    slope: Optional[float] = None
    intercept: Optional[float] = None
    r_value: Optional[float] = None
    r_squared: Optional[float] = None
    p_value: Optional[float] = None
    std_err: Optional[float] = None
    direction: str = "insufficient_data"  # appreciating, depreciating, stable, insufficient_data
    data_points: int = 0


class PlatformPriceStats(BaseModel):
    platform: str
    listing_count: int = 0
    mean_price: Optional[float] = None
    median_price: Optional[float] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None


class SneakerAnalyticsResponse(BaseModel):
    product_id: str
    sku: str
    name: str
    brand: Optional[str] = None
    retail_price: Optional[float] = None
    latest_price: Optional[float] = None
    resale_premium_pct: Optional[float] = None
    is_demo: int = 0
    descriptive_stats: DescriptiveStats
    trend: PriceTrendRegression
    outliers: OutlierAnalysisResponse
    platform_comparison: List[PlatformPriceStats]


# ---------------------------------------------------------------------------
# Collector & System Stats Models
# ---------------------------------------------------------------------------

class StatsResponse(BaseModel):
    total_sneakers: int
    total_price_records: int
    real_sneakers: int
    demo_sneakers: int
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None
    is_empty: bool
    demo_mode_active: bool
    message: str


class CollectorRunResponse(BaseModel):
    status: str
    message: str
    query_used: Optional[str] = None
    raw_file: Optional[str] = None
    cleaned_file: Optional[str] = None
    records_collected: int = 0
    records_cleaned: int = 0
    snapshots_inserted: int = 0
    snapshots_ignored_duplicates: int = 0


# ---------------------------------------------------------------------------
# Stage 6 API Models
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    database: str
    version: str
    environment: str = "production"


class PaginatedProductsResponse(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int
    items: List[SneakerResponse]


class BrandItem(BaseModel):
    brand: str
    product_count: int
    snapshot_count: int = 0
    avg_price: Optional[float] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None


class BrandsListResponse(BaseModel):
    total_brands: int
    brands: List[BrandItem]


class PriceSnapshotDetail(BaseModel):
    id: int
    product_id: str
    platform: str
    price: float
    collection_date: str
    size: Optional[str] = None
    condition: Optional[str] = "new"
    seller: Optional[str] = None
    rating: Optional[float] = None
    is_demo: int = 0


class ProductPriceHistoryResponse(BaseModel):
    product_id: str
    sku: str
    name: str
    brand: Optional[str] = None
    retail_price: Optional[float] = None
    latest_price: Optional[float] = None
    total_snapshots: int
    snapshots: List[PriceSnapshotDetail]


class BrandAnalyticsItem(BaseModel):
    brand: str
    count: int
    mean_price: Optional[float] = None
    median_price: Optional[float] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    std_dev: Optional[float] = None
    iqr: Optional[float] = None


class BrandAnalyticsResponse(BaseModel):
    total_brands_analyzed: int
    brands: List[BrandAnalyticsItem]


class DailyTrendItem(BaseModel):
    date: str
    count: int
    mean_price: float
    median_price: float
    min_price: float
    max_price: float
    std_dev: float


class PriceTrendsResponse(BaseModel):
    daily_trends: List[DailyTrendItem]
    regression: Optional[PriceTrendRegression] = None
    direction: str


class AnovaResponse(BaseModel):
    hypothesis: str
    test_type: str
    null_hypothesis: str
    alternative_hypothesis: str
    alpha: float
    f_statistic: Optional[float] = None
    test_statistic: Optional[float] = None
    p_value: Optional[float] = None
    decision: str
    interpretation: str
    engineering_explanation: Optional[str] = None
    brands_evaluated: List[str] = []
    brand_sample_sizes: dict = {}
    brand_means: dict = {}
    brand_boxplots: List[dict] = []


class Hypothesis2TrendResult(BaseModel):
    hypothesis: str
    test_type: str
    null_hypothesis: str
    alternative_hypothesis: str
    alpha: float
    test_statistic: Optional[float] = None
    coefficient: Optional[float] = None
    pearson_r: Optional[float] = None
    r_squared: Optional[float] = None
    p_value: Optional[float] = None
    trend_information: Optional[str] = None
    decision: str
    interpretation: str
    engineering_explanation: Optional[str] = None
    sample_size: int = 0
    scatter_points: List[dict] = []


class Hypothesis3RatingResult(BaseModel):
    hypothesis: str
    test_type: str = "Pearson Product-Moment Correlation"
    null_hypothesis: str = "There is no linear correlation between sneaker price and product rating (rho = 0)."
    alternative_hypothesis: str = "There is a statistically significant linear correlation between sneaker price and product rating (rho != 0)."
    alpha: float = 0.05
    status: str
    message: str
    test_statistic: Optional[float] = None
    correlation: Optional[float] = None
    p_value: Optional[float] = None
    decision: str
    interpretation: str
    engineering_explanation: Optional[str] = None


class CorrelationResponse(BaseModel):
    price_trend_hypothesis: Hypothesis2TrendResult
    price_rating_hypothesis: Hypothesis3RatingResult
    price_distribution: Optional[dict] = None
    brand_comparison: Optional[List[dict]] = None


class RemovedRecordItem(BaseModel):
    raw_index: Optional[int] = None
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    raw_price: Optional[Any] = None
    reasons: str
    category: Optional[str] = "Data Quality Error"


class PipelineStageItem(BaseModel):
    stage_number: int
    name: str
    icon: str
    description: str
    input_type: str
    output_type: str
    status: str = "Active"
    details: Optional[str] = None


class DataQualityMetrics(BaseModel):
    raw_records: int
    clean_records: int
    duplicate_records: int
    missing_values: dict = {}
    invalid_prices: int = 0
    invalid_timestamps: int = 0
    records_removed: int = 0
    cleaning_percentage: float = 100.0


class DataQualityResponse(BaseModel):
    status: str
    report_date: Optional[str] = None
    summary: str
    metrics: DataQualityMetrics
    removed_records: List[RemovedRecordItem] = []
    pipeline_stages: List[PipelineStageItem] = []
    raw_csv_available: bool = True
    cleaned_csv_available: bool = True


class DashboardResponse(BaseModel):
    total_products: int
    total_snapshots: int
    unique_brands: int
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None
    is_empty: bool
    demo_mode_active: bool
    descriptive_summary: DescriptiveStats
    price_distribution: List[dict] = []
    brand_comparison: List[dict] = []
    price_trends: List[dict] = []
    message: str


class CollectorRunRequest(BaseModel):
    queries: Optional[str] = "Jordan,Nike,Adidas"
    pages: Optional[int] = Field(1, ge=1, le=5)
    limit: Optional[int] = Field(5, ge=1, le=25)
    demo: Optional[bool] = False
