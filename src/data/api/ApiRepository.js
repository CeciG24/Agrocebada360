const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

async function get(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
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
};