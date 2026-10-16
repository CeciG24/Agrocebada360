export function StatCard({ label, value, unit, note, accent = false, loading = false, children }) {
  const available = value !== null && value !== undefined && value !== '';
  return (
    <div className={`stat-card ${accent ? 'stat-card-accent' : ''}`} aria-busy={loading || undefined}>
      <div className="flex items-start justify-between gap-3">
        <p className="text-xs font-medium text-text-mid">{label}</p>
        <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${available ? 'bg-moss-500' : 'bg-ink-600'}`} aria-hidden="true" />
      </div>
      <div className="mt-3 flex min-h-9 flex-wrap items-baseline gap-x-2 gap-y-1">
        <span className={`min-w-0 max-w-full break-words text-2xl font-semibold tracking-tight tabular-nums sm:text-3xl ${available ? 'text-text-hi' : 'text-text-mid'}`}>
          {loading ? <span className="skeleton inline-block h-7 w-16 rounded" aria-label="Cargando" /> : available ? value : '—'}
        </span>
        {available && unit && <span className="text-xs text-text-mid">{unit}</span>}
      </div>
      <p className="mt-2 text-xs leading-relaxed text-text-mid">{note ?? (available ? 'Información de la fuente consultada' : 'Dato aún no disponible')}</p>
      {children}
    </div>
  );
}
