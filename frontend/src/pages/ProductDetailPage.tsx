import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { SneakerProduct, ProductPriceHistory, PageId } from '../types';
import { LoadingSpinner, EmptyState, ErrorAlert } from '../components/common/Feedback';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';

interface ProductDetailPageProps {
  productId: string | null;
  demoMode: boolean;
  onNavigate: (page: PageId) => void;
  onCompareProduct?: (productId: string) => void;
}

export const ProductDetailPage: React.FC<ProductDetailPageProps> = ({
  productId,
  demoMode,
  onNavigate,
  onCompareProduct,
}) => {
  const [product, setProduct] = useState<SneakerProduct | null>(null);
  const [history, setHistory] = useState<ProductPriceHistory | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDetails = async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      const [pRes, hRes] = await Promise.all([
        api.getProduct(id),
        api.getPriceHistory(id, demoMode),
      ]);
      setProduct(pRes);
      setHistory(hRes);
    } catch (err: any) {
      setError(err.message || `Failed to fetch details for product: ${id}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (productId) {
      fetchDetails(productId);
    } else {
      // Pick first available product if none selected
      api.getProducts({ page: 1, limit: 1, includeDemo: demoMode })
        .then((res) => {
          if (res.items.length > 0) {
            fetchDetails(res.items[0].product_id);
          } else {
            setLoading(false);
          }
        })
        .catch(() => setLoading(false));
    }
  }, [productId, demoMode]);

  if (!productId && !product && !loading) {
    return (
      <EmptyState
        title="No Sneaker Selected"
        message="Please select a sneaker from the products catalog to inspect its historical price intelligence."
        actionText="Browse Products Catalog"
        onAction={() => onNavigate('products')}
      />
    );
  }

  if (loading) return <LoadingSpinner message="Retrieving time-series price snapshots & product telemetry..." />;
  if (error) return <ErrorAlert error={error} onRetry={() => productId && fetchDetails(productId)} />;
  if (!product) return null;

  const hasPremium = product.resale_premium_pct !== null;
  const isPositive = (product.resale_premium_pct ?? 0) >= 0;

  // Chart data sorted by date
  const chartData = (history?.snapshots || [])
    .slice()
    .sort((a, b) => a.collection_date.localeCompare(b.collection_date))
    .map((s) => ({
      date: s.collection_date,
      price: s.price,
      platform: s.platform,
    }));

  return (
    <div className="space-y-8">
      {/* Top action row */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => onNavigate('products')}
          className="inline-flex items-center space-x-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors"
        >
          <span>← Back to Products</span>
        </button>
        {onCompareProduct && (
          <button
            onClick={() => onCompareProduct(product.product_id)}
            className="inline-flex items-center space-x-2 rounded-xl border border-indigo-500/40 bg-indigo-600/10 px-3.5 py-1.5 text-xs font-bold text-indigo-300 hover:bg-indigo-600/20 transition-all"
          >
            <span>Compare in Matrix →</span>
          </button>
        )}
      </div>

      {/* Hero Card */}
      <div className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-900/60 p-8 shadow-2xl backdrop-blur-xl">
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          {/* Sneaker Image Frame */}
          <div className="flex items-center justify-center rounded-2xl border border-slate-800 bg-slate-950 p-6 shadow-inner">
            {product.image_url ? (
              <img
                src={product.image_url}
                alt={product.name}
                className="max-h-64 max-w-full object-contain filter drop-shadow-[0_10px_20px_rgba(0,0,0,0.5)]"
              />
            ) : (
              <div className="flex flex-col items-center justify-center p-12 text-slate-600">
                <span className="text-6xl">👟</span>
                <span className="mt-3 text-xs font-semibold uppercase tracking-wider">No Image Asset</span>
              </div>
            )}
          </div>

          {/* Core Specs */}
          <div className="lg:col-span-2 flex flex-col justify-between">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-md border border-indigo-500/30 bg-indigo-500/10 px-2.5 py-1 text-xs font-bold uppercase tracking-wider text-indigo-400">
                  {product.brand || 'Unbranded'}
                </span>
                {product.is_demo === 1 && (
                  <span className="rounded-md border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-xs font-bold text-amber-300">
                    Sample Data
                  </span>
                )}
                {hasPremium && (
                  <span
                    className={`rounded-md border px-2.5 py-1 text-xs font-bold ${
                      isPositive
                        ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400'
                        : 'border-rose-500/30 bg-rose-500/10 text-rose-400'
                    }`}
                  >
                    Resale Premium: {isPositive ? `+${product.resale_premium_pct}%` : `${product.resale_premium_pct}%`}
                  </span>
                )}
              </div>

              <h1 className="mt-3 text-2xl font-extrabold tracking-tight text-white sm:text-3xl">
                {product.name}
              </h1>

              <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4 border-t border-slate-800/80 pt-4">
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Style / SKU</p>
                  <p className="mt-0.5 text-sm font-mono font-bold text-slate-200">{product.product_id}</p>
                </div>
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Retail MSRP</p>
                  <p className="mt-0.5 text-sm font-bold text-slate-200">
                    {product.retail_price ? `$${product.retail_price.toFixed(2)}` : 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Release Date</p>
                  <p className="mt-0.5 text-sm font-semibold text-slate-200">{product.release_date || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Total Snapshots</p>
                  <p className="mt-0.5 text-sm font-bold text-indigo-400">{product.snapshot_count}</p>
                </div>
              </div>
            </div>

            {/* Current Price Highlight Bar */}
            <div className="mt-6 flex items-center justify-between rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
              <div>
                <span className="text-xs text-slate-400">Current Market Price</span>
                <p className="text-3xl font-black tracking-tight text-white">
                  {product.latest_price ? `$${product.latest_price.toFixed(2)}` : 'N/A'}
                </p>
              </div>
              <div className="text-right">
                <span className="text-xs text-slate-400">Market Spread</span>
                <p className="text-sm font-bold text-slate-300">
                  {product.latest_price && product.retail_price
                    ? `$${(product.latest_price - product.retail_price).toFixed(2)} variance`
                    : 'N/A'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Historical Price Trend Area Chart */}
      <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-md">
        <h3 className="text-base font-bold text-white">Historical Price Trajectory</h3>
        <p className="text-xs text-slate-400">Time-series price snapshots over observation dates</p>

        <div className="mt-4 h-72 w-full">
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <defs>
                  <linearGradient id="detailGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#818cf8" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#818cf8" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} tickFormatter={(v) => `$${v}`} />
                <Tooltip
                  content={({ active, payload, label }: any) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="rounded-xl border border-slate-700 bg-slate-900/95 p-3 shadow-2xl backdrop-blur-md">
                          <p className="text-xs font-semibold text-slate-300">{label}</p>
                          <p className="text-sm font-bold text-indigo-400 mt-1">
                            ${payload[0].value?.toFixed(2)} ({payload[0].payload.platform})
                          </p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Area type="monotone" dataKey="price" stroke="#818cf8" strokeWidth={2.5} fillOpacity={1} fill="url(#detailGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex h-full items-center justify-center text-xs text-slate-500">
              Only a single snapshot recorded. Additional historical collections needed to plot time-series trend.
            </div>
          )}
        </div>
      </div>

      {/* Snapshot Logs Table */}
      <div className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-900/60 shadow-xl backdrop-blur-md">
        <div className="border-b border-slate-800/80 p-5">
          <h3 className="text-base font-bold text-white">Recorded Snapshot Logs</h3>
          <p className="text-xs text-slate-400">Preserved historical price observations stored in SQLite</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="border-b border-slate-800 bg-slate-950/70 text-xs uppercase tracking-wider text-slate-400">
              <tr>
                <th className="px-6 py-3.5">Snapshot Date</th>
                <th className="px-6 py-3.5">Marketplace</th>
                <th className="px-6 py-3.5">Recorded Price</th>
                <th className="px-6 py-3.5">Size</th>
                <th className="px-6 py-3.5">Condition</th>
                <th className="px-6 py-3.5">Seller</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {(history?.snapshots || []).map((s) => (
                <tr key={s.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-6 py-3.5 font-mono text-xs text-slate-300">{s.collection_date}</td>
                  <td className="px-6 py-3.5 font-semibold text-indigo-300">{s.platform}</td>
                  <td className="px-6 py-3.5 font-mono font-bold text-white">${s.price.toFixed(2)}</td>
                  <td className="px-6 py-3.5 text-xs text-slate-400">{s.size || 'Unspecified'}</td>
                  <td className="px-6 py-3.5 text-xs text-slate-400 capitalize">{s.condition}</td>
                  <td className="px-6 py-3.5 text-xs text-slate-400">{s.seller || 'Verified'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
