import { cargarGeometriasEstaticas } from '../geometrias';

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

async function get(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}
let geometriasEnCache = null;

async function cargarGeometrias() {
  const url = `${import.meta.env.BASE_URL}data/parcelas.geojson`;
  const res = await fetch(url);
  const faltante = 'falta public/data/parcelas.geojson (geometrías oficiales pendientes de entrega)';
  if (!res.ok) throw new Error(faltante);
  try {
    return await res.json();
  } catch {
    // Un servidor SPA devuelve index.html cuando el archivo no existe.
    throw new Error(faltante);
  }
}
export const ApiRepository = {
  getAllParcelas: () => get('/parcelas'),
  getParcelaById: (id) => get(`/parcelas/${id}`),
  getVecinos: (id, n = 3) => get(`/parcelas/${id}/vecinos?n=${n}`),
  getContextoMunicipal: (id) => get(`/parcelas/${id}/contexto`),
  getCortesTemporales: (id) => get(`/parcelas/${id}/cortes`),
  getResumenGlobal: () => get('/resumen'),
  getMetricasModelo: () => get('/modelo/metricas'),
  getRegionResumen: () => get('/region'),
  // Geometrías: archivo estático, no requiere endpoint del backend.
getGeometrias: () => {
  if (!geometriasEnCache) {
    geometriasEnCache = cargarGeometrias().catch((e) => {
      geometriasEnCache = null; // si falla, se reintenta en la siguiente llamada
      throw e;
    });
  }
  return geometriasEnCache;
},
};