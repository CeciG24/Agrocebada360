import { createBrowserRouter } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { DashboardPage } from './pages/DashboardPage';
import { ParcelaPage } from './pages/ParcelaPage';
import { RegionalPage } from './pages/RegionalPage';
import { ModeloPage } from './pages/ModeloPage';
import { AcercaPage } from './pages/AcercaPage';

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
          <div className="px-6 pb-10">
            <div className="rounded-2xl border border-ink-700/60 bg-ink-900/80 p-6 text-text-mid">
              404 — La página que buscas no existe.
            </div>
          </div>
        ),
      },
    ],
  },
]);