export function MiniKpi({ label, value, unit }) {
  return (
    <div className="rounded-xl border border-ink-700/60 bg-ink-800/70 px-4 py-3
                    transition-all duration-200
                    hover:border-moss-700/50 hover:bg-ink-800
                    animate-fade-up">
      <div className="text-sm text-text-lo">{label}</div>
      <div className="mt-1 flex items-baseline gap-1">
        <span className="text-2xl font-semibold text-text-hi tabular-nums">{value}</span>
        <span className="text-sm text-text-mid">{unit}</span>
      </div>
    </div>
  );
}