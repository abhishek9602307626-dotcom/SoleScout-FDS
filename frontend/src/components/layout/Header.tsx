import React from 'react';
import { PageId } from '../../types';
import { RefreshIcon } from '../common/Icons';

interface HeaderProps {
  currentPage: PageId;
  apiConnected: boolean | null;
  demoMode: boolean;
  onRefresh: () => void;
  isRefreshing: boolean;
  onOpenMobileMenu: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentPage,
  apiConnected,
  demoMode,
  onRefresh,
  isRefreshing,
  onOpenMobileMenu,
}) => {
  const titles: Record<PageId, { title: string; subtitle: string }> = {
    dashboard: {
      title: 'Executive Analytics Dashboard',
      subtitle: 'Macro market trends, pricing distributions & cross-brand performance overview',
    },
    products: {
      title: 'Sneaker Products Catalog',
      subtitle: 'Search, filter, inspect and track individual sneaker models and resale premiums',
    },
    'product-details': {
      title: 'Product Deep-Dive & Time-Series',
      subtitle: 'Historical volatility, snapshot logs, platform comparisons & outlier analysis',
    },
    compare: {
      title: 'Cross-Product Price Comparison',
      subtitle: 'Side-by-side spec comparison, pricing spread & historical value trajectory',
    },
    'price-trends': {
      title: 'Longitudinal Price Trends',
      subtitle: 'Ordinary Least Squares (OLS) linear regression modeling over collection timelines',
    },
    'brand-analytics': {
      title: 'Brand-Wise Cross-Sectional Intelligence',
      subtitle: 'Parametric and non-parametric statistics grouped by canonical footwear brand',
    },
    'statistical-analysis': {
      title: 'FDS Hypothesis Testing & Statistical Models',
      subtitle: 'Formal scientific evaluations: One-Way ANOVA, correlation, regression & distribution shape',
    },
    'data-quality': {
      title: 'Data Cleaning & Pipeline Audit',
      subtitle: 'Stage 4 data verification: duplicate resolution, missing values, anomaly detection & ETL logs',
    },
    about: {
      title: 'About SoleScout Intelligence',
      subtitle: 'Full-stack architectural blueprint, scientific methodologies & data science pipeline',
    },
  };

  const meta = titles[currentPage] || { title: 'SoleScout Analytics', subtitle: 'Sneaker Intelligence' };

  return (
    <header className="sticky top-0 z-30 flex h-20 items-center justify-between border-b border-slate-800/80 bg-slate-950/80 px-6 backdrop-blur-xl">
      <div className="flex items-center space-x-4">
        {/* Mobile menu trigger */}
        <button
          onClick={onOpenMobileMenu}
          className="rounded-xl border border-slate-800 bg-slate-900 p-2 text-slate-400 hover:text-white lg:hidden"
          aria-label="Open navigation menu"
        >
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <div>
          <h2 className="text-xl font-bold tracking-tight text-white">{meta.title}</h2>
          <p className="hidden text-xs text-slate-400 sm:block">{meta.subtitle}</p>
        </div>
      </div>

      <div className="flex items-center space-x-3">
        {/* Demo Mode Badge */}
        {demoMode && (
          <span className="hidden sm:inline-flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-300">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" />
            Sample Data Active
          </span>
        )}

        {/* API Status Badge */}
        <div
          className={`flex items-center space-x-2 rounded-xl border px-3 py-1.5 text-xs font-medium backdrop-blur-md ${
            apiConnected === true
              ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
              : apiConnected === false
              ? 'border-rose-500/30 bg-rose-500/10 text-rose-300'
              : 'border-slate-800 bg-slate-900 text-slate-400'
          }`}
        >
          <span
            className={`h-2 w-2 rounded-full ${
              apiConnected === true
                ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]'
                : apiConnected === false
                ? 'bg-rose-400 shadow-[0_0_8px_rgba(251,113,133,0.8)]'
                : 'bg-slate-400 animate-pulse'
            }`}
          />
          <span className="hidden sm:inline">
            {apiConnected === true ? 'FastAPI Connected' : apiConnected === false ? 'API Offline' : 'Connecting...'}
          </span>
        </div>

        {/* Refresh Action */}
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-800 bg-slate-900 text-slate-400 transition-all hover:border-slate-700 hover:text-white disabled:opacity-50"
          title="Refresh dataset from backend"
        >
          <RefreshIcon className={`h-4 w-4 ${isRefreshing ? 'animate-spin text-indigo-400' : ''}`} />
        </button>
      </div>
    </header>
  );
};
