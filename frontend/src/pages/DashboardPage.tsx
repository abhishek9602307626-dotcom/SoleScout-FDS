import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { DashboardData, PageId } from '../types';
import { KpiCard } from '../components/common/KpiCard';
import { LoadingSpinner, EmptyState, ErrorAlert } from '../components/common/Feedback';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';

interface DashboardPageProps {
  demoMode: boolean;
  onNavigate: (page: PageId) => void;
  onSelectProduct?: (productId: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  demoMode,
  onNavigate,
}) => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getDashboard(demoMode);
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to SoleScout backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, [demoMode]);

  if (loading) return <LoadingSpinner message="Aggregating market intelligence & historical snapshots..." />;
  if (error) return <ErrorAlert error={error} onRetry={fetchDashboard} />;
  if (!data || data.is_empty) {
    return (
      <EmptyState
        title="No SoleScout data has been collected yet."
        message="The intelligence database is currently empty. Run the Python collector or enable Demo Mode in the sidebar to explore."
        actionText="Go to Data Quality & Pipeline"
        onAction={() => onNavigate('data-quality')}
      />
    );
  }

  const desc = data.descriptive_summary;

  // Calculate collection days
  let collectionDays = 1;
  if (data.date_range_start && data.date_range_end) {
    const d1 = new Date(data.date_range_start).getTime();
    const d2 = new Date(data.date_range_end).getTime();
    collectionDays = Math.max(1, Math.round((d2 - d1) / (1000 * 60 * 60 * 24)) + 1);
  }

  // Custom Dark Tooltip
  const CustomTooltip = ({ active, payload, label, prefix = '$', suffix = '' }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="rounded-xl border border-slate-700 bg-slate-900/95 p-3 shadow-2xl backdrop-blur-md">
          <p className="text-xs font-semibold text-slate-300">{label}</p>
          <p className="text-sm font-bold text-indigo-400 mt-1">
            {prefix}{payload[0].value?.toLocaleString()}{suffix}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-8">
      {/* 1. SEVEN KPI CARDS */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7">
        <KpiCard
          title="Total Products"
          value={data.total_products.toLocaleString()}
          subtitle="Distinct models"
          badgeColor="blue"
        />
        <KpiCard
          title="Total Brands"
          value={data.unique_brands}
          subtitle="Footwear makers"
          badgeColor="purple"
        />
        <KpiCard
          title="Average Price"
          value={desc.mean ? `$${desc.mean.toFixed(2)}` : 'N/A'}
          subtitle={`Median: $${desc.median?.toFixed(0) || 'N/A'}`}
          badgeColor="green"
        />
        <KpiCard
          title="Minimum Price"
          value={desc.min_price ? `$${desc.min_price.toFixed(2)}` : 'N/A'}
          subtitle="Lowest in dataset"
          badgeColor="gray"
        />
        <KpiCard
          title="Maximum Price"
          value={desc.max_price ? `$${desc.max_price.toFixed(2)}` : 'N/A'}
          subtitle="Highest peak"
          badgeColor="yellow"
        />
        <KpiCard
          title="Historical Snapshots"
          value={data.total_snapshots.toLocaleString()}
          subtitle="Time-series logs"
          badgeColor="blue"
        />
        <KpiCard
          title="Collection Days"
          value={`${collectionDays} d`}
          subtitle={data.date_range_start || 'Observed'}
          badgeColor="purple"
        />
      </div>

      {/* 2. CHARTS SECTION (2x2 Grid) */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Chart 1: Average Price Over Time */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md">
          <div className="flex items-center justify-between pb-4">
            <div>
              <h3 className="text-base font-bold text-white">Average Price Over Time</h3>
              <p className="text-xs text-slate-400">Chronological daily price tracking</p>
            </div>
            <button
              onClick={() => onNavigate('price-trends')}
              className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              Analyze Trends →
            </button>
          </div>
          <div className="h-72 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.price_trends} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <defs>
                  <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} tickFormatter={(v) => `$${v}`} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="avg_price" stroke="#6366f1" strokeWidth={2.5} fillOpacity={1} fill="url(#priceGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Average Price by Brand */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md">
          <div className="flex items-center justify-between pb-4">
            <div>
              <h3 className="text-base font-bold text-white">Average Price by Brand</h3>
              <p className="text-xs text-slate-400">Cross-sectional brand price comparisons</p>
            </div>
            <button
              onClick={() => onNavigate('brand-analytics')}
              className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              Full Brand Stats →
            </button>
          </div>
          <div className="h-72 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.brand_comparison} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="brand" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} tickFormatter={(v) => `$${v}`} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="mean_price" fill="#818cf8" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 3: Product Count by Brand */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md">
          <div className="flex items-center justify-between pb-4">
            <div>
              <h3 className="text-base font-bold text-white">Product Count by Brand</h3>
              <p className="text-xs text-slate-400">Catalog representation and volume</p>
            </div>
            <button
              onClick={() => onNavigate('products')}
              className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              Browse Catalog →
            </button>
          </div>
          <div className="h-72 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.brand_comparison} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="brand" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} allowDecimals={false} />
                <Tooltip content={<CustomTooltip prefix="" suffix=" models" />} />
                <Bar dataKey="count" fill="#a78bfa" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 4: Price Distribution */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md">
          <div className="flex items-center justify-between pb-4">
            <div>
              <h3 className="text-base font-bold text-white">Price Distribution</h3>
              <p className="text-xs text-slate-400">Market histogram frequencies</p>
            </div>
            <button
              onClick={() => onNavigate('statistical-analysis')}
              className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              FDS Analysis →
            </button>
          </div>
          <div className="h-72 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.price_distribution} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="range" stroke="#64748b" fontSize={10} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip content={<CustomTooltip prefix="" suffix=" pairs" />} />
                <Bar dataKey="count" fill="#38bdf8" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
