import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import {
  DataQualityResponse,
  CollectorRunResponse,
  PipelineStageItem,
  RemovedRecordItem,
} from '../types';
import { LoadingSpinner, ErrorAlert } from '../components/common/Feedback';
import { KpiCard } from '../components/common/KpiCard';

// ─── Pipeline Flow Diagram ────────────────────────────────────────────────────

const PipelineArrow: React.FC = () => (
  <div className="flex items-center justify-center py-1">
    <div className="flex flex-col items-center gap-1">
      <div className="w-px h-4 bg-gradient-to-b from-indigo-500/60 to-indigo-400/40" />
      <svg width="12" height="7" viewBox="0 0 12 7" className="text-indigo-400">
        <path d="M6 7L0 0h12z" fill="currentColor" />
      </svg>
    </div>
  </div>
);

interface StageCardProps {
  stage: PipelineStageItem;
  isLast: boolean;
}

const StageCard: React.FC<StageCardProps> = ({ stage, isLast }) => {
  const stageColors: Record<number, string> = {
    1: 'border-blue-500/40 bg-blue-950/20',
    2: 'border-amber-500/40 bg-amber-950/20',
    3: 'border-orange-500/40 bg-orange-950/20',
    4: 'border-purple-500/40 bg-purple-950/20',
    5: 'border-emerald-500/40 bg-emerald-950/20',
    6: 'border-cyan-500/40 bg-cyan-950/20',
    7: 'border-indigo-500/40 bg-indigo-950/20',
  };
  const badgeColors: Record<number, string> = {
    1: 'bg-blue-900/60 text-blue-300',
    2: 'bg-amber-900/60 text-amber-300',
    3: 'bg-orange-900/60 text-orange-300',
    4: 'bg-purple-900/60 text-purple-300',
    5: 'bg-emerald-900/60 text-emerald-300',
    6: 'bg-cyan-900/60 text-cyan-300',
    7: 'bg-indigo-900/60 text-indigo-300',
  };

  const borderClass = stageColors[stage.stage_number] ?? 'border-slate-700/40 bg-slate-900/20';
  const badgeClass = badgeColors[stage.stage_number] ?? 'bg-slate-800 text-slate-300';

  return (
    <div>
      <div className={`rounded-2xl border p-4 ${borderClass} transition-all hover:scale-[1.01]`}>
        <div className="flex items-start gap-3">
          <span className="text-2xl leading-none">{stage.icon}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-bold text-slate-500">Stage {stage.stage_number}</span>
              <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${badgeClass}`}>
                {stage.status}
              </span>
            </div>
            <h4 className="mt-0.5 font-bold text-white text-sm">{stage.name}</h4>
            <p className="mt-1 text-xs text-slate-400 leading-relaxed">{stage.description}</p>
            <div className="mt-2 flex flex-wrap gap-2 text-[10px]">
              <span className="rounded px-2 py-0.5 bg-slate-800/80 text-slate-400 font-mono">
                IN: {stage.input_type}
              </span>
              <span className="text-slate-600">→</span>
              <span className="rounded px-2 py-0.5 bg-slate-800/80 text-slate-300 font-mono">
                OUT: {stage.output_type}
              </span>
            </div>
            {stage.details && (
              <p className="mt-1.5 text-[10px] font-semibold text-slate-400 italic">{stage.details}</p>
            )}
          </div>
        </div>
      </div>
      {!isLast && <PipelineArrow />}
    </div>
  );
};

// ─── Cleaning Efficiency Bar ──────────────────────────────────────────────────

const CleaningEfficiencyBar: React.FC<{
  raw: number;
  clean: number;
  removed: number;
  pct: number;
}> = ({ raw, clean, removed, pct }) => {
  const cleanPct = raw > 0 ? (clean / raw) * 100 : 100;
  const removedPct = 100 - cleanPct;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-xs text-slate-400">
        <span className="font-semibold">
          {raw.toLocaleString()} raw records
        </span>
        <span className="font-semibold text-emerald-400">
          {clean.toLocaleString()} retained ({pct.toFixed(1)}%)
        </span>
      </div>
      <div className="h-5 w-full overflow-hidden rounded-full bg-slate-800 flex">
        <div
          className="h-full bg-gradient-to-r from-emerald-600 to-emerald-400 transition-all duration-700 flex items-center justify-center"
          style={{ width: `${Math.min(cleanPct, 100)}%` }}
        >
          {cleanPct > 20 && (
            <span className="text-[9px] font-bold text-white px-1">Clean</span>
          )}
        </div>
        {removedPct > 0 && (
          <div
            className="h-full bg-gradient-to-r from-red-800 to-red-600 flex items-center justify-center"
            style={{ width: `${Math.min(removedPct, 100)}%` }}
          >
            {removedPct > 10 && (
              <span className="text-[9px] font-bold text-white px-1">Removed</span>
            )}
          </div>
        )}
      </div>
      <div className="flex gap-4 text-[10px] text-slate-500">
        <span className="flex items-center gap-1">
          <span className="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500" />
          Clean: {clean.toLocaleString()}
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-2.5 h-2.5 rounded-full bg-red-700" />
          Removed: {removed.toLocaleString()}
        </span>
      </div>
    </div>
  );
};

// ─── Removed Records Table ────────────────────────────────────────────────────

const RemovedRecordsTable: React.FC<{ records: RemovedRecordItem[] }> = ({ records }) => {
  if (records.length === 0) {
    return (
      <div className="px-6 py-10 text-center text-slate-500 text-xs">
        No records were removed during cleaning. All ingested records passed quality validation.
      </div>
    );
  }

  const getCategoryStyle = (category?: string) => {
    if (!category) return 'bg-slate-800/60 text-slate-400';
    if (category.toLowerCase().includes('duplicate')) return 'bg-yellow-900/40 text-yellow-300';
    return 'bg-red-900/40 text-red-300';
  };

  const getRowHover = (category?: string) => {
    if (category?.toLowerCase().includes('duplicate')) return 'hover:bg-yellow-950/20';
    return 'hover:bg-red-950/20';
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-xs text-slate-300">
        <thead className="border-b border-slate-800 bg-slate-950/70 text-[10px] uppercase tracking-wider text-slate-400">
          <tr>
            <th className="px-4 py-3">#</th>
            <th className="px-4 py-3">Product ID</th>
            <th className="px-4 py-3">Product Name</th>
            <th className="px-4 py-3">Raw Price</th>
            <th className="px-4 py-3">Error Type</th>
            <th className="px-4 py-3">Reason(s)</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/40">
          {records.map((rec, idx) => (
            <tr
              key={idx}
              className={`transition-colors ${getRowHover(rec.category)}`}
            >
              <td className="px-4 py-3 font-mono text-slate-500">
                {rec.raw_index !== null && rec.raw_index !== undefined ? rec.raw_index : idx}
              </td>
              <td className="px-4 py-3 font-mono text-slate-400">
                {rec.product_id ?? <span className="text-slate-600 italic">null</span>}
              </td>
              <td className="px-4 py-3 text-white font-medium max-w-[180px] truncate">
                {rec.product_name ?? <span className="text-slate-600 italic">null</span>}
              </td>
              <td className="px-4 py-3 font-mono">
                {rec.raw_price !== null && rec.raw_price !== undefined
                  ? String(rec.raw_price)
                  : <span className="text-slate-600 italic">null</span>}
              </td>
              <td className="px-4 py-3">
                <span className={`rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide ${getCategoryStyle(rec.category)}`}>
                  {rec.category ?? 'Data Quality Error'}
                </span>
              </td>
              <td className="px-4 py-3 text-slate-400 max-w-[220px]">
                {rec.reasons}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// ─── Main Page ────────────────────────────────────────────────────────────────

export const DataQualityPage: React.FC = () => {
  const [data, setData] = useState<DataQualityResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [runningCollector, setRunningCollector] = useState<boolean>(false);
  const [collectorResult, setCollectorResult] = useState<CollectorRunResponse | null>(null);

  const fetchQuality = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getDataQuality();
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve data quality audit.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQuality();
  }, []);

  const handleRunCollector = async (demo: boolean) => {
    try {
      setRunningCollector(true);
      setCollectorResult(null);
      const res = await api.runCollector({ demo, queries: 'Jordan,Nike,Adidas', limit: 5 });
      setCollectorResult(res);
      await fetchQuality();
    } catch (err: any) {
      setError(err.message || 'Pipeline trigger failed.');
    } finally {
      setRunningCollector(false);
    }
  };

  if (loading && !data) return <LoadingSpinner message="Auditing SQLite dataset & ETL quality reports..." />;
  if (error && !data) return <ErrorAlert error={error} onRetry={fetchQuality} />;
  if (!data) return null;

  const m = data.metrics;
  const pipeline = data.pipeline_stages ?? [];
  const removedRecords = data.removed_records ?? [];

  // Build default pipeline if backend didn't return one (older report)
  const displayPipeline: PipelineStageItem[] = pipeline.length > 0 ? pipeline : [
    { stage_number: 1, name: 'SoleScout API', icon: '🌐', description: 'Live sneaker market data via REST API.', input_type: 'HTTP Request', output_type: 'JSON Response', status: 'Active' },
    { stage_number: 2, name: 'Raw Data Storage', icon: '📦', description: 'Raw JSON files saved to data/raw/.', input_type: 'JSON Response', output_type: 'JSON Files', status: 'Active' },
    { stage_number: 3, name: 'Validation', icon: '🔍', description: 'Validates product IDs, names, prices, timestamps.', input_type: 'JSON Records', output_type: 'Valid / Rejected Records', status: 'Active' },
    { stage_number: 4, name: 'Cleaning Pipeline', icon: '🧹', description: 'Deduplication, brand standardization, outlier flagging.', input_type: 'Valid Records', output_type: 'Clean DataFrame', status: 'Active' },
    { stage_number: 5, name: 'Clean Data Export', icon: '📊', description: 'Cleaned CSV + Data Quality JSON report exported.', input_type: 'Clean DataFrame', output_type: 'CSV + JSON Report', status: 'Active' },
    { stage_number: 6, name: 'SQLite Database', icon: '🗄️', description: 'Ingested with UNIQUE(product_id, collection_date).', input_type: 'Clean DataFrame', output_type: 'SQLite Rows', status: 'Active' },
    { stage_number: 7, name: 'Analysis & API', icon: '📈', description: 'FastAPI + SciPy serving analytics to React frontend.', input_type: 'SQLite Data', output_type: 'JSON API Responses', status: 'Active' },
  ];

  const rawCsvAvailable = data.raw_csv_available ?? false;
  const cleanedCsvAvailable = data.cleaned_csv_available ?? false;

  return (
    <div className="space-y-8">
      {/* ── Page Header + Controls ─────────────────────────────────────────── */}
      <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-md">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 className="text-xl font-extrabold tracking-tight text-white">
              Data Quality & ETL Pipeline
            </h2>
            <p className="mt-1 text-xs text-slate-400 max-w-lg">
              Stage 4 — FDS Data Cleaning Audit. All records normalized through a reproducible pipeline.
              Missing fields are preserved as <code className="font-mono text-indigo-400">NULL</code> — never invented.
            </p>
            {data.report_date && (
              <p className="mt-2 text-[10px] font-mono text-slate-500">
                Report generated: {new Date(data.report_date).toLocaleString()}
              </p>
            )}
          </div>

          {/* Actions */}
          <div className="flex flex-wrap items-center gap-3 shrink-0">
            {/* Download CSV Buttons */}
            {rawCsvAvailable ? (
              <a
                href="/api/download/raw-csv"
                download="solescout_raw_data.csv"
                className="flex items-center gap-2 rounded-xl border border-slate-600 bg-slate-800 px-4 py-2 text-xs font-bold text-slate-200 hover:bg-slate-700 hover:border-slate-500 transition-all"
              >
                <span>⬇</span>
                <span>Raw CSV</span>
              </a>
            ) : (
              <span className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-xs text-slate-600 cursor-not-allowed" title="Run collector first">
                ⬇ Raw CSV
              </span>
            )}

            {cleanedCsvAvailable ? (
              <a
                href="/api/download/cleaned-csv"
                download="solescout_cleaned_data.csv"
                className="flex items-center gap-2 rounded-xl border border-emerald-600/50 bg-emerald-950/30 px-4 py-2 text-xs font-bold text-emerald-300 hover:bg-emerald-900/30 hover:border-emerald-500 transition-all"
              >
                <span>⬇</span>
                <span>Cleaned CSV</span>
              </a>
            ) : (
              <span className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-xs text-slate-600 cursor-not-allowed" title="Run cleaning pipeline first">
                ⬇ Cleaned CSV
              </span>
            )}

            {/* Pipeline triggers */}
            <button
              onClick={() => handleRunCollector(false)}
              disabled={runningCollector}
              className="rounded-xl bg-indigo-600 px-4 py-2 text-xs font-bold text-white shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 disabled:opacity-50 transition-all"
            >
              {runningCollector ? 'Processing…' : '▶ Run Live Collector'}
            </button>
            <button
              onClick={() => handleRunCollector(true)}
              disabled={runningCollector}
              className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-xs font-bold text-slate-200 hover:bg-slate-700 disabled:opacity-50 transition-all"
            >
              Seed Demo Data
            </button>
          </div>
        </div>

        {/* Collector result toast */}
        {collectorResult && (
          <div
            className={`mt-4 rounded-2xl border p-4 text-xs font-medium ${
              collectorResult.status === 'success'
                ? 'border-emerald-500/30 bg-emerald-950/20 text-emerald-300'
                : 'border-amber-500/30 bg-amber-950/20 text-amber-300'
            }`}
          >
            <div className="flex items-center justify-between flex-wrap gap-2">
              <span className="font-bold uppercase tracking-wider">
                Pipeline Status: {collectorResult.status}
              </span>
              <span>Inserted: {collectorResult.snapshots_inserted} snapshots</span>
            </div>
            <p className="mt-1 font-mono">{collectorResult.message}</p>
          </div>
        )}
      </div>

      {/* ── ETL Pipeline Flow ──────────────────────────────────────────────── */}
      <div className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-900/60 shadow-xl backdrop-blur-md">
        <div className="border-b border-slate-800/80 p-5">
          <h3 className="text-base font-bold text-white">FDS Data Pipeline</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            End-to-end ETL flow: from live API ingestion through cleaning, validation, and statistical analysis.
          </p>
        </div>
        <div className="p-6">
          {/* Mobile: vertical stack */}
          <div className="flex flex-col md:hidden gap-0">
            {displayPipeline.map((stage, i) => (
              <StageCard key={stage.stage_number} stage={stage} isLast={i === displayPipeline.length - 1} />
            ))}
          </div>
          {/* Desktop: 4 + 3 grid with arrows */}
          <div className="hidden md:block space-y-0">
            {/* Row 1: stages 1–4 */}
            <div className="grid grid-cols-4 gap-3">
              {displayPipeline.slice(0, 4).map((stage) => (
                <StageCard key={stage.stage_number} stage={stage} isLast={true} />
              ))}
            </div>
            {/* Center arrow going down from col 4 to row 2 */}
            <div className="flex justify-end pr-[calc(25%-12px)]">
              <PipelineArrow />
            </div>
            {/* Row 2: stages 5–7, right-aligned */}
            <div className="grid grid-cols-4 gap-3">
              <div /> {/* empty slot */}
              {displayPipeline.slice(4).map((stage) => (
                <StageCard key={stage.stage_number} stage={stage} isLast={true} />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── KPI Metric Cards ───────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        <KpiCard
          title="Raw API Records"
          value={m.raw_records.toLocaleString()}
          subtitle="Ingested from collector"
          badgeColor="blue"
        />
        <KpiCard
          title="Clean Records Retained"
          value={m.clean_records.toLocaleString()}
          subtitle="Passed all quality checks"
          badgeColor="green"
        />
        <KpiCard
          title="Duplicates Purged"
          value={m.duplicate_records.toLocaleString()}
          subtitle="UNIQUE(product_id, date)"
          badgeColor="yellow"
        />
        <KpiCard
          title="Invalid Prices"
          value={m.invalid_prices.toLocaleString()}
          subtitle="Non-positive or non-numeric"
          badgeColor="red"
        />
        <KpiCard
          title="Invalid Timestamps"
          value={m.invalid_timestamps.toLocaleString()}
          subtitle="Non-ISO 8601 dates rejected"
          badgeColor="red"
        />
        <KpiCard
          title="Total Records Removed"
          value={m.records_removed.toLocaleString()}
          subtitle="Errors + duplicates combined"
          badgeColor="orange"
        />
        <KpiCard
          title="Cleaning Efficiency"
          value={`${m.cleaning_percentage.toFixed(1)}%`}
          subtitle="Valid data retention rate"
          badgeColor="purple"
        />
        <KpiCard
          title="Outliers Preserved"
          value="Policy: Keep"
          subtitle="Statistical outliers flagged, not removed"
          badgeColor="cyan"
        />
      </div>

      {/* ── Cleaning Efficiency Bar ────────────────────────────────────────── */}
      <div className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-900/60 shadow-xl backdrop-blur-md">
        <div className="border-b border-slate-800/80 p-5">
          <h3 className="text-base font-bold text-white">Cleaning Flow Summary</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Visual breakdown of raw input vs. clean output vs. removed records.
          </p>
        </div>
        <div className="p-6">
          <CleaningEfficiencyBar
            raw={m.raw_records}
            clean={m.clean_records}
            removed={m.records_removed}
            pct={m.cleaning_percentage}
          />
          <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div className="rounded-xl border border-slate-700 bg-slate-800/40 p-4 text-center">
              <p className="text-slate-500 uppercase tracking-wide text-[9px] font-bold mb-1">Outlier Policy</p>
              <p className="text-slate-200 font-semibold">Tukey IQR — Flag Only</p>
              <p className="text-slate-500 mt-0.5">Outliers preserved with <code className="font-mono">is_outlier=True</code></p>
            </div>
            <div className="rounded-xl border border-slate-700 bg-slate-800/40 p-4 text-center">
              <p className="text-slate-500 uppercase tracking-wide text-[9px] font-bold mb-1">Missing Value Policy</p>
              <p className="text-slate-200 font-semibold">Store as SQL NULL</p>
              <p className="text-slate-500 mt-0.5">Never imputed or synthesized</p>
            </div>
            <div className="rounded-xl border border-slate-700 bg-slate-800/40 p-4 text-center">
              <p className="text-slate-500 uppercase tracking-wide text-[9px] font-bold mb-1">Reproducibility</p>
              <p className="text-slate-200 font-semibold">Pipeline v2.0-fds</p>
              <p className="text-slate-500 mt-0.5">Deterministic — same input → same output</p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Missing Values Audit ───────────────────────────────────────────── */}
      <div className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-900/60 shadow-xl backdrop-blur-md">
        <div className="border-b border-slate-800/80 p-5">
          <h3 className="text-base font-bold text-white">Missing Values & Sparsity Audit</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Per project integrity rules, missing fields are preserved as <code className="font-mono text-indigo-400">NULL</code> and never artificially fabricated.
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="border-b border-slate-800 bg-slate-950/70 text-xs uppercase tracking-wider text-slate-400">
              <tr>
                <th className="px-6 py-3.5">Schema Field</th>
                <th className="px-6 py-3.5">Missing Count</th>
                <th className="px-6 py-3.5">Sparsity %</th>
                <th className="px-6 py-3.5">Integrity Treatment</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-xs">
              {Object.entries(m.missing_values).length > 0 ? (
                Object.entries(m.missing_values).map(([field, meta]) => (
                  <tr key={field} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-3.5 font-mono font-bold text-white">{field}</td>
                    <td className="px-6 py-3.5 font-mono text-slate-300">{meta.count}</td>
                    <td className="px-6 py-3.5">
                      <div className="flex items-center space-x-3">
                        <div className="h-2 w-24 rounded-full bg-slate-800 overflow-hidden">
                          <div
                            className={`h-full ${meta.percentage > 50 ? 'bg-amber-500' : 'bg-indigo-500'}`}
                            style={{ width: `${meta.percentage}%` }}
                          />
                        </div>
                        <span className="font-mono text-slate-400">{meta.percentage.toFixed(1)}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-3.5 text-slate-400">
                      Preserved as SQL NULL; no synthetic values imputed
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-slate-500">
                    No field sparsity detected in current clean dataset. Run the collector & cleaning pipeline to generate a full report.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Records Removed Table ──────────────────────────────────────────── */}
      <div className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-900/60 shadow-xl backdrop-blur-md">
        <div className="border-b border-slate-800/80 p-5 flex items-center justify-between flex-wrap gap-3">
          <div>
            <h3 className="text-base font-bold text-white">Records Removed During Cleaning</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Rows purged from the raw dataset with their quality error categories and reasons.
              <span className="ml-2 text-[9px] uppercase tracking-wide">
                <span className="text-red-400 font-bold">■ Data Quality Error</span>
                <span className="mx-2 text-slate-600">|</span>
                <span className="text-yellow-400 font-bold">■ Duplicate Record</span>
              </span>
            </p>
          </div>
          <span className="rounded-full border border-slate-700 bg-slate-800 px-3 py-1 text-xs font-mono text-slate-400">
            {removedRecords.length} record{removedRecords.length !== 1 ? 's' : ''}
          </span>
        </div>
        <RemovedRecordsTable records={removedRecords} />
        {removedRecords.length === 0 && m.records_removed > 0 && (
          <div className="px-6 py-4 text-center text-xs text-slate-500 border-t border-slate-800/40">
            {m.records_removed} record(s) were removed. Re-run the cleaning pipeline to generate detailed removal reasons.
          </div>
        )}
      </div>

      {/* ── Download Footer ────────────────────────────────────────────────── */}
      <div className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-900/60 shadow-xl backdrop-blur-md">
        <div className="p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-bold text-white">Export Raw & Cleaned Datasets</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              CSV exports contain no API credentials. Run the collector first to generate the raw CSV.
            </p>
          </div>
          <div className="flex gap-3 flex-wrap">
            {rawCsvAvailable ? (
              <a
                href="/api/download/raw-csv"
                download="solescout_raw_data.csv"
                className="flex items-center gap-2 rounded-xl border border-slate-600 bg-slate-800 px-5 py-2.5 text-sm font-bold text-slate-200 hover:bg-slate-700 transition-all"
              >
                ⬇ Download Raw CSV
              </a>
            ) : (
              <button disabled className="rounded-xl border border-slate-800 bg-slate-900 px-5 py-2.5 text-sm font-bold text-slate-600 cursor-not-allowed">
                ⬇ Download Raw CSV
              </button>
            )}
            {cleanedCsvAvailable ? (
              <a
                href="/api/download/cleaned-csv"
                download="solescout_cleaned_data.csv"
                className="flex items-center gap-2 rounded-xl bg-emerald-700 px-5 py-2.5 text-sm font-bold text-white hover:bg-emerald-600 transition-all"
              >
                ⬇ Download Cleaned CSV
              </a>
            ) : (
              <button disabled className="rounded-xl bg-slate-800 px-5 py-2.5 text-sm font-bold text-slate-600 cursor-not-allowed">
                ⬇ Download Cleaned CSV
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
