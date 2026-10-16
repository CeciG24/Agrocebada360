export function Panel({ className = '', children }) {
  return (
    <div
      className={`rounded-2xl border border-ink-700/60 bg-ink-900/80 shadow-panel
                  transition-shadow duration-300 hover:shadow-[0_10px_40px_-12px_rgba(34,197,94,0.15)]
                  ${className}`}
    >
      {children}
    </div>
  );
}