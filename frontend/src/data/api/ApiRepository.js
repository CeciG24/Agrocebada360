import { verifyModelEvidence } from '../model/modelEvidence.js';
import { assertMeta, assertParcel, assertPrediction, assertExplanation, assertRisk, assertRegion, sameContext } from './contract.js';

const MESSAGES = {
  PARCEL_NOT_FOUND: 'No se encontró la parcela solicitada.',
  REGION_NOT_FOUND: 'No se encontró la región solicitada.',
  ROUTE_NOT_FOUND: 'Esta consulta todavía no está disponible en la API.',
  DATA_UNAVAILABLE: 'El catálogo de parcelas no está disponible.',
  MODEL_UNAVAILABLE: 'El modelo no está disponible.',
  PREDICTION_UNAVAILABLE: 'La predicción no está disponible para esta parcela.',
  EXPLANATION_UNAVAILABLE: 'No se pudo consultar la explicación.',
  RISK_UNAVAILABLE: 'No se pudo consultar el riesgo.',
  REGION_DATA_UNAVAILABLE: 'La fuente de regiones todavía no está disponible.',
  REGION_SUMMARY_UNAVAILABLE: 'El resumen regional no está disponible.',
  VALIDATION_ERROR: 'Los parámetros de consulta no son válidos.',
  NETWORK_ERROR: 'No se pudo conectar con la API.',
  INVALID_RESPONSE: 'La API devolvió una respuesta incompatible con el contrato.',
  MODEL_EVIDENCE_MISMATCH: 'La ficha de validación no corresponde al modelo o contexto de la API activa.',
};

