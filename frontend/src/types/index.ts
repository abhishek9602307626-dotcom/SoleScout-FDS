/**
 * SoleScout Sneaker Price Intelligence & Analytics
 * TypeScript Definitions for Frontend Components & API Payloads
 */

export interface SneakerProduct {
  id: number;
  product_id: string;
  sku: string;
  name: string;
  brand: string | null;
  colorway: string | null;
  retail_price: number | null;
  latest_price: number | null;
  resale_premium_pct: number | null;
  release_date: string | null;
  image_url: string | null;
  snapshot_count: number;
  is_demo: number;
  fetched_at?: string;
}

export interface PaginatedProducts {
  total: number;
  page: number;
  limit: number;
  total_pages: number;
  items: SneakerProduct[];
}

export interface PriceSnapshot {
  id: number;
  product_id: string;
  platform: string;
  price: number;
  collection_date: string;
  size: string | null;
  condition: string;
  seller: string | null;
  rating: number | null;
  is_demo: number;
}

export interface ProductPriceHistory {
  product_id: string;
  sku: string;
  name: string;
  brand: string | null;
  retail_price: number | null;
  latest_price: number | null;
  total_snapshots: number;
  snapshots: PriceSnapshot[];
}

export interface BrandItem {
  brand: string;
  product_count: number;
  snapshot_count: number;
  avg_price: number | null;
  min_price: number | null;
  max_price: number | null;
}

export interface BrandsListResponse {
  total_brands: number;
  brands: BrandItem[];
}

export interface DescriptiveStats {
  count: number;
  mean: number | null;
  median: number | null;
  mode: number | null;
  std_dev: number | null;
  variance: number | null;
  min_price: number | null;
  max_price: number | null;
  q1: number | null;
  q3: number | null;
  iqr: number | null;
  volatility_cv: number | null;
  resale_premium_pct: number | null;
}

export interface PriceDistributionBin {
  range: string;
  count: number;
  pct: number;
}

export interface BrandComparisonItem {
  brand: string;
  mean_price: number;
  median_price: number;
  min_price: number;
  max_price: number;
  count: number;
}

export interface PriceTrendItem {
  date: string;
  avg_price: number;
  median_price: number;
  volume: number;
}

export interface DashboardData {
  total_products: number;
  total_snapshots: number;
  unique_brands: number;
  date_range_start: string | null;
  date_range_end: string | null;
  is_empty: boolean;
  demo_mode_active: boolean;
  descriptive_summary: DescriptiveStats;
  price_distribution: PriceDistributionBin[];
  brand_comparison: BrandComparisonItem[];
  price_trends: PriceTrendItem[];
  message: string;
}

export interface BrandAnalyticsItem {
  brand: string;
  count: number;
  mean_price: number | null;
  median_price: number | null;
  min_price: number | null;
  max_price: number | null;
  std_dev: number | null;
  iqr: number | null;
}

export interface BrandAnalyticsResponse {
  total_brands_analyzed: number;
  brands: BrandAnalyticsItem[];
}

export interface DailyTrendDetail {
  date: string;
  count: number;
  mean_price: number;
  median_price: number;
  min_price: number;
  max_price: number;
  std_dev: number;
}

export interface PriceTrendRegression {
  slope: number | null;
  intercept: number | null;
  r_value: number | null;
  r_squared: number | null;
  p_value: number | null;
  std_err: number | null;
  direction: string;
  data_points: number;
}

export interface PriceTrendsResponse {
  daily_trends: DailyTrendDetail[];
  regression: PriceTrendRegression | null;
  direction: string;
}

export interface BrandBoxplot {
  brand: string;
  q1: number;
  median: number;
  q3: number;
  min_whisker: number;
  max_whisker: number;
  mean: number;
  sample_size: number;
}

export interface AnovaResponse {
  hypothesis: string;
  test_type: string;
  null_hypothesis: string;
  alternative_hypothesis: string;
  alpha: number;
  f_statistic: number | null;
  test_statistic?: number | null;
  p_value: number | null;
  decision: string;
  interpretation: string;
  engineering_explanation?: string | null;
  brands_evaluated: string[];
  brand_sample_sizes: Record<string, number>;
  brand_means: Record<string, number>;
  brand_boxplots?: BrandBoxplot[];
}

export interface TrendScatterPoint {
  date: string;
  days_elapsed: number;
  price: number;
  fitted_price: number | null;
  brand: string;
  product_name: string;
}

export interface Hypothesis2Trend {
  hypothesis: string;
  test_type: string;
  null_hypothesis: string;
  alternative_hypothesis: string;
  alpha: number;
  test_statistic?: number | null;
  coefficient: number | null;
  pearson_r: number | null;
  r_squared: number | null;
  p_value: number | null;
  trend_information: string | null;
  decision: string;
  interpretation: string;
  engineering_explanation?: string | null;
  sample_size: number;
  scatter_points?: TrendScatterPoint[];
}

export interface Hypothesis3Rating {
  hypothesis: string;
  test_type?: string;
  null_hypothesis?: string;
  alternative_hypothesis?: string;
  alpha?: number;
  status: string;
  message: string;
  test_statistic?: number | null;
  correlation: number | null;
  p_value: number | null;
  decision: string;
  interpretation: string;
  engineering_explanation?: string | null;
}

export interface DistributionBin {
  bin_label: string;
  min_price: number;
  max_price: number;
  count: number;
  percentage: number;
}

export interface CorrelationResponse {
  price_trend_hypothesis: Hypothesis2Trend;
  price_rating_hypothesis: Hypothesis3Rating;
  price_distribution?: {
    bins: DistributionBin[];
    skewness?: number;
    kurtosis?: number;
    mean?: number;
    median?: number;
  } | null;
  brand_comparison?: BrandAnalyticsItem[] | null;
}

export interface DataQualityMetrics {
  raw_records: number;
  clean_records: number;
  duplicate_records: number;
  missing_values: Record<string, { count: number; percentage: number }>;
  invalid_prices: number;
  invalid_timestamps: number;
  records_removed: number;
  cleaning_percentage: number;
}

export interface RemovedRecordItem {
  raw_index: number | null;
  product_id: string | null;
  product_name: string | null;
  raw_price: any;
  reasons: string;
  category?: string;
}

export interface PipelineStageItem {
  stage_number: number;
  name: string;
  icon: string;
  description: string;
  input_type: string;
  output_type: string;
  status: string;
  details?: string | null;
}

export interface DataQualityResponse {
  status: string;
  report_date: string | null;
  summary: string;
  metrics: DataQualityMetrics;
  removed_records: RemovedRecordItem[];
  pipeline_stages: PipelineStageItem[];
  raw_csv_available: boolean;
  cleaned_csv_available: boolean;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  database: string;
  version: string;
  environment: string;
}

export interface CollectorRunResponse {
  status: string;
  message: string;
  query_used: string | null;
  raw_file: string | null;
  cleaned_file: string | null;
  records_collected: number;
  records_cleaned: number;
  snapshots_inserted: number;
  snapshots_ignored_duplicates: number;
}

export type PageId =
  | 'dashboard'
  | 'products'
  | 'product-details'
  | 'compare'
  | 'price-trends'
  | 'brand-analytics'
  | 'statistical-analysis'
  | 'data-quality'
  | 'about';
