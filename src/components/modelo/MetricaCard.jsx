export function MetricaCard({ label, value, unit, hint, variant = 'default' }) {
  const accent =
    variant === 'highlight'
      ? 'border-moss-700/50 bg-moss-900/30'
      : 'border-ink-700/60 bg-ink-900/70';

  return (
    <div className={`rounded-2xl border ${accent} px-5 py-4 animate-fade-up`}>
      <div className="text-sm text-text-lo">{label}</div>
      <div className="mt-1.5 flex items-baseline gap-1.5">
        <span className="text-3xl font-semibold text-text-hi tabular-nums">{value}</span>
        {unit && <span className="text-sm text-text-mid">{unit}</span>}
      </div>
      {hint && <div className="mt-1 text-xs text-text-lo">{hint}</div>}
    </div>
  );
}