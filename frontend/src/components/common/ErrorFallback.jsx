import { useDemoStore } from '../../store/demoStore';
import { Panel } from './Panel';

export function ErrorFallback({ error, onRetry }) {
  const { modoDemo, activarDemo } = useDemoStore();

  return (
    <Panel className="p-4 sm:p-6 space-y-4">
      <div className="flex items-start gap-3">
        <div className="grid h-10 w-10 place-items-center rounded-xl
                        bg-rose-950/50 border border-rose-700/40 shrink-0">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" className="text-rose-400">
            <path d="M12 9v4M12 17h.01M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"
                  stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        <div className="flex-1">
          <div className="text-sm font-semibold text-rose-300">
            No se pudo cargar la información
          </div>
          <div className="mt-1 text-sm text-text-mid">
            {error ?? 'Error desconocido.'}
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 pt-2">
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="rounded-lg border border-ink-600/60 bg-ink-800/70
                       px-3.5 py-2 text-sm text-text-mid
                       hover:border-moss-700/50 hover:text-moss-500
                       transition-colors duration-150"
          >
            Reintentar
          </button>
        )}

        {!modoDemo && (
          <button
            type="button"
            onClick={activarDemo}
            className="rounded-lg border border-moss-700/50 bg-moss-900/40
                       px-3.5 py-2 text-sm text-moss-500
                       hover:bg-moss-900/60 hover:border-moss-600
                       transition-colors duration-150"
          >
            Pasar a modo demo
          </button>
        )}
      </div>
    </Panel>
  );
}