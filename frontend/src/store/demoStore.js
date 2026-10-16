import { create } from 'zustand';

const STORAGE_KEY = 'cebada360.modoDemo';

function actualizarQuery(demo) {
  const url = new URL(window.location.href);
  if (url.searchParams.has('demo')) {
    url.searchParams.set('demo', demo ? '1' : '0');
    window.history.replaceState(null, '', url);
  }
}

// Prioridad:
// 1. Query param ?demo=1 → fuerza demo
// 2. Query param ?demo=0 → fuerza real
// 3. localStorage → lo que el usuario eligió antes
// 4. Default: true (demo activo hasta que exista backend)
const modoInicial = (() => {
  try {
    const params = new URLSearchParams(window.location.search);
    const demo = params.get('demo');
    if (demo === '1') return true;
    if (demo === '0') return false;

    const guardado = localStorage.getItem(STORAGE_KEY);
    if (guardado === 'true') return true;
    if (guardado === 'false') return false;

    // Sin backend todavía → demo por defecto
    return true;
  } catch {
    return true;
  }
})();

export const useDemoStore = create((set, get) => ({
  modoDemo: modoInicial,
  apiMeta: null,

  activarDemo: () => {
    actualizarQuery(true);
    try { localStorage.setItem(STORAGE_KEY, 'true'); } catch { /* sin localStorage: el modo queda solo en memoria */ }
    set({ modoDemo: true });
  },

  desactivarDemo: () => {
    actualizarQuery(false);
    try { localStorage.setItem(STORAGE_KEY, 'false'); } catch { /* sin localStorage: el modo queda solo en memoria */ }
    set({ modoDemo: false });
  },

  toggleDemo: () => {
    const { modoDemo } = get();
    if (modoDemo) get().desactivarDemo();
    else get().activarDemo();
  },
}));
