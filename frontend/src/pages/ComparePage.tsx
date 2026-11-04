import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { SneakerProduct } from '../types';
import { LoadingSpinner, EmptyState, ErrorAlert } from '../components/common/Feedback';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts';

interface ComparePageProps {
  initialProductId?: string | null;
  demoMode: boolean;
}

export const ComparePage: React.FC<ComparePageProps> = ({ initialProductId, demoMode }) => {
  const [allProducts, setAllProducts] = useState<SneakerProduct[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadProducts = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await api.getProducts({ page: 1, limit: 50, includeDemo: demoMode });
        setAllProducts(res.items);

        // Pre-select 2 products
        if (res.items.length >= 2) {
          const first = initialProductId || res.items[0].product_id;
          const second = res.items.find((p) => p.product_id !== first)?.product_id || res.items[1].product_id;
          setSelectedIds([first, second]);
        } else if (res.items.length === 1) {
          setSelectedIds([res.items[0].product_id]);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load catalog for comparison.');
      } finally {
        setLoading(false);
      }
    };
    loadProducts();
  }, [demoMode, initialProductId]);

  const toggleSelect = (pid: string) => {
    if (selectedIds.includes(pid)) {
      if (selectedIds.length > 1) {
        setSelectedIds(selectedIds.filter((id) => id !== pid));
      }
    } else {
      if (selectedIds.length < 4) {
        setSelectedIds([...selectedIds, pid]);
      }
    }
  };

  if (loading) return <LoadingSpinner message="Loading sneaker matrix for comparison..." />;
  if (error) return <ErrorAlert error={error} />;
  if (allProducts.length === 0) {
    return (
      <EmptyState
        title="Insufficient products for comparison."
        message="At least 2 sneaker models must be available in the dataset to perform comparative analysis."
      />
    );
  }

  const comparedProducts = allProducts.filter((p) => selectedIds.includes(p.product_id));

  // Chart data
  const chartData = comparedProducts.map((p) => ({
    name: p.name.length > 20 ? p.name.slice(0, 20) + '...' : p.name,
    retail: p.retail_price || 0,
    market: p.latest_price || 0,
  }));

  return (
    <div className="space-y-8">
      {/* Selector Drawer */}
      <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-md">
        <h3 className="text-base font-bold text-white">Select Models to Compare (Up to 4)</h3>
        <p className="text-xs text-slate-400 mt-0.5">Click models below to toggle them in the comparison matrix</p>

        <div className="mt-4 flex flex-wrap gap-2">
          {allProducts.map((p) => {
            const isSelected = selectedIds.includes(p.product_id);
            return (
              <button
                key={p.product_id}
                onClick={() => toggleSelect(p.product_id)}
                className={`rounded-xl border px-3 py-1.5 text-xs font-semibold transition-all ${
                  isSelected
                    ? 'border-indigo-500 bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                    : 'border-slate-800 bg-slate-950/80 text-slate-400 hover:border-slate-700 hover:text-white'
                }`}
              >
                {isSelected ? '✓ ' : '+ '}
                {p.brand ? `${p.brand} ` : ''}
                {p.name.slice(0, 22)}...
              </button>
            );
          })}
        </div>
      </div>

      {/* Comparison Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {comparedProducts.map((p) => {
          const hasPremium = p.resale_premium_pct !== null;
          const isPositive = (p.resale_premium_pct ?? 0) >= 0;

          return (
            <div
              key={p.product_id}
              className="rounded-3xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-md flex flex-col justify-between"
            >
              <div>
                <div className="flex h-40 w-full items-center justify-center rounded-2xl bg-slate-950 p-3 border border-slate-800/80">
                  {p.image_url ? (
                    <img src={p.image_url} alt={p.name} className="h-full w-full object-contain" />
                  ) : (
                    <span className="text-5xl">👟</span>
                  )}
                </div>
                <span className="mt-4 inline-block text-[10px] font-bold uppercase tracking-wider text-indigo-400">
                  {p.brand || 'Unbranded'}
                </span>
                <h4 className="mt-1 line-clamp-2 text-base font-bold text-white">{p.name}</h4>
                <p className="text-xs font-mono text-slate-500 mt-0.5">{p.product_id}</p>
              </div>

              <div className="mt-6 space-y-2 border-t border-slate-800/80 pt-4">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Retail MSRP:</span>
                  <span className="font-semibold text-slate-300">
                    {p.retail_price ? `$${p.retail_price.toFixed(2)}` : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Current Market:</span>
                  <span className="font-extrabold text-white">
                    {p.latest_price ? `$${p.latest_price.toFixed(2)}` : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Resale Premium:</span>
                  <span
                    className={`font-bold ${
                      hasPremium
                        ? isPositive
                          ? 'text-emerald-400'
                          : 'text-rose-400'
                        : 'text-slate-500'
                    }`}
                  >
                    {hasPremium ? (isPositive ? `+${p.resale_premium_pct}%` : `${p.resale_premium_pct}%`) : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Snapshots Logged:</span>
                  <span className="font-mono text-indigo-400">{p.snapshot_count}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Visual Bar Comparison Chart */}
      <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-md">
        <h3 className="text-base font-bold text-white">Retail vs. Resale Price Comparison</h3>
        <p className="text-xs text-slate-400">Direct spread comparison between original MSRP and current secondary market price</p>

        <div className="mt-6 h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} />
              <YAxis stroke="#64748b" fontSize={11} tickLine={false} tickFormatter={(v) => `$${v}`} />
              <Tooltip
                content={({ active, payload, label }: any) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="rounded-xl border border-slate-700 bg-slate-900/95 p-3 shadow-2xl backdrop-blur-md">
                        <p className="text-xs font-semibold text-slate-300">{label}</p>
                        <p className="text-xs font-bold text-slate-400 mt-1">Retail: ${payload[0]?.value?.toFixed(2)}</p>
                        <p className="text-xs font-bold text-indigo-400 mt-0.5">Market: ${payload[1]?.value?.toFixed(2)}</p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
              <Bar dataKey="retail" name="Retail MSRP" fill="#64748b" radius={[6, 6, 0, 0]} />
              <Bar dataKey="market" name="Latest Market Price" fill="#6366f1" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
