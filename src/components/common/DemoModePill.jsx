import { useDemoStore } from '../../store/demoStore';

export function DemoModePill() {
  const { modoDemo, toggleDemo } = useDemoStore();

  return (
    <button
      type="button"
      onClick={toggleDemo}
      aria-pressed={modoDemo}
      title={modoDemo
        ? 'Modo demo activo. La app usa datos de ejemplo.'
        : 'Conectado al backend real.'}
      className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm
                  transition-all duration-200
                  ${modoDemo
                    ? 'border-moss-700/60 bg-moss-900/50 text-moss-500'
                    : 'border-ink-600/60 bg-ink-800/70 text-text-mid hover:border-moss-700/40 hover:text-text-hi'}`}
    >
      {/* Iconos */}
      {modoDemo ? (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <path d="M5 12.5a10 10 0 0 1 14 0M8.5 15.5a5.5 5.5 0 0 1 7 0M12 18.5h.01"
                stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
        </svg>
      ) : (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <path d="M5 12h14M12 5v14" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
        </svg>
      )}

      <span>
        {modoDemo ? 'Modo demo' : 'Conectado'}
      </span>

      {/* Indicador de estado */}
      <span
        className={`h-1.5 w-1.5 rounded-full ${
          modoDemo
            ? 'bg-moss-500 animate-pulse'
            : 'bg-ink-500'
        }`}
      />
    </button>
  );
}