export function ChartPlaceholder({ title, description, xLabel, yLabel }) {
  return (
    <div className="chart-placeholder" role="img" aria-label={`${title}. ${description}`}>
      <div className="chart-placeholder-grid" aria-hidden="true" />
      <div className="relative z-10 mx-auto max-w-xs rounded-2xl border border-ink-600 bg-ink-900/95 p-5 text-center shadow-panel">
        <span className="status-chip mb-3">Datos pendientes</span>
        <p className="text-sm font-semibold text-text-hi">{title}</p>
        <p className="mt-2 text-xs leading-relaxed text-text-mid">{description}</p>
      </div>
      {xLabel && <span className="absolute bottom-3 right-4 text-xs text-text-mid">{xLabel}</span>}
      {yLabel && <span className="absolute left-4 top-3 text-xs text-text-mid">{yLabel}</span>}
    </div>
  );
}
