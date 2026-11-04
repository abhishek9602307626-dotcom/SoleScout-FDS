import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { PaginatedProducts, PageId } from '../types';
import { LoadingSpinner, EmptyState, ErrorAlert } from '../components/common/Feedback';
import { SearchIcon } from '../components/common/Icons';

interface ProductsPageProps {
  demoMode: boolean;
  onSelectProduct: (productId: string) => void;
  onNavigate: (page: PageId) => void;
}

export const ProductsPage: React.FC<ProductsPageProps> = ({
  demoMode,
  onSelectProduct,
  // onNavigate reserved for future breadcrumb / routing use
}) => {
  const [data, setData] = useState<PaginatedProducts | null>(null);
  const [page, setPage] = useState<number>(1);
  const [search, setSearch] = useState<string>('');
  const [brand, setBrand] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('id');
  const [order, setOrder] = useState<'asc' | 'desc'>('desc');
  const [availableBrands, setAvailableBrands] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');

  const fetchProducts = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getProducts({
        page,
        limit: 12,
        search: search.trim() || undefined,
        brand: brand || undefined,
        sortBy,
        order,
        includeDemo: demoMode,
      });
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch sneaker catalog.');
    } finally {
      setLoading(false);
    }
  };

  const fetchBrandList = async () => {
    try {
      const res = await api.getBrands(demoMode);
      setAvailableBrands(res.brands.map((b) => b.brand));
    } catch {
      // Ignore
    }
  };

  useEffect(() => {
    fetchBrandList();
  }, [demoMode]);

  useEffect(() => {
    fetchProducts();
  }, [page, brand, sortBy, order, demoMode]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchProducts();
  };

  return (
    <div className="space-y-6">
      {/* Search & Filter Bar */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-xl backdrop-blur-md">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          {/* Search Form */}
          <form onSubmit={handleSearchSubmit} className="relative flex-1">
            <SearchIcon className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search sneaker title, style code, SKU or brand..."
              className="w-full rounded-xl border border-slate-800 bg-slate-950/80 py-2.5 pl-10 pr-4 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </form>

          {/* Controls: Brand, Sort, Order, View toggle */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Brand Filter */}
            <select
              value={brand}
              onChange={(e) => {
                setBrand(e.target.value);
                setPage(1);
              }}
              className="rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-xs font-medium text-slate-300 focus:border-indigo-500 focus:outline-none"
            >
              <option value="">All Brands</option>
              {availableBrands.map((b) => (
                <option key={b} value={b}>
                  {b}
                </option>
              ))}
            </select>

            {/* Sort Field */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-xs font-medium text-slate-300 focus:border-indigo-500 focus:outline-none"
            >
              <option value="id">Latest Added</option>
              <option value="name">Product Title</option>
              <option value="retail_price">Retail Price</option>
            </select>

            {/* Order */}
            <button
              onClick={() => setOrder(order === 'asc' ? 'desc' : 'asc')}
              className="rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-xs font-semibold text-slate-300 hover:text-white transition-colors"
            >
              {order === 'asc' ? '↑ Ascending' : '↓ Descending'}
            </button>

            {/* View Mode */}
            <div className="flex rounded-xl border border-slate-800 bg-slate-950/80 p-0.5">
              <button
                onClick={() => setViewMode('grid')}
                className={`rounded-lg px-2.5 py-1 text-xs font-semibold transition-all ${
                  viewMode === 'grid' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'
                }`}
              >
                Grid
              </button>
              <button
                onClick={() => setViewMode('table')}
                className={`rounded-lg px-2.5 py-1 text-xs font-semibold transition-all ${
                  viewMode === 'table' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'
                }`}
              >
                Table
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Catalog Content */}
      {loading ? (
        <LoadingSpinner message="Querying live product models from FastAPI..." />
      ) : error ? (
        <ErrorAlert error={error} onRetry={fetchProducts} />
      ) : !data || data.items.length === 0 ? (
        <EmptyState
          title="No sneakers found matching your criteria."
          message="Try resetting your search query or brand filter."
          actionText="Clear Filters"
          onAction={() => {
            setSearch('');
            setBrand('');
            setPage(1);
          }}
        />
      ) : viewMode === 'grid' ? (
        /* GRID VIEW */
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {data.items.map((sneaker) => {
            const hasPremium = sneaker.resale_premium_pct !== null;
            const isPositive = (sneaker.resale_premium_pct ?? 0) >= 0;

            return (
              <div
                key={sneaker.id}
                onClick={() => onSelectProduct(sneaker.product_id)}
                className="group relative cursor-pointer overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-xl backdrop-blur-md transition-all duration-300 hover:-translate-y-1 hover:border-indigo-500/50 hover:shadow-2xl hover:shadow-indigo-500/10"
              >
                {/* Image / Thumbnail Container */}
                <div className="relative mb-4 flex h-48 w-full items-center justify-center overflow-hidden rounded-xl bg-slate-950/80 p-3">
                  {sneaker.image_url ? (
                    <img
                      src={sneaker.image_url}
                      alt={sneaker.name}
                      className="h-full w-full object-contain transition-transform duration-500 group-hover:scale-105"
                      onError={(e) => {
                        (e.target as HTMLElement).style.display = 'none';
                      }}
                    />
                  ) : (
                    <div className="flex flex-col items-center justify-center text-slate-600">
                      <span className="text-4xl">👟</span>
                      <span className="mt-2 text-[10px] uppercase tracking-wider font-semibold">No Image</span>
                    </div>
                  )}

                  {sneaker.is_demo === 1 && (
                    <span className="absolute left-2.5 top-2.5 rounded-md border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[10px] font-bold text-amber-300">
                      Sample
                    </span>
                  )}

                  {hasPremium && (
                    <span
                      className={`absolute right-2.5 top-2.5 rounded-md border px-2 py-0.5 text-[10px] font-bold ${
                        isPositive
                          ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400'
                          : 'border-rose-500/30 bg-rose-500/10 text-rose-400'
                      }`}
                    >
                      {isPositive ? `+${sneaker.resale_premium_pct}%` : `${sneaker.resale_premium_pct}%`}
                    </span>
                  )}
                </div>

                {/* Info */}
                <p className="text-xs font-semibold uppercase tracking-wider text-indigo-400">
                  {sneaker.brand || 'Unbranded'}
                </p>
                <h4 className="mt-1 line-clamp-1 text-sm font-bold text-white group-hover:text-indigo-300 transition-colors">
                  {sneaker.name}
                </h4>
                <p className="mt-0.5 text-[11px] font-mono text-slate-500">ID: {sneaker.product_id}</p>

                {/* Price Bar */}
                <div className="mt-4 flex items-baseline justify-between border-t border-slate-800/80 pt-3">
                  <div>
                    <span className="text-[10px] uppercase tracking-wider text-slate-400">Latest Price</span>
                    <p className="text-lg font-extrabold text-white">
                      {sneaker.latest_price ? `$${sneaker.latest_price.toFixed(2)}` : 'N/A'}
                    </p>
                  </div>
                  {sneaker.retail_price && (
                    <div className="text-right">
                      <span className="text-[10px] uppercase tracking-wider text-slate-400">Retail</span>
                      <p className="text-xs font-semibold text-slate-400 line-through">
                        ${sneaker.retail_price.toFixed(2)}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* TABLE VIEW */
        <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60 shadow-xl backdrop-blur-md">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="border-b border-slate-800 bg-slate-950/70 text-xs uppercase tracking-wider text-slate-400">
                <tr>
                  <th className="px-6 py-4">Sneaker</th>
                  <th className="px-6 py-4">Brand</th>
                  <th className="px-6 py-4">Retail</th>
                  <th className="px-6 py-4">Latest Price</th>
                  <th className="px-6 py-4">Resale Premium</th>
                  <th className="px-6 py-4">Snapshots</th>
                  <th className="px-6 py-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {data.items.map((sneaker) => {
                  const hasPremium = sneaker.resale_premium_pct !== null;
                  const isPositive = (sneaker.resale_premium_pct ?? 0) >= 0;

                  return (
                    <tr
                      key={sneaker.id}
                      onClick={() => onSelectProduct(sneaker.product_id)}
                      className="cursor-pointer transition-colors hover:bg-slate-800/40"
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center space-x-3">
                          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-slate-950 p-1 border border-slate-800">
                            {sneaker.image_url ? (
                              <img src={sneaker.image_url} alt="" className="h-full w-full object-contain" />
                            ) : (
                              <span>👟</span>
                            )}
                          </div>
                          <div>
                            <p className="font-bold text-white hover:text-indigo-300">{sneaker.name}</p>
                            <p className="text-xs font-mono text-slate-400">{sneaker.product_id}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 font-medium text-slate-300">{sneaker.brand || 'N/A'}</td>
                      <td className="px-6 py-4 font-mono text-slate-400">
                        {sneaker.retail_price ? `$${sneaker.retail_price.toFixed(2)}` : 'N/A'}
                      </td>
                      <td className="px-6 py-4 font-bold text-white font-mono">
                        {sneaker.latest_price ? `$${sneaker.latest_price.toFixed(2)}` : 'N/A'}
                      </td>
                      <td className="px-6 py-4">
                        {hasPremium ? (
                          <span
                            className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-bold border ${
                              isPositive
                                ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400'
                                : 'border-rose-500/30 bg-rose-500/10 text-rose-400'
                            }`}
                          >
                            {isPositive ? `+${sneaker.resale_premium_pct}%` : `${sneaker.resale_premium_pct}%`}
                          </span>
                        ) : (
                          <span className="text-slate-600">—</span>
                        )}
                      </td>
                      <td className="px-6 py-4 font-mono text-slate-400">{sneaker.snapshot_count}</td>
                      <td className="px-6 py-4 text-right">
                        <span className="text-xs font-semibold text-indigo-400 hover:text-indigo-300">
                          Inspect →
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Pagination Controls */}
      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between rounded-2xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-md">
          <p className="text-xs text-slate-400">
            Showing Page <span className="font-bold text-white">{data.page}</span> of{' '}
            <span className="font-bold text-white">{data.total_pages}</span> ({data.total} total products)
          </p>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="rounded-xl border border-slate-800 bg-slate-950 px-3.5 py-1.5 text-xs font-semibold text-slate-300 hover:bg-slate-800 disabled:opacity-40 transition-all"
            >
              ← Previous
            </button>
            <button
              onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
              disabled={page >= data.total_pages}
              className="rounded-xl border border-slate-800 bg-slate-950 px-3.5 py-1.5 text-xs font-semibold text-slate-300 hover:bg-slate-800 disabled:opacity-40 transition-all"
            >
              Next →
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
