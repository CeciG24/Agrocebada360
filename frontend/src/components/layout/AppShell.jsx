import { useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Topbar } from './Topbar';
import { ModoListener } from './ModoListener';
import { useDemoStore } from '../../store/demoStore';

const TITULOS = {
  '/': 'Dashboard',
  '/regional': 'Regional',
  '/modelo': 'Modelo',
  '/acerca': 'Acerca de',
};

function tituloDe(pathname) {
  if (TITULOS[pathname]) return TITULOS[pathname];
  if (pathname.startsWith('/parcela/')) return `Parcela ${pathname.split('/')[2] ?? ''}`.trim();
  return 'Página no encontrada';
}

export function AppShell() {
  const location = useLocation();
  const modoDemo = useDemoStore((s) => s.modoDemo);
  const apiMeta = useDemoStore((s) => s.apiMeta);

  // El título de la pestaña sigue a la vista (historial, lectores de pantalla)
  useEffect(() => {
    document.title = `${tituloDe(location.pathname)} · Cebada360`;
  }, [location.pathname]);

  return (
    <div className="min-h-screen bg-ink-950 text-text-hi">
      <a
        href="#contenido"
        className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50
                   focus:rounded-lg focus:border focus:border-moss-700/60 focus:bg-moss-900
                   focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-moss-500"
      >
        Saltar al contenido
      </a>
      <ModoListener />
      <Topbar />

      {modoDemo && (
        <div className="border-b border-moss-700/30 bg-moss-900/20 px-4 py-2 sm:px-6">
          <div className="flex items-center gap-2 text-xs text-moss-500">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
              <path d="M5 12.5a10 10 0 0 1 14 0M8.5 15.5a5.5 5.5 0 0 1 7 0M12 18.5h.01"
                    stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            <span>
              Modo demo activo — se muestran datos de ejemplo.
              Desactívalo para consultar la API.
            </span>
          </div>
        </div>
      )}

      {!modoDemo && apiMeta && (
        <div role="status" className="border-b border-ink-700 px-6 py-2 text-sm text-text-mid">
          {apiMeta.mode === 'mock' ? 'La API está en modo mock: estos resultados son sintéticos.' : 'Resultados reales entregados por la API.'}
          {' '}Ciclo {apiMeta.cycle} · límite de información {apiMeta.data_cutoff}.
        </div>
      )}

      <main id="contenido" tabIndex={-1} key={location.pathname} className="animate-fade-up outline-none">
        <Outlet />
      </main>
    </div>
  );
}
