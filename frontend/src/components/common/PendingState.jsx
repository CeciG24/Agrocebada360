export function PendingState({ title, description, compact = false }) {
  return (
    <div className={`pending-state ${compact ? 'p-3' : 'p-5'}`}>
      <div className="flex items-start gap-3">
        <span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-lg border border-ink-600 bg-ink-800 text-text-mid" aria-hidden="true">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M5 8h14M5 12h8M5 16h5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg>
        </span>
        <div className="min-w-0">
          <p className="text-sm font-medium text-text-hi">{title}</p>
          <p className="mt-1 text-xs leading-relaxed text-text-mid">{description}</p>
        </div>
      </div>
    </div>
  );
}