export class ApiError extends Error {
  constructor(code, status = 0, details = []) {
    super(MESSAGES[code] ?? 'No se pudo completar la consulta a la API.');
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

export function createApiRepository({ baseUrl = '', fetchImpl = globalThis.fetch, onMeta = () => {}, modelEvidence = null } = {}) {
  const base = baseUrl.replace(/\/$/, '');
  let catalogPromise;
  const details = new Map();

  async function get(path) {
    let res;
    try { res = await fetchImpl(`${base}${path}`, { headers: { Accept: 'application/json' } }); }
    catch { throw new ApiError('NETWORK_ERROR'); }
    let body;
    try { body = await res.json(); }
    catch { throw new ApiError('INVALID_RESPONSE', res.status); }
    if (!res.ok) throw new ApiError(body?.error?.code ?? 'INVALID_RESPONSE', res.status, body?.error?.details ?? []);
    try { assertMeta(body.meta); }
    catch { throw new ApiError('INVALID_RESPONSE', res.status); }
    onMeta(body.meta);
    return body;
  }

  async function checked(path, validate) {
    const body = await get(path);
    try { validate(body); }
    catch { throw new ApiError('INVALID_RESPONSE', 200); }
    return body;
  }

  async function getParcelList({ region, includeGeometry = false } = {}) {
    const query = new URLSearchParams({ include_geometry: String(includeGeometry) });
    if (region !== undefined) query.set('region', region);
    return checked(`/parcels?${query}`, (body) => {
      if (!Array.isArray(body.items) || body.total !== body.items.length) throw new Error('total');
      const ids = body.items.map((item) => {
        assertParcel(item, includeGeometry);
        if (region !== undefined && item.region !== region) throw new Error('region');
        return item.id;
      });
      if (new Set(ids).size !== ids.length || ids.some((id, i) => i > 0 && ids[i - 1] > id)) throw new Error('ids');
    });
  }

  function catalog() {
    // Una consulta compartida para listado y mapa, sin solicitudes por parcela.
    catalogPromise ??= getParcelList({ includeGeometry: true }).catch((e) => { catalogPromise = undefined; throw e; });
    return catalogPromise;
  }

  function detail(id) {
    if (!details.has(id)) {
      details.set(id, checked(`/parcel/${encodeURIComponent(id)}`, (body) => {
        assertParcel(body, true);
        if (body.id !== id) throw new Error('id');
      }).catch((e) => { details.delete(id); throw e; }));
    }
    return details.get(id);
  }

  async function getRegion(region) {
    return checked(`/regions/${encodeURIComponent(region)}`, (body) => {
      assertRegion(body);
      if (body.region !== region) throw new Error('region');
    });
  }

  return {
    getParcelList,
    getRegion,
    clearCache() { catalogPromise = undefined; details.clear(); },
    async getAllParcelas() {
      const body = await catalog();
      return body.items.map((p) => ({ ...p, meta: body.meta }));
    },
    async getGeometrias() {
      const body = await catalog();
      return { type: 'FeatureCollection', features: body.items.filter((p) => p.geometry !== null).map((p) => ({
        type: 'Feature', id: p.id, properties: { id: p.id, region: p.region }, geometry: p.geometry,
      })) };
    },
    async getParcelaById(id) {
      const parcel = await detail(id);
      const results = await Promise.allSettled([
        checked(`/predict/${encodeURIComponent(id)}`, assertPrediction),
        checked(`/explain/${encodeURIComponent(id)}`, assertExplanation),
        checked(`/risk/${encodeURIComponent(id)}`, assertRisk),
      ]);
      const labels = ['Predicción', 'Explicación', 'Riesgo'];
      const avisos = [];
      const values = results.map((result, i) => {
        if (result.status === 'rejected') {
          if (['PARCEL_NOT_FOUND', 'INVALID_RESPONSE'].includes(result.reason.code)) throw result.reason;
          avisos.push(`${labels[i]}: ${result.reason.message}`);
          return null;
        }
        const body = result.value;
        if (body.parcel_id !== id || !sameContext(parcel.meta, body.meta)) throw new ApiError('INVALID_RESPONSE', 200);
        return body;
      });
      const [prediction, explanation, risk] = values;
      for (const item of [explanation, risk]) {
        if (item?.status === 'available' && (!prediction || item.model_version !== prediction.model_version)) throw new ApiError('INVALID_RESPONSE', 200);
      }
      if (explanation?.status === 'unavailable') avisos.push('Explicación todavía no disponible.');
      if (risk?.status === 'unavailable') avisos.push('Riesgo todavía no disponible.');
      return {
        ...parcel,
        rendimiento_t_ha: prediction?.prediction ?? null,
        prediction_unit: prediction?.unit ?? null,
        model_version: prediction?.model_version ?? null,
        rango_probable: prediction?.lower !== null && prediction?.lower !== undefined ? [prediction.lower, prediction.upper] : null,
        interval_level: prediction?.interval_level ?? null,
        interval_method: prediction?.interval_method ?? null,
        riesgo: ({ low: 'bajo', medium: 'medio', high: 'alto' })[risk?.level] ?? null,
        riesgo_descripcion: risk?.description ?? null,
        risk_method_version: risk?.method_version ?? null,
        shap: explanation?.status === 'available' ? explanation.features.map((f) => ({ categoria: f.feature, etiqueta: f.friendly_name, valor: f.impact })) : [],
        explanation: explanation?.status === 'available' ? explanation : null,
        avisos,
      };
    },
    // La ficha de validación es un artefacto del frontend, contrastado mediante /predict; no añade endpoints.
    async getVecinos() { return []; },
    async getCortesTemporales() { return []; },
    async getMetricasModelo() {
      if (!modelEvidence) return null;
      const ref = modelEvidence.reference_prediction;
      if (!ref?.parcel_id) throw new ApiError('MODEL_EVIDENCE_MISMATCH');
      const prediction = await checked(`/predict/${encodeURIComponent(ref.parcel_id)}`, assertPrediction);
      if (prediction.meta.mode === 'mock') return null;
      try { return verifyModelEvidence(modelEvidence, prediction); }
      catch { throw new ApiError('MODEL_EVIDENCE_MISMATCH'); }
    },
    async getResumenGlobal() { return null; },
    async getContextoMunicipal(id) {
      const parcel = await detail(id);
      if (parcel.region === null) return null;
      const summary = await getRegion(parcel.region);
      if (!sameContext(parcel.meta, summary.meta)) throw new ApiError('INVALID_RESPONSE', 200);
      return summary;
    },
    async getRegionResumen() {
      const body = await catalog();
      const regions = [...new Set(body.items.map((p) => p.region).filter((r) => r !== null))].sort();
      const results = await Promise.allSettled(regions.map(getRegion));
      const items = [], unavailable = [];
      results.forEach((result, i) => {
        if (result.status === 'rejected') {
          if (result.reason.code === 'INVALID_RESPONSE') throw result.reason;
          unavailable.push({ region: regions[i], code: result.reason.code, message: result.reason.message });
        } else {
          if (!sameContext(body.meta, result.value.meta)) throw new ApiError('INVALID_RESPONSE', 200);
          items.push(result.value);
        }
      });
      return { items, unavailable, unassigned_count: body.items.filter((p) => p.region === null).length, meta: body.meta };
    },
  };
}
