import { createBrowserRouter } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { DashboardPage } from './pages/DashboardPage';
import { ParcelaPage } from './pages/ParcelaPage';
import { RegionalPage } from './pages/RegionalPage';
import { ModeloPage } from './pages/ModeloPage';
import { AcercaPage } from './pages/AcercaPage';
import { EmptyState } from './components/common/EmptyState';
import { Link } from 'react-router-dom';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true,              element: <DashboardPage /> },
      { path: 'parcela/:id',      element: <ParcelaPage /> },
      { path: 'regional',         element: <RegionalPage /> },
      { path: 'modelo',           element: <ModeloPage /> },
      { path: 'acerca',           element: <AcercaPage /> },
      {
        path: '*',
        element: (
          <div className="px-4 sm:px-6 pb-10">
            <div className="rounded-2xl border border-ink-700/60 bg-ink-900/80">
              <EmptyState
                titulo="Esta página no existe"
                detalle="Puede que el enlace esté mal escrito o que la página ya no esté disponible."
              >
                <Link
                  to="/"
                  className="mt-1 inline-flex min-h-[40px] items-center rounded-lg border border-moss-700/50
                             bg-moss-900 px-4 text-sm font-semibold text-moss-500 hover:bg-moss-700 hover:text-white"
                >
                  Volver al dashboard
                </Link>
              </EmptyState>
            </div>
          </div>
        ),
      },
    ],
  },
]);