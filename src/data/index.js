import { MockRepository } from './mock/MockRepository';
import { ApiRepository } from './api/ApiRepository';
import { useDemoStore } from '../store/demoStore';

// Helper: obtén el repo adecuado AHORA, fuera de React
export function getRepo() {
  return useDemoStore.getState().modoDemo ? MockRepository : ApiRepository;
}

// Objeto proxy: cada llamada decide el repo en el momento de ejecutarse
export const repo = new Proxy({}, {
  get: (_, metodo) => {
    return (...args) => {
      const activo = getRepo();
      if (typeof activo[metodo] !== 'function') {
        return Promise.reject(new Error(`Método no implementado: ${metodo}`));
      }
      return activo[metodo](...args);
    };
  },
});