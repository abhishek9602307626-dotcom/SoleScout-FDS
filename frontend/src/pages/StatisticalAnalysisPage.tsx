import React, { useEffect, useState } from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  BarChart,
  Bar,
  Line,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import { api } from '../services/api';
import { AnovaResponse, CorrelationResponse } from '../types';
import { LoadingSpinner, ErrorAlert } from '../components/common/Feedback';

interface StatisticalAnalysisPageProps {
  demoMode: boolean;
}

export const StatisticalAnalysisPage: React.FC<StatisticalAnalysisPageProps> = ({ demoMode }) => {
  const [anova, setAnova] = useState<AnovaResponse | null>(null);
  const [corr, setCorr] = useState<CorrelationResponse | null>(null);
  const [alpha, setAlpha] = useState<number>(0.05);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHypotheses = async () => {
    try {
      setLoading(true);
      setError(null);
      const [anovaRes, corrRes] = await Promise.all([
        api.getAnova(alpha, demoMode),
        api.getCorrelation(alpha, demoMode),
      ]);
      setAnova(anovaRes);
      setCorr(corrRes);
    } catch (err: any) {
      setError(err.message || 'Failed to compute scientific hypotheses.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHypotheses();
  }, [alpha, demoMode]);

  if (loading) {
    return <LoadingSpinner message="Executing SciPy One-Way ANOVA, OLS regression, and hypothesis models..." />;
  }

  if (error) {
    return <ErrorAlert error={error} onRetry={fetchHypotheses} />;
  }

  const h1 = anova;
  const h2 = corr?.price_trend_hypothesis;
  const h3 = corr?.price_rating_hypothesis;
  const priceDist = corr?.price_distribution;
  const brandComp = corr?.brand_comparison || [];
  const boxplots = anova?.brand_boxplots || [];
  const scatterPoints = h2?.scatter_points || [];

  // Determine global price bounds for the visual box plots
  const allPrices = boxplots.flatMap((b) => [b.min_whisker, b.max_whisker]);
  const minPriceScale = allPrices.length > 0 ? Math.max(0, Math.floor(Math.min(...allPrices) / 20) * 20 - 20) : 0;
  const maxPriceScale = allPrices.length > 0 ? Math.ceil(Math.max(...allPrices) / 20) * 20 + 20 : 300;
  const priceRange = maxPriceScale - minPriceScale || 1;

  return (
    <div className="space-y-10 pb-16">
      {/* ------------------------------------------------------------------- */}
      {/* PAGE HEADER & CONTROLS */}
      {/* ------------------------------------------------------------------- */}
      <div className="rounded-3xl border border-indigo-500/20 bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 p-6 shadow-2xl backdrop-blur-xl">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="rounded-md border border-indigo-500/30 bg-indigo-500/10 px-2.5 py-1 text-xs font-bold uppercase tracking-wider text-indigo-400">
                Fundamentals of Data Science (FDS)
              </span>
              <span className="rounded-md border border-sky-500/30 bg-sky-500/10 px-2.5 py-1 text-xs font-bold uppercase tracking-wider text-sky-400">
                Engineering Hypothesis Engine
              </span>
            </div>
            <h2 className="mt-2 text-2xl font-black text-white sm:text-3xl">
              Scientific Hypothesis Testing & Analytics
            </h2>
            <p className="mt-1 text-xs leading-relaxed text-slate-400 max-w-3xl">
              Strict formal parametric and non-parametric testing computed live using <code className="text-indigo-300 font-mono">scipy.stats</code>.
              All conclusions strictly observe Karl Popper&apos;s falsification principle: failing to reject the null hypothesis
              indicates insufficient evidence, never that the null hypothesis is proven true.
            </p>
          </div>

          <div className="flex items-center space-x-3 rounded-2xl border border-slate-800 bg-slate-950/80 p-3 self-start sm:self-auto">
            <span className="text-xs font-semibold text-slate-300">Significance Level (α):</span>
            <select
              value={alpha}
              onChange={(e) => setAlpha(Number(e.target.value))}
              className="rounded-xl border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs font-bold text-indigo-400 focus:outline-none"
            >
              <option value={0.01}>α = 0.01 (99% Confidence)</option>
              <option value={0.05}>α = 0.05 (95% Confidence - Standard)</option>
              <option value={0.10}>α = 0.10 (90% Confidence)</option>
            </select>
          </div>
        </div>

        {/* Global Scientific Framework Banner */}
        <div className="mt-5 grid grid-cols-1 gap-3 rounded-2xl border border-slate-800/80 bg-slate-950/60 p-4 sm:grid-cols-3">
          <div className="text-xs">
            <span className="font-bold text-slate-400">Formal Decision Rule:</span>
            <p className="mt-0.5 text-slate-300">
              <span className="font-mono text-emerald-400">p &lt; α</span> → Reject H₀ | <span className="font-mono text-amber-400">p ≥ α</span> → Fail to reject H₀
            </p>
          </div>
          <div className="text-xs">
            <span className="font-bold text-slate-400">Non-Dogmatic Mandate:</span>
            <p className="mt-0.5 text-slate-300 italic">
              Absence of evidence is not evidence of absence. H₀ is never proven true.
            </p>
          </div>
          <div className="text-xs">
            <span className="font-bold text-slate-400">Active Significance Threshold:</span>
            <p className="mt-0.5 font-mono font-bold text-indigo-400">α = {alpha} (Critical p-cutoff: {alpha})</p>
          </div>
        </div>
      </div>

      {/* ------------------------------------------------------------------- */}
      {/* HYPOTHESIS 1: BRAND VS PRICE (ONE-WAY ANOVA) */}
      {/* ------------------------------------------------------------------- */}
      {h1 && (
        <section className="space-y-6 rounded-3xl border border-slate-800 bg-slate-900/60 p-6 shadow-2xl backdrop-blur-md">
          {/* 1. Header with Title and Decision Pill */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
            <div>
              <span className="rounded-md border border-indigo-500/30 bg-indigo-500/10 px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wider text-indigo-400">
                FDS Hypothesis 1
              </span>
              <h3 className="mt-1 text-xl font-black text-white">
                Brand Influence on Sneaker Market Price (One-Way ANOVA)
              </h3>
              <p className="text-xs text-slate-400">
                Scientific Question: Does brand prestige and positioning produce statistically significant mean price differences?
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span
                className={`rounded-full border px-4 py-1.5 text-xs font-black tracking-wide ${
                  h1.decision === 'Reject H0'
                    ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400 shadow-lg shadow-emerald-500/10'
                    : h1.decision === 'Fail to reject H0'
                    ? 'border-amber-500/40 bg-amber-500/10 text-amber-400 shadow-lg shadow-amber-500/10'
                    : 'border-slate-700 bg-slate-800 text-slate-400'
                }`}
              >
                Decision: {h1.decision}
              </span>
            </div>
          </div>

          {/* 2. Formal Hypotheses Cards (H0 & H1) */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-4">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-black uppercase tracking-wider text-slate-400">
                  Null Hypothesis (H₀)
                </span>
                <span className="font-mono text-[11px] text-slate-400">μ₁ = μ₂ = ... = μₖ</span>
              </div>
              <p className="mt-2 text-xs font-medium leading-relaxed text-slate-200">
                {h1.null_hypothesis}
              </p>
              <p className="mt-2 text-[11px] text-slate-400">
                Assumes sneaker brand has zero systematic effect; all observed price variance is purely random noise.
              </p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-4">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-black uppercase tracking-wider text-indigo-400">
                  Alternative Hypothesis (H₁)
                </span>
                <span className="font-mono text-[11px] text-indigo-400">∃ i, j : μᵢ ≠ μⱼ</span>
              </div>
              <p className="mt-2 text-xs font-medium leading-relaxed text-slate-200">
                {h1.alternative_hypothesis}
              </p>
              <p className="mt-2 text-[11px] text-slate-400">
                Asserts that at least one brand has a statistically significantly different average price.
              </p>
            </div>
          </div>

          {/* 3. Numerical Metrics Grid */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
            <div className="rounded-2xl border border-slate-800 bg-slate-950/90 p-4">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Statistical Test</span>
              <p className="mt-1 text-sm font-bold text-white">{h1.test_type}</p>
              <p className="text-[10px] font-mono text-slate-400">scipy.stats.f_oneway</p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950/90 p-4">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Significance Level (α)</span>
              <p className="mt-1 text-xl font-black text-indigo-400">{h1.alpha}</p>
              <p className="text-[10px] text-slate-400">95% Confidence</p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950/90 p-4">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">F-Statistic</span>
              <p className="mt-1 text-xl font-black text-white">
                {h1.f_statistic !== null ? h1.f_statistic.toFixed(4) : 'N/A'}
              </p>
              <p className="text-[10px] text-slate-400">Between / Within Var</p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950/90 p-4">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">p-value</span>
              <p className="mt-1 text-xl font-black text-sky-400">
                {h1.p_value !== null ? (h1.p_value < 0.0001 ? '< 0.0001' : h1.p_value.toFixed(6)) : 'N/A'}
              </p>
              <p className="text-[10px] font-mono text-slate-400">
                {h1.p_value !== null ? (h1.p_value < h1.alpha ? 'p < α (Reject H₀)' : 'p ≥ α (Fail to reject)') : 'Insufficient'}
              </p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950/90 p-4">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Brands Evaluated</span>
              <p className="mt-1 text-xl font-black text-emerald-400">{h1.brands_evaluated.length}</p>
              <p className="text-[10px] text-slate-400">
                {Object.values(h1.brand_sample_sizes).reduce((a, b) => a + b, 0)} total snapshots
              </p>
            </div>
          </div>

          {/* 4. Interpretations: Scientific & 2nd-Year Engineering */}
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <div className="rounded-2xl border border-slate-800 bg-slate-950/90 p-4">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                Scientific Statistical Conclusion
              </span>
              <p className="mt-2 text-xs leading-relaxed text-slate-300 font-sans">
                {h1.interpretation}
              </p>
            </div>

            <div className="rounded-2xl border border-indigo-500/30 bg-indigo-950/20 p-4">
              <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-400">
                2nd-Year Engineering Analogy: Signal-to-Noise Ratio (SNR)
              </span>
              <p className="mt-2 text-xs leading-relaxed text-indigo-200/90 font-sans">
                {h1.engineering_explanation ||
                  "Think of One-Way ANOVA as calculating the Signal-to-Noise Ratio (SNR) in an operational amplifier. " +
                  "The 'Signal' is the variance between brand means (brand pricing power). " +
                  "The 'Noise' is the random variance within each brand. " +
                  "When F is large and p < 0.05, the brand signal significantly exceeds random noise."}
              </p>
            </div>
          </div>

          {/* 5. CHART 1: BRAND PRICE BOX PLOT */}
          <div className="space-y-4 rounded-2xl border border-slate-800/80 bg-slate-950/70 p-5">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div>
                <h4 className="text-sm font-bold text-white flex items-center gap-2">
                  <span>📊</span> Brand Price Distribution Box Plot (Five-Number Summary)
                </h4>
                <p className="text-xs text-slate-400">
                  Visualizes Min Whisker, Q₁ (25%), Median Q₂ (50%), Q₃ (75%), Max Whisker, and Mean (♦) for each evaluated brand.
                </p>
              </div>
              <div className="flex items-center gap-4 text-[11px] text-slate-400">
                <span className="flex items-center gap-1.5">
                  <span className="h-2.5 w-6 rounded-sm bg-indigo-500/60 border border-indigo-400" /> IQR (Q₁ to Q₃)
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-3 w-1 bg-white rounded-full" /> Median
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-amber-400" /> Mean (♦)
                </span>
              </div>
            </div>

            {boxplots.length === 0 ? (
              <p className="py-6 text-center text-xs text-slate-500">
                Insufficient data to render box plots. Collect products across multiple brands.
              </p>
            ) : (
              <div className="space-y-5 pt-2">
                {boxplots.map((bp) => {
                  const leftWhiskerPct = Math.max(0, ((bp.min_whisker - minPriceScale) / priceRange) * 100);
                  const rightWhiskerPct = Math.min(100, ((bp.max_whisker - minPriceScale) / priceRange) * 100);
                  const q1Pct = Math.max(0, ((bp.q1 - minPriceScale) / priceRange) * 100);
                  const q3Pct = Math.min(100, ((bp.q3 - minPriceScale) / priceRange) * 100);
                  const medianPct = Math.max(0, ((bp.median - minPriceScale) / priceRange) * 100);
                  const meanPct = Math.max(0, ((bp.mean - minPriceScale) / priceRange) * 100);
                  const boxWidthPct = Math.max(1, q3Pct - q1Pct);

                  return (
                    <div key={bp.brand} className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-bold text-white flex items-center gap-2">
                          <span className="text-indigo-400 font-mono">[{bp.brand}]</span>
                          <span className="text-[11px] text-slate-400 font-normal">n = {bp.sample_size}</span>
                        </span>
                        <div className="flex items-center gap-3 font-mono text-[11px] text-slate-300">
                          <span>Min: ${bp.min_whisker}</span>
                          <span className="text-indigo-300 font-semibold">Q₁: ${bp.q1}</span>
                          <span className="text-white font-bold">Med: ${bp.median}</span>
                          <span className="text-indigo-300 font-semibold">Q₃: ${bp.q3}</span>
                          <span>Max: ${bp.max_whisker}</span>
                          <span className="text-amber-400 font-bold">Mean: ${bp.mean}</span>
                        </div>
                      </div>

                      {/* Visual Box & Whisker Track */}
                      <div className="relative h-8 w-full rounded-xl bg-slate-900 border border-slate-800/80 px-2 flex items-center">
                        {/* Whisker Line */}
                        <div
                          className="absolute h-0.5 bg-slate-600 rounded-full"
                          style={{
                            left: `${leftWhiskerPct}%`,
                            width: `${Math.max(1, rightWhiskerPct - leftWhiskerPct)}%`,
                          }}
                        />

                        {/* Min Whisker End Cap */}
                        <div
                          className="absolute h-3.5 w-0.5 bg-slate-400 rounded-full"
                          style={{ left: `${leftWhiskerPct}%`, transform: 'translateX(-50%)' }}
                        />

                        {/* Max Whisker End Cap */}
                        <div
                          className="absolute h-3.5 w-0.5 bg-slate-400 rounded-full"
                          style={{ left: `${rightWhiskerPct}%`, transform: 'translateX(-50%)' }}
                        />

                        {/* IQR Box (Q1 to Q3) */}
                        <div
                          className="absolute h-6 rounded-md border border-indigo-400/80 bg-indigo-600/40 shadow-inner backdrop-blur-sm"
                          style={{
                            left: `${q1Pct}%`,
                            width: `${boxWidthPct}%`,
                          }}
                        />

                        {/* Median Line */}
                        <div
                          className="absolute h-6 w-1 rounded-full bg-white shadow-md z-10"
                          style={{ left: `${medianPct}%`, transform: 'translateX(-50%)' }}
                          title={`Median: $${bp.median}`}
                        />

                        {/* Mean Marker */}
                        <div
                          className="absolute h-3 w-3 rotate-45 rounded-xs bg-amber-400 border border-amber-200 shadow-md z-10"
                          style={{ left: `${meanPct}%`, transform: 'translateX(-50%)' }}
                          title={`Mean: $${bp.mean}`}
                        />
                      </div>
                    </div>
                  );
                })}

                {/* Price Scale Ticks */}
                <div className="relative pt-1 border-t border-slate-800 text-[10px] font-mono text-slate-500 flex justify-between">
                  <span>${minPriceScale}</span>
                  <span>${Math.round(minPriceScale + priceRange * 0.25)}</span>
                  <span>${Math.round(minPriceScale + priceRange * 0.5)}</span>
                  <span>${Math.round(minPriceScale + priceRange * 0.75)}</span>
                  <span>${maxPriceScale}</span>
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {/* ------------------------------------------------------------------- */}
      {/* HYPOTHESIS 2: PRICE TREND OVER TIME (OLS REGRESSION) */}
      {/* ------------------------------------------------------------------- */}
      {h2 && (
        <section className="space-y-6 rounded-3xl border border-slate-800 bg-slate-900/60 p-6 shadow-2xl backdrop-blur-md">
          {/* 1. Header with Title and Decision Pill */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
            <div>
              <span className="rounded-md border border-indigo-500/30 bg-indigo-500/10 px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wider text-indigo-400">
                FDS Hypothesis 2
              </span>
              <h3 className="mt-1 text-xl font-black text-white">
                Longitudinal Price Trend Sensitivity to Collection Date
              </h3>
              <p className="text-xs text-slate-400">
                Scientific Question: Does sneaker market price drift predictably over time or remain stationary?
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span
                className={`rounded-full border px-4 py-1.5 text-xs font-black tracking-wide ${
                  h2.decision === 'Reject H0'
                    ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400 shadow-lg shadow-emerald-500/10'
                    : h2.decision === 'Fail to reject H0'
                    ? 'border-amber-500/40 bg-amber-500/10 text-amber-400 shadow-lg shadow-amber-500/10'
                    : 'border-slate-700 bg-slate-800 text-slate-400'
                }`}
              >
                Decision: {h2.decision}
              </span>
            </div>
          </div>

          {/* 2. Formal Hypotheses Cards (H0 & H1) */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-4">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-black uppercase tracking-wider text-slate-400">
                  Null Hypothesis (H₀)
                </span>
                <span className="font-mono text-[11px] text-slate-400">β = 0 (Slope is zero)</span>
              </div>
              <p className="mt-2 text-xs font-medium leading-relaxed text-slate-200">
                {h2.null_hypothesis}
              </p>
              <p className="mt-2 text-[11px] text-slate-400">
                Asserts that collection date has zero predictive relationship with price; observed daily changes are random fluctuations.
              </p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-4">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-black uppercase tracking-wider text-indigo-400">
                  Alternative Hypothesis (H₁)
                </span>
                <span className="font-mono text-[11px] text-indigo-400">β ≠ 0 (Non-zero slope)</span>
              </div>
              <p className="mt-2 text-xs font-medium leading-relaxed text-slate-200">
                {h2.alternative_hypothesis}
              </p>
              <p className="mt-2 text-[11px] text-slate-400">
                Asserts a statistically significant temporal trend (market appreciation or depreciation).
              </p>
            </div>
          </div>

          {/* 3. Numerical Metrics Grid */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
            <div className="rounded-2xl border border-slate-800 bg-slate-950/90 p-4">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Statistical Test</span>
              <p className="mt-1 text-sm font-bold text-white">OLS Regression & Pearson</p>
              <p className="text-[10px] font-mono text-slate-400">scipy.stats.linregress</p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950/90 p-4">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Slope (β) / Velocity</span>
              <p className="mt-1 text-xl font-black text-indigo-400">
                {h2.coefficient !== null ? `$${h2.coefficient.toFixed(4)}/d` : 'N/A'}
              </p>
              <p className="text-[10px] text-slate-400">dy/dt rate of change</p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950/90 p-4">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Pearson Correlation (r)</span>
              <p className="mt-1 text-xl font-black text-white">
                {h2.pearson_r !== null ? h2.pearson_r.toFixed(4) : 'N/A'}
              </p>
              <p className="text-[10px] font-mono text-slate-400">R² = {h2.r_squared !== null && h2.r_squared !== undefined ? h2.r_squared.toFixed(4) : 'N/A'}</p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950/90 p-4">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">p-value</span>
              <p className="mt-1 text-xl font-black text-sky-400">
                {h2.p_value !== null ? (h2.p_value < 0.0001 ? '< 0.0001' : h2.p_value.toFixed(4)) : 'N/A'}
              </p>
              <p className="text-[10px] font-mono text-slate-400">
                {h2.p_value !== null ? (h2.p_value < h2.alpha ? 'p < α (Reject H₀)' : 'p ≥ α (Fail to reject)') : 'Insufficient'}
              </p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950/90 p-4">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Sample Size</span>
              <p className="mt-1 text-xl font-black text-emerald-400">{h2.sample_size}</p>
              <p className="text-[10px] text-slate-400">Historical snapshots</p>
            </div>
          </div>

          {/* 4. Interpretations: Scientific & 2nd-Year Engineering */}
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <div className="rounded-2xl border border-slate-800 bg-slate-950/90 p-4">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                Scientific Statistical Conclusion
              </span>
              <p className="mt-2 text-xs leading-relaxed text-slate-300 font-sans">
                {h2.interpretation}
              </p>
            </div>

            <div className="rounded-2xl border border-indigo-500/30 bg-indigo-950/20 p-4">
              <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-400">
                2nd-Year Engineering Analogy: Kinematics & Velocity (dy/dt)
              </span>
              <p className="mt-2 text-xs leading-relaxed text-indigo-200/90 font-sans">
                {h2.engineering_explanation ||
                  "In physical dynamics, the regression slope (beta) is literally the price velocity dy/dt (change in dollars per day). " +
                  "If beta is near 0 and p >= 0.05, the market is in steady-state equilibrium (prices are stationary, analogous to a DC voltage with low-amplitude thermal jitter). " +
                  "If p < 0.05 and beta > 0, the market has positive momentum (appreciation); beta < 0 indicates market depreciation."}
              </p>
            </div>
          </div>

          {/* 5. CHARTS: SCATTER PLOT WITH REGRESSION / TREND LINE */}
          <div className="space-y-3 rounded-2xl border border-slate-800/80 bg-slate-950/70 p-5">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div>
                <h4 className="text-sm font-bold text-white flex items-center gap-2">
                  <span>📈</span> Scatter Plot & OLS Fitted Regression Line
                </h4>
                <p className="text-xs text-slate-400">
                  Individual price observations (scatter points) overlaid with the Ordinary Least Squares (OLS) fitted trend line.
                </p>
              </div>
              <div className="flex items-center gap-4 text-[11px] text-slate-400">
                <span className="flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-sky-400" /> Sneaker Observation
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-0.5 w-6 bg-indigo-400" /> OLS Linear Fit Line
                </span>
              </div>
            </div>

            {scatterPoints.length === 0 ? (
              <p className="py-12 text-center text-xs text-slate-500">
                Insufficient data to plot trend line. Collect products across multiple days.
              </p>
            ) : (
              <div className="h-72 w-full pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={scatterPoints} margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
                    <XAxis
                      dataKey="date"
                      stroke="#94a3b8"
                      fontSize={11}
                      tickLine={false}
                    />
                    <YAxis
                      stroke="#94a3b8"
                      fontSize={11}
                      tickLine={false}
                      domain={['auto', 'auto']}
                      tickFormatter={(v) => `$${v}`}
                    />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0].payload;
                          return (
                            <div className="rounded-xl border border-slate-800 bg-slate-900 p-3 shadow-xl text-xs">
                              <p className="font-bold text-white">{data.product_name}</p>
                              <p className="text-slate-400">{data.brand} • {data.date}</p>
                              <div className="mt-2 space-y-1 font-mono text-[11px]">
                                <p className="text-sky-400">Observed Price: <strong className="text-white">${data.price}</strong></p>
                                {data.fitted_price && (
                                  <p className="text-indigo-400">OLS Fitted Price: <strong>${data.fitted_price}</strong></p>
                                )}
                              </div>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Scatter
                      name="Observed Price"
                      dataKey="price"
                      fill="#38bdf8"
                    />
                    <Line
                      type="linear"
                      name="Fitted OLS Trend"
                      dataKey="fitted_price"
                      stroke="#818cf8"
                      strokeWidth={3}
                      dot={false}
                      activeDot={{ r: 6 }}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </section>
      )}

      {/* ------------------------------------------------------------------- */}
      {/* HYPOTHESIS 3: PRICE VS RATING (DATA SCIENCE INTEGRITY RULE) */}
      {/* ------------------------------------------------------------------- */}
      {h3 && (
        <section className="space-y-6 rounded-3xl border border-slate-800 bg-slate-900/60 p-6 shadow-2xl backdrop-blur-md">
          {/* 1. Header with Title and Status Pill */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
            <div>
              <span className="rounded-md border border-amber-500/30 bg-amber-500/10 px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wider text-amber-400">
                FDS Hypothesis 3
              </span>
              <h3 className="mt-1 text-xl font-black text-white">
                Correlation Between Sneaker Price and Product Rating
              </h3>
              <p className="text-xs text-slate-400">
                Scientific Question: Does market price exhibit a statistically significant correlation with consumer review rating?
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span className="rounded-full border border-amber-500/40 bg-amber-500/10 px-4 py-1.5 text-xs font-black text-amber-400 shadow-lg shadow-amber-500/10">
                Status: {h3.message}
              </span>
            </div>
          </div>

          {/* 2. Formal Hypotheses Cards (H0 & H1) */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-4">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-black uppercase tracking-wider text-slate-400">
                  Null Hypothesis (H₀)
                </span>
                <span className="font-mono text-[11px] text-slate-400">ρ = 0 (Zero Correlation)</span>
              </div>
              <p className="mt-2 text-xs font-medium leading-relaxed text-slate-200">
                {h3.null_hypothesis || 'There is no linear correlation between sneaker price and consumer rating (rho = 0).'}
              </p>
              <p className="mt-2 text-[11px] text-slate-400">
                Assumes price is decoupled from subjective customer rating scores.
              </p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-4">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-black uppercase tracking-wider text-indigo-400">
                  Alternative Hypothesis (H₁)
                </span>
                <span className="font-mono text-[11px] text-indigo-400">ρ ≠ 0 (Non-Zero Correlation)</span>
              </div>
              <p className="mt-2 text-xs font-medium leading-relaxed text-slate-200">
                {h3.alternative_hypothesis || 'There is a statistically significant linear correlation between sneaker price and consumer rating (rho != 0).'}
              </p>
              <p className="mt-2 text-[11px] text-slate-400">
                Assumes higher prices correlate with premium user ratings (or vice versa).
              </p>
            </div>
          </div>

          {/* 3. Numerical Metrics Grid */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
            <div className="rounded-2xl border border-slate-800 bg-slate-950/90 p-4">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Statistical Test</span>
              <p className="mt-1 text-sm font-bold text-white">Pearson Product-Moment</p>
              <p className="text-[10px] font-mono text-slate-400">scipy.stats.pearsonr</p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950/90 p-4">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Significance Level (α)</span>
              <p className="mt-1 text-xl font-black text-indigo-400">{h3.alpha ?? 0.05}</p>
              <p className="text-[10px] text-slate-400">Standard Threshold</p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950/90 p-4">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Test Statistic (r)</span>
              <p className="mt-1 text-xl font-black text-slate-400">
                {h3.correlation !== null ? h3.correlation.toFixed(4) : 'N/A (No Sensor)'}
              </p>
              <p className="text-[10px] text-slate-400">Pearson correlation</p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950/90 p-4">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">p-value</span>
              <p className="mt-1 text-xl font-black text-slate-400">
                {h3.p_value !== null ? h3.p_value.toFixed(4) : 'N/A'}
              </p>
              <p className="text-[10px] text-slate-400">Test Not Executed</p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950/90 p-4">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Decision</span>
              <p className="mt-1 text-sm font-bold text-amber-400">{h3.decision}</p>
              <p className="text-[10px] text-slate-400">Data Integrity Guard</p>
            </div>
          </div>

          {/* 4. Data Science Integrity & Engineering Explanation */}
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <div className="rounded-2xl border border-amber-500/20 bg-amber-950/10 p-5 text-amber-200">
              <h4 className="text-sm font-bold flex items-center gap-2">
                <span>⚠️</span> Academic FDS Integrity Policy Applied
              </h4>
              <p className="mt-2 text-xs leading-relaxed text-amber-300 font-mono">
                &ldquo;{h3.interpretation}&rdquo;
              </p>
              <p className="mt-3 text-[11px] text-amber-400/80">
                SoleScout indexes live retailer pricing, in-stock US sizes, and store availability;
                it does not collect subjective review scores. Per academic FDS ethics rules, artificial ratings are never synthesized.
              </p>
            </div>

            <div className="rounded-2xl border border-indigo-500/30 bg-indigo-950/20 p-5">
              <h4 className="text-sm font-bold text-indigo-300 flex items-center gap-2">
                <span>⚡</span> 2nd-Year Engineering Analogy: Telemetry Sensor Circuit
              </h4>
              <p className="mt-2 text-xs leading-relaxed text-indigo-200/90">
                {h3.engineering_explanation ||
                  "In electrical measurement, you cannot report impedance or current without connecting an ammeter to the circuit. " +
                  "Attempting to correlate price with missing review telemetry would require fabricating synthetic data, " +
                  "which directly violates engineering ethics. In professional systems, reporting 'Sensor Telemetry Absent' " +
                  "is the correct, rigorous engineering response."}
              </p>
            </div>
          </div>
        </section>
      )}

      {/* ------------------------------------------------------------------- */}
      {/* SUPPORTING CHARTS: PRICE DISTRIBUTION & BRAND COMPARISON */}
      {/* ------------------------------------------------------------------- */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* CHART 4: PRICE DISTRIBUTION HISTOGRAM */}
        <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-400">
              Distribution Analysis
            </span>
            <h4 className="mt-1 text-base font-bold text-white">
              Sneaker Market Price Distribution (Histogram)
            </h4>
            <p className="text-xs text-slate-400">
              Histogram bins showing price density across the catalog.
              {priceDist?.skewness !== undefined && (
                <span className="ml-2 font-mono text-indigo-300">
                  Skewness: {priceDist.skewness.toFixed(2)} ({priceDist.skewness > 0 ? 'Right-skewed' : 'Left-skewed'})
                </span>
              )}
            </p>
          </div>

          <div className="h-64 w-full pt-4">
            {priceDist?.bins && priceDist.bins.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={priceDist.bins} margin={{ top: 10, right: 10, bottom: 20, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
                  <XAxis dataKey="bin_label" stroke="#94a3b8" fontSize={10} tickLine={false} />
                  <YAxis stroke="#94a3b8" fontSize={10} tickLine={false} />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const bin = payload[0].payload;
                        return (
                          <div className="rounded-xl border border-slate-800 bg-slate-900 p-2.5 shadow-xl text-xs font-mono">
                            <p className="font-bold text-white">{bin.bin_label}</p>
                            <p className="text-indigo-400">Count: <strong>{bin.count}</strong> ({bin.percentage}%)</p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Bar dataKey="count" fill="#6366f1" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="py-20 text-center text-xs text-slate-500">No price distribution data available.</p>
            )}
          </div>
        </div>

        {/* CHART 5: BRAND COMPARISON BAR CHART */}
        <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <span className="text-[11px] font-bold uppercase tracking-wider text-sky-400">
              Comparative Analysis
            </span>
            <h4 className="mt-1 text-base font-bold text-white">
              Brand Price Comparison (Mean vs. Median)
            </h4>
            <p className="text-xs text-slate-400">
              Evaluates central tendency differences between brands to inspect ANOVA group variance.
            </p>
          </div>

          <div className="h-64 w-full pt-4">
            {brandComp && brandComp.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={brandComp} margin={{ top: 10, right: 10, bottom: 20, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
                  <XAxis dataKey="brand" stroke="#94a3b8" fontSize={10} tickLine={false} />
                  <YAxis stroke="#94a3b8" fontSize={10} tickLine={false} tickFormatter={(v) => `$${v}`} />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const item = payload[0].payload;
                        return (
                          <div className="rounded-xl border border-slate-800 bg-slate-900 p-2.5 shadow-xl text-xs font-mono">
                            <p className="font-bold text-white">{item.brand}</p>
                            <p className="text-indigo-400">Mean: ${item.mean_price?.toFixed(2)}</p>
                            <p className="text-sky-400">Median: ${item.median_price?.toFixed(2)}</p>
                            <p className="text-slate-400">Count: {item.count} items</p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                  <Bar dataKey="mean_price" name="Mean Price ($)" fill="#818cf8" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="median_price" name="Median Price ($)" fill="#38bdf8" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="py-20 text-center text-xs text-slate-500">No brand comparison data available.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
