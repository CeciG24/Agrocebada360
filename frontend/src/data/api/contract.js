import { esGeometriaValida } from '../../lib/geo.js';

const fail = () => { throw new Error('Respuesta incompatible con API 0.1.0'); };
const text = (v) => typeof v === 'string' && v.trim().length > 0;
const finite = (v) => typeof v === 'number' && Number.isFinite(v);
const nullableText = (v) => v === null || text(v);

export function assertMeta(meta) {
  if (!meta || meta.contract_version !== '0.1.0' || !['mock', 'real'].includes(meta.mode)
      || meta.cycle !== '2025-04/2025-10' || meta.data_cutoff !== '2025-10-31') fail();
}

export function sameContext(a, b) {
  return ['contract_version', 'mode', 'cycle', 'data_cutoff'].every((key) => a[key] === b[key]);
}

export function assertParcel(p, includeGeometry) {
  if (!text(p.id) || !nullableText(p.region)) fail();
  if (includeGeometry && !esGeometriaValida(p.geometry)) fail();
  if (!includeGeometry && 'geometry' in p) fail();
}

export function assertPrediction(p) {
  if (!text(p.parcel_id) || !finite(p.prediction) || !text(p.unit) || !text(p.model_version)) fail();
  if (p.meta.mode === 'real' && p.unit !== 't/ha') fail();
  const values = [p.lower, p.upper, p.interval_level, p.interval_method];
  if (values.every((v) => v === null)) return;
  if (!finite(p.lower) || !finite(p.upper) || !finite(p.interval_level) || !text(p.interval_method)
      || p.interval_level <= 0 || p.interval_level >= 1 || p.lower > p.prediction || p.upper < p.prediction) fail();
}

export function assertExplanation(e) {
  if (!text(e.parcel_id) || !Array.isArray(e.features)) fail();
  if (e.status === 'unavailable') {
    if (e.reason !== 'EXPLANATION_NOT_READY' || e.features.length ||
        ['method', 'model_version', 'output_space', 'base_value', 'explained_output'].some((k) => e[k] !== null)) fail();
    return;
  }
  if (e.status !== 'available' || e.reason !== null || e.method !== 'shap' || !text(e.model_version)
      || !text(e.output_space) || !finite(e.base_value) || !finite(e.explained_output) || !e.features.length) fail();
  const names = new Set();
  e.features.forEach((f, i) => {
    const direction = f.impact > 0 ? 'positive' : f.impact < 0 ? 'negative' : 'neutral';
    if (!text(f.feature) || !text(f.friendly_name) || !finite(f.impact) || f.direction !== direction || names.has(f.feature)) fail();
    if (i > 0) {
      const prev = e.features[i - 1];
      if (Math.abs(prev.impact) < Math.abs(f.impact) || (Math.abs(prev.impact) === Math.abs(f.impact) && prev.feature > f.feature)) fail();
    }
    names.add(f.feature);
  });
}

export function assertRisk(r) {
  if (!text(r.parcel_id)) fail();
  if (r.status === 'unavailable') {
    if (r.reason !== 'RISK_NOT_READY' || ['level', 'method_version', 'model_version', 'description'].some((k) => r[k] !== null)) fail();
    return;
  }
  if (r.status !== 'available' || r.reason !== null || !['low', 'medium', 'high'].includes(r.level)
      || !text(r.method_version) || !text(r.model_version) || !text(r.description)) fail();
}

export function assertRegion(r) {
  if (!text(r.region) || !Number.isInteger(r.parcel_count) || r.parcel_count < 1
      || !Number.isInteger(r.predicted_count) || r.predicted_count < 0 || r.predicted_count > r.parcel_count) fail();
  if (r.predicted_count === 0) {
    if ([r.mean_prediction, r.unit, r.model_version].some((v) => v !== null)) fail();
  } else if (!finite(r.mean_prediction) || !text(r.unit) || !text(r.model_version) || (r.meta.mode === 'real' && r.unit !== 't/ha')) fail();
}
