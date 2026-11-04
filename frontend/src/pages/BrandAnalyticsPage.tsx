import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { BrandAnalyticsResponse } from '../types';
import { LoadingSpinner, EmptyState, ErrorAlert } from '../components/common/Feedback';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';

interface BrandAnalyticsPageProps {
  demoMode: boolean;
}

export const BrandAnalyticsPage: React.FC<BrandAnalyticsPageProps> = ({ demoMode }) => {
  const [data, setData] = useState<BrandAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBrandData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getBrandAnalytics(demoMode);
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch brand-level analytics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBrandData();
  }, [demoMode]);

  if (loading) return <LoadingSpinner message="Aggregating brand-level cross-sectional metrics..." />;
  if (error) return <ErrorAlert error={error} onRetry={fetchBrandData} />;
  if (!data || data.brands.length === 0) {
    return (
      <EmptyState
        title="No brand data available."
        message="Collect sneaker products from multiple brands to evaluate cross-sectional market distributions."
      />
    );
  }

  const chartData = data.brands.map((b) => ({
    brand: b.brand,
    mean: b.mean_price || 0,
    median: b.median_price || 0,
    count: b.count,
    iqr: b.iqr || 0,
  }));

  return (
    <div className="space-y-8">
      {/* Brand High-Level Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {data.brands.map((b) => (
          <div
            key={b.brand}
            className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg backdrop-blur-md"
          >
            <p className="text-xs font-bold uppercase tracking-wider text-indigo-400">{b.brand}</p>
            <h4 className="mt-2 text-2xl font-black text-white">
              {b.mean_price ? `$${b.mean_price.toFixed(0)}` : 'N/A'}
            </h4>
            <div className="mt-3 flex items-center justify-between border-t border-slate-800/80 pt-2 text-xs text-slate-400">
              <span>{b.count} models</span>
              <span>Median: ${b.median_price?.toFixed(0) || 'N/A'}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Mean vs Median by Brand */}
        <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-md">
          <h3 className="text-base font-bold text-white">Mean vs. Median Price by Brand</h3>
          <p className="text-xs text-slate-400">Evaluating central tendency skewness across brand portfolios</p>

          <div className="mt-4 h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="brand" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} tickFormatter={(v) => `$${v}`} />
                <Tooltip
                  content={({ active, payload, label }: any) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="rounded-xl border border-slate-700 bg-slate-900/95 p-3 shadow-2xl backdrop-blur-md">
                          <p className="text-xs font-semibold text-slate-300">{label}</p>
                          <p className="text-xs font-bold text-indigo-400 mt-1">Mean: ${payload[0]?.value?.toFixed(2)}</p>
                          <p className="text-xs font-bold text-violet-400 mt-0.5">Median: ${payload[1]?.value?.toFixed(2)}</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="mean" name="Mean Price" fill="#6366f1" radius={[6, 6, 0, 0]} />
                <Bar dataKey="median" name="Median Price" fill="#a855f7" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Brand Dispersion: Interquartile Range (IQR) */}
        <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-md">
          <h3 className="text-base font-bold text-white">Price Dispersion: Interquartile Range (IQR)</h3>
          <p className="text-xs text-slate-400">Measures the middle 50% price spread ($Q_3 - Q_1$) to assess volatility</p>

          <div className="mt-4 h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="brand" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} tickFormatter={(v) => `$${v}`} />
                <Tooltip
                  content={({ active, payload, label }: any) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="rounded-xl border border-slate-700 bg-slate-900/95 p-3 shadow-2xl backdrop-blur-md">
                          <p className="text-xs font-semibold text-slate-300">{label}</p>
                          <p className="text-xs font-bold text-sky-400 mt-1">IQR: ${payload[0]?.value?.toFixed(2)}</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="iqr" name="IQR ($)" fill="#38bdf8" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Rigorous Statistical Table */}
      <div className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-900/60 shadow-xl backdrop-blur-md">
        <div className="border-b border-slate-800/80 p-5">
          <h3 className="text-base font-bold text-white">Full Brand Descriptive Statistics</h3>
          <p className="text-xs text-slate-400">Parametric and non-parametric metrics computed with NumPy and SciPy</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="border-b border-slate-800 bg-slate-950/70 text-xs uppercase tracking-wider text-slate-400">
              <tr>
                <th className="px-6 py-3.5">Brand</th>
                <th className="px-6 py-3.5">Observations</th>
                <th className="px-6 py-3.5">Mean (x̄)</th>
                <th className="px-6 py-3.5">Median (M)</th>
                <th className="px-6 py-3.5">Std Dev (s)</th>
                <th className="px-6 py-3.5">IQR Spread</th>
                <th className="px-6 py-3.5">Min Price</th>
                <th className="px-6 py-3.5">Max Price</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
              {data.brands.map((b) => (
                <tr key={b.brand} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-6 py-3.5 font-sans font-bold text-white">{b.brand}</td>
                  <td className="px-6 py-3.5 text-indigo-400">{b.count}</td>
                  <td className="px-6 py-3.5 font-bold text-slate-200">
                    {b.mean_price ? `$${b.mean_price.toFixed(2)}` : 'N/A'}
                  </td>
                  <td className="px-6 py-3.5 text-slate-300">
                    {b.median_price ? `$${b.median_price.toFixed(2)}` : 'N/A'}
                  </td>
                  <td className="px-6 py-3.5 text-slate-400">
                    {b.std_dev ? `$${b.std_dev.toFixed(2)}` : 'N/A'}
                  </td>
                  <td className="px-6 py-3.5 text-sky-400">
                    {b.iqr ? `$${b.iqr.toFixed(2)}` : 'N/A'}
                  </td>
                  <td className="px-6 py-3.5 text-slate-400">
                    {b.min_price ? `$${b.min_price.toFixed(2)}` : 'N/A'}
                  </td>
                  <td className="px-6 py-3.5 text-slate-400">
                    {b.max_price ? `$${b.max_price.toFixed(2)}` : 'N/A'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
