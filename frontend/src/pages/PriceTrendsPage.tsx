import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { PriceTrendsResponse } from '../types';
import { LoadingSpinner, EmptyState, ErrorAlert } from '../components/common/Feedback';
import { KpiCard } from '../components/common/KpiCard';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';

interface PriceTrendsPageProps {
  demoMode: boolean;
}

export const PriceTrendsPage: React.FC<PriceTrendsPageProps> = ({ demoMode }) => {
  const [data, setData] = useState<PriceTrendsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTrends = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getPriceTrends(demoMode);
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch price trend telemetry.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrends();
  }, [demoMode]);

  if (loading) return <LoadingSpinner message="Fitting SciPy Ordinary Least Squares regression model..." />;
  if (error) return <ErrorAlert error={error} onRetry={fetchTrends} />;
  if (!data || data.daily_trends.length === 0) {
    return (
      <EmptyState
        title="Insufficient temporal data points."
        message="Historical snapshots over multiple dates are required to calculate regression slopes and trend lines."
      />
    );
  }

  const reg = data.regression;

  // Compute trend line data points
  const chartData = data.daily_trends.map((d, idx) => {
    let fittedVal = null;
    if (reg && reg.slope !== null && reg.intercept !== null) {
      fittedVal = Number((reg.intercept + reg.slope * idx).toFixed(2));
    }
    return {
      date: d.date,
      mean_price: d.mean_price,
      median_price: d.median_price,
      min_price: d.min_price,
      max_price: d.max_price,
      volume: d.count,
      fitted_regression: fittedVal,
    };
  });

  return (
    <div className="space-y-8">
      {/* KPI Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          title="Market Direction"
          value={data.direction.toUpperCase()}
          subtitle="Longitudinal movement"
          badge={data.direction}
          badgeColor={
            data.direction === 'appreciating'
              ? 'green'
              : data.direction === 'depreciating'
              ? 'yellow'
              : 'blue'
          }
        />
        <KpiCard
          title="OLS Slope (β)"
          value={reg?.slope !== null && reg?.slope !== undefined ? `${reg.slope >= 0 ? '+' : ''}$${reg.slope.toFixed(2)}/d` : 'N/A'}
          subtitle="Daily rate of price change"
          badgeColor="purple"
        />
        <KpiCard
          title="R-Squared (R²)"
          value={reg?.r_squared !== null && reg?.r_squared !== undefined ? reg.r_squared.toFixed(4) : 'N/A'}
          subtitle="Model explanatory power"
          badgeColor="blue"
        />
        <KpiCard
          title="Regression p-value"
          value={reg?.p_value !== null && reg?.p_value !== undefined ? reg.p_value.toFixed(4) : 'N/A'}
          subtitle={reg?.p_value && reg.p_value < 0.05 ? 'Significant (p < 0.05)' : 'Not significant'}
          badgeColor={reg?.p_value && reg.p_value < 0.05 ? 'green' : 'gray'}
        />
      </div>

      {/* Main Longitudinal Trend Chart */}
      <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-md">
        <div className="flex items-center justify-between pb-4">
          <div>
            <h3 className="text-base font-bold text-white">Longitudinal Price Trend with OLS Regression</h3>
            <p className="text-xs text-slate-400">Daily average market prices plotted against fitted linear trajectory</p>
          </div>
          <span className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1 text-xs font-mono text-slate-300">
            {chartData.length} Observation Windows
          </span>
        </div>

        <div className="h-80 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
              <YAxis stroke="#64748b" fontSize={11} tickLine={false} tickFormatter={(v) => `$${v}`} />
              <Tooltip
                content={({ active, payload, label }: any) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="rounded-xl border border-slate-700 bg-slate-900/95 p-3 shadow-2xl backdrop-blur-md">
                        <p className="text-xs font-semibold text-slate-300">{label}</p>
                        <p className="text-xs font-bold text-indigo-400 mt-1">Mean: ${payload[0]?.value?.toFixed(2)}</p>
                        {payload[1] && (
                          <p className="text-xs font-bold text-violet-400 mt-0.5">Median: ${payload[1]?.value?.toFixed(2)}</p>
                        )}
                        {payload[2] && payload[2].value && (
                          <p className="text-xs font-mono text-emerald-400 mt-0.5">OLS Fit: ${payload[2]?.value?.toFixed(2)}</p>
                        )}
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
              <Line type="monotone" dataKey="mean_price" name="Mean Price ($)" stroke="#6366f1" strokeWidth={2.5} dot={{ r: 4, fill: '#6366f1' }} />
              <Line type="monotone" dataKey="median_price" name="Median Price ($)" stroke="#a855f7" strokeWidth={2} strokeDasharray="4 4" dot={false} />
              {reg && reg.slope !== null && (
                <Line type="linear" dataKey="fitted_regression" name="OLS Linear Trend (β)" stroke="#10b981" strokeWidth={2} dot={false} />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Daily Breakdown Table */}
      <div className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-900/60 shadow-xl backdrop-blur-md">
        <div className="border-b border-slate-800/80 p-5">
          <h3 className="text-base font-bold text-white">Daily Aggregate Statistics Table</h3>
          <p className="text-xs text-slate-400">Granular daily aggregations of sample mean, median, standard deviation, and volume</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="border-b border-slate-800 bg-slate-950/70 text-xs uppercase tracking-wider text-slate-400">
              <tr>
                <th className="px-6 py-3.5">Observation Date</th>
                <th className="px-6 py-3.5">Snapshots</th>
                <th className="px-6 py-3.5">Mean Price</th>
                <th className="px-6 py-3.5">Median Price</th>
                <th className="px-6 py-3.5">Price Range (Min - Max)</th>
                <th className="px-6 py-3.5">Std Dev (s)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {data.daily_trends.map((row) => (
                <tr key={row.date} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-6 py-3.5 font-mono text-xs text-slate-200">{row.date}</td>
                  <td className="px-6 py-3.5 font-bold text-indigo-400">{row.count}</td>
                  <td className="px-6 py-3.5 font-mono font-bold text-white">${row.mean_price.toFixed(2)}</td>
                  <td className="px-6 py-3.5 font-mono text-slate-300">${row.median_price.toFixed(2)}</td>
                  <td className="px-6 py-3.5 font-mono text-xs text-slate-400">
                    ${row.min_price.toFixed(0)} - ${row.max_price.toFixed(0)}
                  </td>
                  <td className="px-6 py-3.5 font-mono text-xs text-slate-400">
                    ${row.std_dev.toFixed(2)}
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
