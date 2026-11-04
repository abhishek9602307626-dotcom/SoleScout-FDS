import React from 'react';

export const AboutPage: React.FC = () => {
  const steps = [
    { title: '1. SoleScout Public API', desc: 'Queries live retailer stock and secondary sneaker pricing via OpenAPI 3.1 endpoints.' },
    { title: '2. Python Data Collector', desc: 'Multi-query, multi-page asynchronous collector saving immutable raw JSON snapshots.' },
    { title: '3. Data Cleaning Pipeline', desc: 'Standardizes canonical brand names, verifies ISO dates, handles missing values, and checks Tukey IQR outliers.' },
    { title: '4. SQLite Historical Database', desc: 'Enforces UNIQUE(product_id, collection_date) to preserve longitudinal price time-series.' },
    { title: '5. Scientific Analytics Engine', desc: 'NumPy, Pandas & SciPy power One-Way ANOVA, OLS linear regression, and descriptive metrics.' },
    { title: '6. FastAPI REST Backend', desc: 'Pydantic v2 validated endpoints serving CORS-secured JSON models to the web frontend.' },
    { title: '7. React SaaS Dashboard', desc: 'Modern TypeScript, Tailwind CSS & Recharts client for interactive academic visualization.' },
  ];

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Hero Card */}
      <div className="rounded-3xl border border-indigo-500/20 bg-gradient-to-br from-slate-900 via-indigo-950/30 to-slate-900 p-8 shadow-2xl backdrop-blur-xl">
        <span className="rounded-md border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs font-bold text-indigo-400 uppercase tracking-wider">
          Fundamentals of Data Science (FDS) College Project
        </span>
        <h1 className="mt-4 text-3xl font-black tracking-tight text-white sm:text-4xl">
          SoleScout Sneaker Price Intelligence & Analytics
        </h1>
        <p className="mt-3 text-sm text-slate-300 leading-relaxed max-w-3xl">
          SoleScout is an end-to-end full-stack data science system designed to collect, clean, preserve, and scientifically analyze secondary market sneaker price fluctuations.
          Built as a collegiate FDS term project demonstrating reproducible ETL, rigorous statistical hypothesis testing, and professional full-stack web engineering.
        </p>
      </div>

      {/* Architecture Pipeline */}
      <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-8 shadow-xl backdrop-blur-md">
        <h2 className="text-xl font-bold text-white">Full-Stack Data Flow Architecture</h2>
        <p className="text-xs text-slate-400 mt-1">End-to-end data pipeline from public API ingestion to frontend dashboard</p>

        <div className="mt-8 relative border-l-2 border-indigo-500/40 ml-4 pl-6 space-y-6">
          {steps.map((step, idx) => (
            <div key={idx} className="relative">
              <span className="absolute -left-[35px] top-0 flex h-6 w-6 items-center justify-center rounded-full border border-indigo-500 bg-slate-950 text-[10px] font-bold text-indigo-400">
                {idx + 1}
              </span>
              <h3 className="text-sm font-bold text-white">{step.title}</h3>
              <p className="mt-1 text-xs text-slate-400 leading-relaxed">{step.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Integrity & Compliance Rules */}
      <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-8 shadow-xl backdrop-blur-md">
        <h2 className="text-xl font-bold text-white">Non-Negotiable Data Integrity Rules</h2>
        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400">No Secret Exposure</h4>
            <p className="mt-1 text-xs text-slate-400">API keys reside exclusively in backend .env and are never sent to the browser or logged in responses.</p>
          </div>
          <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400">No Synthetic Real Data</h4>
            <p className="mt-1 text-xs text-slate-400">Missing fields are kept as SQL NULL (None). Fake ratings or sales are strictly forbidden.</p>
          </div>
          <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400">Preserved Snapshots</h4>
            <p className="mt-1 text-xs text-slate-400">UNIQUE(product_id, collection_date) prevents overwriting historical snapshots for longitudinal modeling.</p>
          </div>
          <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400">Non-Dogmatic Hypothesis Decisions</h4>
            <p className="mt-1 text-xs text-slate-400">Falsification principle: failing to reject H0 never claims that the null hypothesis is proven true.</p>
          </div>
        </div>
      </div>

      {/* Technology Stack Grid */}
      <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-8 shadow-xl backdrop-blur-md">
        <h2 className="text-xl font-bold text-white">Technology Stack</h2>
        <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4 text-xs font-medium">
          <div className="rounded-xl border border-slate-800 bg-slate-950 p-3 text-slate-300">
            <strong className="block text-indigo-400">Python 3.11+</strong> Data Engine
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-950 p-3 text-slate-300">
            <strong className="block text-indigo-400">FastAPI</strong> High-Perf REST API
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-950 p-3 text-slate-300">
            <strong className="block text-indigo-400">Pandas & NumPy</strong> Matrix Operations
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-950 p-3 text-slate-300">
            <strong className="block text-indigo-400">SciPy Stats</strong> One-Way ANOVA & OLS
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-950 p-3 text-slate-300">
            <strong className="block text-indigo-400">SQLite3</strong> Relational Store
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-950 p-3 text-slate-300">
            <strong className="block text-indigo-400">React 18 & Vite</strong> UI Architecture
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-950 p-3 text-slate-300">
            <strong className="block text-indigo-400">TypeScript</strong> Strict Type Safety
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-950 p-3 text-slate-300">
            <strong className="block text-indigo-400">Tailwind & Recharts</strong> SaaS Analytics UI
          </div>
        </div>
      </div>
    </div>
  );
};
