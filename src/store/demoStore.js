import { create } from 'zustand';

const STORAGE_KEY = 'cebada360.modoDemo';

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

  activarDemo: () => {
    try { localStorage.setItem(STORAGE_KEY, 'true'); } catch {}
    set({ modoDemo: true });
  },

  desactivarDemo: () => {
    try { localStorage.setItem(STORAGE_KEY, 'false'); } catch {}
    set({ modoDemo: false });
  },

  toggleDemo: () => {
    const { modoDemo } = get();
    if (modoDemo) get().desactivarDemo();
    else get().activarDemo();
  },
}));