/**
 * SoleScout Frontend API Service
 * Exclusively communicates with the FastAPI backend (/api).
 * NEVER directly accesses SQLite or SoleScout credentials.
 */

import {
  HealthResponse,
  DashboardData,
  PaginatedProducts,
  SneakerProduct,
  ProductPriceHistory,
  BrandsListResponse,
  BrandAnalyticsResponse,
  PriceTrendsResponse,
  AnovaResponse,
  CorrelationResponse,
  DataQualityResponse,
  CollectorRunResponse,
} from '../types';

const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  (typeof window !== 'undefined' && window.location.port === '5173'
    ? 'http://127.0.0.1:8000/api'
    : '/api');

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const errJson = await res.json();
      if (errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // Non-JSON error payload
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  async getHealth(): Promise<HealthResponse> {
    const res = await fetch(`${API_BASE_URL}/health`);
    return handleResponse<HealthResponse>(res);
  },

  async getDashboard(includeDemo = true): Promise<DashboardData> {
    const res = await fetch(`${API_BASE_URL}/dashboard?include_demo=${includeDemo}`);
    return handleResponse<DashboardData>(res);
  },

  async getProducts(params: {
    page?: number;
    limit?: number;
    search?: string;
    brand?: string;
    sortBy?: string;
    order?: 'asc' | 'desc';
    includeDemo?: boolean;
  } = {}): Promise<PaginatedProducts> {
    const query = new URLSearchParams();
    if (params.page) query.set('page', String(params.page));
    if (params.limit) query.set('limit', String(params.limit));
    if (params.search) query.set('search', params.search);
    if (params.brand) query.set('brand', params.brand);
    if (params.sortBy) query.set('sort_by', params.sortBy);
    if (params.order) query.set('order', params.order);
    if (params.includeDemo !== undefined) query.set('include_demo', String(params.includeDemo));

    const res = await fetch(`${API_BASE_URL}/products?${query.toString()}`);
    return handleResponse<PaginatedProducts>(res);
  },

  async getProduct(productId: string): Promise<SneakerProduct> {
    const res = await fetch(`${API_BASE_URL}/products/${encodeURIComponent(productId)}`);
    return handleResponse<SneakerProduct>(res);
  },

  async getPriceHistory(productId: string, includeDemo = true): Promise<ProductPriceHistory> {
    const res = await fetch(
      `${API_BASE_URL}/price-history/${encodeURIComponent(productId)}?include_demo=${includeDemo}`
    );
    return handleResponse<ProductPriceHistory>(res);
  },

  async getBrands(includeDemo = true): Promise<BrandsListResponse> {
    const res = await fetch(`${API_BASE_URL}/brands?include_demo=${includeDemo}`);
    return handleResponse<BrandsListResponse>(res);
  },

  async getBrandAnalytics(includeDemo = true): Promise<BrandAnalyticsResponse> {
    const res = await fetch(`${API_BASE_URL}/analytics/brands?include_demo=${includeDemo}`);
    return handleResponse<BrandAnalyticsResponse>(res);
  },

  async getPriceTrends(includeDemo = true): Promise<PriceTrendsResponse> {
    const res = await fetch(`${API_BASE_URL}/analytics/price-trends?include_demo=${includeDemo}`);
    return handleResponse<PriceTrendsResponse>(res);
  },

  async getAnova(alpha = 0.05, includeDemo = true): Promise<AnovaResponse> {
    const res = await fetch(`${API_BASE_URL}/statistics/anova?alpha=${alpha}&include_demo=${includeDemo}`);
    return handleResponse<AnovaResponse>(res);
  },

  async getCorrelation(alpha = 0.05, includeDemo = true): Promise<CorrelationResponse> {
    const res = await fetch(`${API_BASE_URL}/statistics/correlation?alpha=${alpha}&include_demo=${includeDemo}`);
    return handleResponse<CorrelationResponse>(res);
  },

  async getDataQuality(): Promise<DataQualityResponse> {
    const res = await fetch(`${API_BASE_URL}/data-quality`);
    return handleResponse<DataQualityResponse>(res);
  },

  async runCollector(params: {
    queries?: string;
    pages?: number;
    limit?: number;
    demo?: boolean;
  }): Promise<CollectorRunResponse> {
    const res = await fetch(`${API_BASE_URL}/collector/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    return handleResponse<CollectorRunResponse>(res);
  },
};
