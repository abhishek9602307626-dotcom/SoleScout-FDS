import React from 'react';
import { PageId } from '../../types';
import {
  DashboardIcon,
  ProductsIcon,
  CompareIcon,
  TrendsIcon,
  BrandsIcon,
  StatsIcon,
  DataQualityIcon,
  AboutIcon,
} from '../common/Icons';

interface SidebarProps {
  currentPage: PageId;
  onNavigate: (page: PageId) => void;
  demoMode: boolean;
  onToggleDemo: (enabled: boolean) => void;
  isOpen: boolean;
  onClose: () => void;
}

interface NavItem {
  id: PageId;
  label: string;
  badge?: string;
  icon: React.ReactNode;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onNavigate,
  demoMode,
  onToggleDemo,
  isOpen,
  onClose,
}) => {
  const navItems: NavItem[] = [
    { id: 'dashboard', label: 'Dashboard', icon: <DashboardIcon /> },
    { id: 'products', label: 'Products', icon: <ProductsIcon /> },
    { id: 'product-details', label: 'Product Details', icon: <ProductsIcon /> },
    { id: 'compare', label: 'Compare', icon: <CompareIcon /> },
    { id: 'price-trends', label: 'Price Trends', icon: <TrendsIcon /> },
    { id: 'brand-analytics', label: 'Brand Analytics', icon: <BrandsIcon /> },
    { id: 'statistical-analysis', label: 'Statistical Analysis', badge: 'FDS', icon: <StatsIcon /> },
    { id: 'data-quality', label: 'Data Quality', icon: <DataQualityIcon /> },
    { id: 'about', label: 'About Project', icon: <AboutIcon /> },
  ];

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
        />
      )}

      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 flex w-72 flex-col border-r border-slate-800/80 bg-slate-950/95 p-5 shadow-2xl backdrop-blur-xl transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand / Logo */}
        <div className="flex items-center justify-between pb-6 border-b border-slate-800/80">
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => onNavigate('dashboard')}>
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-500 shadow-lg shadow-indigo-500/25">
              <span className="text-xl">👟</span>
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-1.5">
                SoleScout
                <span className="text-[10px] font-semibold tracking-wider text-indigo-400 bg-indigo-500/10 px-1.5 py-0.5 rounded border border-indigo-500/20">FDS</span>
              </h1>
              <p className="text-[11px] font-medium text-slate-400">Price Intelligence & Analytics</p>
            </div>
          </div>
        </div>

        {/* Navigation list */}
        <div className="flex-1 overflow-y-auto py-5 space-y-1">
          <p className="px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400">Analytics Suite</p>
          {navItems.map((item) => {
            const isActive = currentPage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  onNavigate(item.id);
                  onClose();
                }}
                className={`group flex w-full items-center justify-between rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                    : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <span className={`${isActive ? 'text-white' : 'text-slate-400 group-hover:text-slate-300'}`}>
                    {item.icon}
                  </span>
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span
                    className={`rounded-md px-1.5 py-0.5 text-[10px] font-bold ${
                      isActive
                        ? 'bg-white/20 text-white'
                        : 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Demo Mode Switch & Academic Tag */}
        <div className="border-t border-slate-800/80 pt-4 space-y-3">
          <div className="flex items-center justify-between rounded-xl bg-slate-900/60 p-3 border border-slate-800">
            <div>
              <p className="text-xs font-semibold text-slate-200">Include Demo Data</p>
              <p className="text-[10px] text-slate-400">Multi-brand sample snapshots</p>
            </div>
            <button
              onClick={() => onToggleDemo(!demoMode)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
                demoMode ? 'bg-indigo-600' : 'bg-slate-700'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  demoMode ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          <div className="rounded-xl bg-gradient-to-br from-slate-900 to-indigo-950/30 p-3 border border-indigo-500/20 text-center">
            <p className="text-[11px] font-semibold text-indigo-300">Fundamentals of Data Science</p>
            <p className="text-[10px] text-slate-400 mt-0.5">College Project • Semester Academic Build</p>
          </div>
        </div>
      </aside>
    </>
  );
};
