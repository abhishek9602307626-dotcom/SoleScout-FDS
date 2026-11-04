import React from 'react';

interface KpiCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  badge?: string;
  badgeColor?: 'green' | 'blue' | 'yellow' | 'purple' | 'gray' | 'red' | 'orange' | 'cyan';
  icon?: React.ReactNode;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  subtitle,
  badge,
  badgeColor = 'blue',
  icon,
}) => {
  const badgeClasses: Record<string, string> = {
    green: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    blue: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
    yellow: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    purple: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
    gray: 'bg-slate-800 text-slate-400 border-slate-700',
    red: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    orange: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
    cyan: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  };
  const badgeClass = badgeClasses[badgeColor] ?? badgeClasses['blue'];

  return (
    <div className="relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-xl backdrop-blur-md transition-all duration-200 hover:border-slate-700 hover:shadow-indigo-500/5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold tracking-wider text-slate-400 uppercase">{title}</p>
          <h3 className="mt-2 text-2xl font-bold tracking-tight text-white">{value}</h3>
          {subtitle && <p className="mt-1 text-xs text-slate-400">{subtitle}</p>}
        </div>
        {icon && (
          <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-slate-800 bg-slate-800/60 text-indigo-400 shadow-inner">
            {icon}
          </div>
        )}
      </div>
      {badge && (
        <div className="mt-3">
          <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${badgeClass}`}>
            {badge}
          </span>
        </div>
      )}
    </div>
  );
};
