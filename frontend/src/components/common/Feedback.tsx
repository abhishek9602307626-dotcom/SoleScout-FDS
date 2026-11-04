import React from 'react';

export const LoadingSpinner: React.FC<{ message?: string }> = ({ message = "Loading analytics..." }) => (
  <div className="flex min-h-[300px] flex-col items-center justify-center p-8 text-center">
    <div className="relative flex h-12 w-12 items-center justify-center">
      <div className="absolute h-full w-full animate-ping rounded-full bg-indigo-500/20"></div>
      <div className="h-10 w-10 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent shadow-lg"></div>
    </div>
    <p className="mt-4 text-sm font-medium text-slate-400">{message}</p>
  </div>
);

export const EmptyState: React.FC<{
  title?: string;
  message?: string;
  actionText?: string;
  onAction?: () => void;
}> = ({
  title = "No SoleScout data has been collected yet.",
  message = "Configure the API key in backend/.env or enable Demo Mode to explore the analytics dashboard.",
  actionText,
  onAction,
}) => (
  <div className="flex min-h-[360px] flex-col items-center justify-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/40 p-8 text-center backdrop-blur-sm">
    <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-slate-800 bg-slate-800/80 text-amber-400 shadow-inner">
      <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
      </svg>
    </div>
    <h3 className="mt-4 text-lg font-semibold text-white">{title}</h3>
    <p className="mt-2 max-w-md text-sm text-slate-400 leading-relaxed">{message}</p>
    {actionText && onAction && (
      <button
        onClick={onAction}
        className="mt-6 inline-flex items-center rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 transition-all hover:bg-indigo-500 hover:shadow-indigo-500/40 active:scale-95"
      >
        {actionText}
      </button>
    )}
  </div>
);

export const ErrorAlert: React.FC<{
  error: string;
  onRetry?: () => void;
}> = ({ error, onRetry }) => (
  <div className="rounded-2xl border border-rose-500/30 bg-rose-950/20 p-5 text-rose-300 backdrop-blur-md">
    <div className="flex items-start justify-between">
      <div className="flex items-start space-x-3">
        <svg className="mt-0.5 h-5 w-5 flex-shrink-0 text-rose-400" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
        </svg>
        <div>
          <h4 className="text-sm font-bold text-rose-200">System Communication Error</h4>
          <p className="mt-1 text-xs text-rose-300/90 leading-relaxed">{error}</p>
        </div>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="rounded-lg border border-rose-500/40 bg-rose-500/10 px-3 py-1.5 text-xs font-semibold text-rose-200 hover:bg-rose-500/20 transition-all"
        >
          Retry
        </button>
      )}
    </div>
  </div>
);
