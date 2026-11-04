import React, { useState, useEffect } from 'react';
import { PageId } from './types';
import { api } from './services/api';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';

import { DashboardPage } from './pages/DashboardPage';
import { ProductsPage } from './pages/ProductsPage';
import { ProductDetailPage } from './pages/ProductDetailPage';
import { ComparePage } from './pages/ComparePage';
import { PriceTrendsPage } from './pages/PriceTrendsPage';
import { BrandAnalyticsPage } from './pages/BrandAnalyticsPage';
import { StatisticalAnalysisPage } from './pages/StatisticalAnalysisPage';
import { DataQualityPage } from './pages/DataQualityPage';
import { AboutPage } from './pages/AboutPage';

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<PageId>('dashboard');
  const [selectedProductId, setSelectedProductId] = useState<string | null>(null);
  const [compareProductId, setCompareProductId] = useState<string | null>(null);
  const [demoMode, setDemoMode] = useState<boolean>(true);
  const [apiConnected, setApiConnected] = useState<boolean | null>(null);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);
  const [refreshTrigger, setRefreshTrigger] = useState<number>(0);

  // Check backend health on initial mount
  useEffect(() => {
    const checkApi = async () => {
      try {
        const res = await api.getHealth();
        setApiConnected(res.status === 'healthy');
      } catch {
        setApiConnected(false);
      }
    };
    checkApi();
    const interval = setInterval(checkApi, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      const res = await api.getHealth();
      setApiConnected(res.status === 'healthy');
      setRefreshTrigger((prev) => prev + 1);
    } catch {
      setApiConnected(false);
    } finally {
      setTimeout(() => setIsRefreshing(false), 500);
    }
  };

  const handleSelectProduct = (productId: string) => {
    setSelectedProductId(productId);
    setCurrentPage('product-details');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleCompareProduct = (productId: string) => {
    setCompareProductId(productId);
    setCurrentPage('compare');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 antialiased font-sans">
      {/* Sidebar Navigation */}
      <Sidebar
        currentPage={currentPage}
        onNavigate={(page) => {
          setCurrentPage(page);
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }}
        demoMode={demoMode}
        onToggleDemo={(enabled) => setDemoMode(enabled)}
        isOpen={mobileMenuOpen}
        onClose={() => setMobileMenuOpen(false)}
      />

      {/* Main Content Area */}
      <div className="lg:pl-72 flex min-h-screen flex-col">
        {/* Top Header */}
        <Header
          currentPage={currentPage}
          apiConnected={apiConnected}
          demoMode={demoMode}
          onRefresh={handleRefresh}
          isRefreshing={isRefreshing}
          onOpenMobileMenu={() => setMobileMenuOpen(true)}
        />

        {/* Dynamic Page Body */}
        <main className="flex-1 p-6 md:p-8 max-w-7xl mx-auto w-full" key={refreshTrigger}>
          {currentPage === 'dashboard' && (
            <DashboardPage
              demoMode={demoMode}
              onNavigate={(page) => setCurrentPage(page)}
              onSelectProduct={handleSelectProduct}
            />
          )}

          {currentPage === 'products' && (
            <ProductsPage
              demoMode={demoMode}
              onSelectProduct={handleSelectProduct}
              onNavigate={(page) => setCurrentPage(page)}
            />
          )}

          {currentPage === 'product-details' && (
            <ProductDetailPage
              productId={selectedProductId}
              demoMode={demoMode}
              onNavigate={(page) => setCurrentPage(page)}
              onCompareProduct={handleCompareProduct}
            />
          )}

          {currentPage === 'compare' && (
            <ComparePage
              initialProductId={compareProductId}
              demoMode={demoMode}
            />
          )}

          {currentPage === 'price-trends' && (
            <PriceTrendsPage demoMode={demoMode} />
          )}

          {currentPage === 'brand-analytics' && (
            <BrandAnalyticsPage demoMode={demoMode} />
          )}

          {currentPage === 'statistical-analysis' && (
            <StatisticalAnalysisPage demoMode={demoMode} />
          )}

          {currentPage === 'data-quality' && (
            <DataQualityPage />
          )}

          {currentPage === 'about' && (
            <AboutPage />
          )}
        </main>

        {/* Institutional Footer */}
        <footer className="border-t border-slate-900 bg-slate-950/90 py-6 px-8 text-center text-xs text-slate-500">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 max-w-7xl mx-auto">
            <p>
              SoleScout • Fundamentals of Data Science (FDS) College Project
            </p>
            <div className="flex items-center space-x-4">
              <span>FastAPI Backend v2.0.0</span>
              <span>•</span>
              <span>SciPy Statistical Engine</span>
              <span>•</span>
              <button
                onClick={() => setCurrentPage('about')}
                className="text-indigo-400 hover:text-indigo-300 transition-colors"
              >
                Project Blueprint →
              </button>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default App;
