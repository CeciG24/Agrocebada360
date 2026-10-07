import { Outlet, useLocation } from 'react-router-dom';
import { Topbar } from './Topbar';
import { ModoListener } from './ModoListener';
import { useDemoStore } from '../../store/demoStore';

export function AppShell() {
  const location = useLocation();
  const modoDemo = useDemoStore((s) => s.modoDemo);

  return (
    <div className="min-h-screen bg-ink-950 text-text-hi">
      <ModoListener />
      <Topbar />

      {modoDemo && (
        <div className="border-b border-moss-700/30 bg-moss-900/20 px-6 py-2">
          <div className="flex items-center gap-2 text-xs text-moss-500">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
              <path d="M5 12.5a10 10 0 0 1 14 0M8.5 15.5a5.5 5.5 0 0 1 7 0M12 18.5h.01"
                    stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            <span>
              Modo demo activo — se muestran datos de ejemplo.
              Desactívalo para conectarte al backend real.
            </span>
          </div>
        </div>
      )}

      <main key={location.pathname} className="animate-fade-up">
        <Outlet />
      </main>
    </div>
  );
}