import { Link } from 'react-router-dom';
import { NavLink } from './NavLink';
import { DemoModePill } from '../common/DemoModePill';

const NAV_ITEMS = [
  { to: '/',          label: 'Dashboard', end: true },
  { to: '/regional',  label: 'Regional' },
  { to: '/modelo',    label: 'Modelo' },
  { to: '/acerca',    label: 'Acerca de' },
];

export function Topbar() {
  return (
    <header className="sticky top-0 z-30 border-b border-ink-700/60
                       bg-ink-950/85 backdrop-blur-md">
      {/* En móvil el menú baja a una segunda fila a todo el ancho (order-last);
          desde md vuelve al centro de la barra. */}
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 px-4 py-3 sm:px-6 md:py-4">

        {/* Logo + título → home */}
        <Link to="/" className="flex min-h-[40px] items-center gap-3 group">
          <div className="grid h-9 w-9 place-items-center rounded-lg
                          bg-moss-900 border border-moss-700/40
                          transition-all duration-200
                          group-hover:border-moss-600 group-hover:scale-105">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" className="text-moss-500">
              <path d="M12 3c3 4 6 6 6 10a6 6 0 1 1-12 0c0-4 3-6 6-10Z"
                    stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"/>
              <path d="M12 21V11" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
            </svg>
          </div>
          <div className="leading-tight">
            <div className="text-text-hi font-semibold tracking-tight">Cebada360</div>
            <div className="hidden text-xs text-text-lo sm:block">Reto AgroCebada FIRA 2026</div>
          </div>
        </Link>

        {/* Navegación central */}
        <nav
          aria-label="Principal"
          className="order-last flex w-full items-center gap-1 md:order-none md:w-auto"
        >
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end}>
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* Modo demo */}
        <DemoModePill />
      </div>
    </header>
  );
}