import {
  parcelasMock,
  municipiosMock,
  cortesMock,
  generarCortes,
  resumenGlobalMock,
  metricasModeloMock,
} from './parcelas.mock';

// ---------- Utilidad ----------
const delay = (ms = 180) => new Promise((r) => setTimeout(r, ms));

// ============================================================
// Repositorio mock — mismo contrato que ApiRepository
// ============================================================
export const MockRepository = {
  // ---------- Parcelas ----------
  async getAllParcelas() {
    await delay();
    return parcelasMock.map((p) => ({
      id: p.id,
      codigo: p.codigo,
      rendimiento_t_ha: p.rendimiento_t_ha,
      superficie_ha: p.superficie_ha,
      municipio: p.municipio,
      riesgo: p.riesgo,
    }));
  },

  async getParcelaById(id) {
    await delay();
    const p = parcelasMock.find((x) => x.id === id);
    if (!p) throw new Error(`Parcela no encontrada: ${id}`);
    return p;
  },

  async getVecinos(id, n = 3) {
    await delay();
    const parcela = parcelasMock.find((p) => p.id === id);
    if (!parcela) return [];

    return parcelasMock
      .filter((p) => p.id !== id && p.municipio === parcela.municipio)
      .slice(0, n)
      .map((p) => ({
        id: p.id,
        rendimiento_t_ha: p.rendimiento_t_ha,
        superficie_ha: p.superficie_ha,
        municipio: p.municipio,
      }));
  },

  // ---------- Contexto municipal ----------
  async getContextoMunicipal(id) {
    await delay();
    const parcela = parcelasMock.find((p) => p.id === id);
    if (!parcela) return null;
    return municipiosMock[parcela.municipio] ?? null;
  },

  // ---------- Cortes temporales ----------
  async getCortesTemporales(id) {
    await delay();
    if (cortesMock[id]) return cortesMock[id];

    const parcela = parcelasMock.find((p) => p.id === id);
    return parcela ? generarCortes(parcela.rendimiento_t_ha) : [];
  },

  // ---------- Resumen global (dashboard) ----------
  async getResumenGlobal() {
    await delay();
    return resumenGlobalMock;
  },

  // ---------- Métricas del modelo ----------
  async getMetricasModelo() {
    await delay();
    return metricasModeloMock;
  },

  // ---------- Región / municipios (futuro /regional) ----------
  async getRegionResumen() {
    await delay();
    return Object.values(municipiosMock);
  },
};