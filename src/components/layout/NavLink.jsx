import { NavLink as RouterNavLink } from 'react-router-dom';

export function NavLink({ to, children, end = false }) {
  return (
    <RouterNavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        `relative px-3 py-1.5 text-sm rounded-lg transition-colors duration-200
         ${isActive
           ? 'text-moss-500 bg-moss-900/60 font-semibold'
           : 'text-text-mid hover:text-text-hi hover:bg-ink-800/60'}`
      }
    >
      {({ isActive }) => (
        <>
          {children}
          {isActive && (
            <span
              className="absolute left-1/2 -bottom-[3px] h-0.5 w-6 -translate-x-1/2
                         bg-moss-500 rounded-full animate-fade-in"
              aria-hidden
            />
          )}
        </>
      )}
    </RouterNavLink>
  );
}