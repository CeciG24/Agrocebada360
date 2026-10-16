import test from 'node:test';
import assert from 'node:assert/strict';
import { createApiRepository } from '../src/data/api/ApiRepository.js';

const meta = { contract_version: '0.1.0', mode: 'real', cycle: '2025-04/2025-10', data_cutoff: '2025-10-31' };
const geometry = { type: 'Polygon', coordinates: [[[-100, 20], [-99, 20], [-99, 21], [-100, 20]]] };
const absent = (kind, id) => kind === 'explain' ? {
  parcel_id: id, status: 'unavailable', reason: 'EXPLANATION_NOT_READY', method: null, model_version: null,
  output_space: null, base_value: null, explained_output: null, features: [], meta,
} : { parcel_id: id, status: 'unavailable', reason: 'RISK_NOT_READY', level: null, method_version: null, model_version: null, description: null, meta };
const prediction = (id) => ({ parcel_id: id, prediction: 3.123456789, unit: 't/ha', lower: null, upper: null,
  interval_level: null, interval_method: null, model_version: 'yield-v1', meta });

function fixture({ id = '0001', parcels, overrides = {}, context = meta } = {}) {
  const calls = [];
  const items = parcels ?? [{ id, region: 'zona A/1', geometry }];
  const repository = createApiRepository({ baseUrl: 'http://api.test', fetchImpl: async (url) => {
    calls.push(url);
    const parsed = new URL(url);
    const path = parsed.pathname;
    let body;
    if (path === '/parcels') body = { items: items.map((p) => parsed.searchParams.get('include_geometry') === 'true'
      ? p : { id: p.id, region: p.region }), total: items.length, meta: context };
    else if (path === `/parcel/${encodeURIComponent(id)}`) body = { ...items[0], meta: context };
    else if (path === `/predict/${encodeURIComponent(id)}`) body = { ...prediction(id), meta: context };
    else if (path === `/explain/${encodeURIComponent(id)}`) body = { ...absent('explain', id), meta: context };
    else if (path === `/risk/${encodeURIComponent(id)}`) body = { ...absent('risk', id), meta: context };
    else if (path.startsWith('/regions/')) body = { region: decodeURIComponent(path.slice(9)), parcel_count: items.length,
      predicted_count: 1, mean_prediction: 3.12, unit: 't/ha', model_version: 'yield-v1', meta: context };
    else assert.fail(`Ruta fuera de contrato: ${path}`);
    const replacement = overrides[path];
    if (replacement instanceof Error) throw replacement;
    const value = replacement ?? body;
    return { ok: !value.error, status: value.error ? value.httpStatus ?? 503 : 200, json: async () => value };
  } });
  return { repository, calls };
}

test('197 parcelas y geometrías en una consulta compartida, preservando IDs y null', async () => {
  const parcels = Array.from({ length: 197 }, (_, i) => ({ id: String(i).padStart(4, '0'), region: null, geometry: i === 0 ? null : geometry }));
  const { repository, calls } = fixture({ parcels });
  const [items, fc] = await Promise.all([repository.getAllParcelas(), repository.getGeometrias()]);
  assert.equal(calls.length, 1);
  assert.equal(new URL(calls[0]).pathname, '/parcels');
  assert.equal(new URL(calls[0]).searchParams.get('include_geometry'), 'true');
  assert.equal(items.length, 197);
  assert.equal(items[0].id, '0000');
  assert.equal(items[0].geometry, null);
  assert.equal(fc.features.length, 196);
  assert.equal(fc.features[0].properties.id, '0001');
});

test('variante sin geometrías y filtro regional usan parámetros canónicos', async () => {
  const { repository, calls } = fixture();
  const body = await repository.getParcelList({ region: 'zona A/1' });
  assert.equal('geometry' in body.items[0], false);
  const params = new URL(calls[0]).searchParams;
  assert.equal(params.get('region'), 'zona A/1');
  assert.equal(params.get('include_geometry'), 'false');
});

test('detalle compone rutas públicas, codifica ID opaco y conserva precisión', async () => {
  const id = '00 A/á?#';
  const { repository, calls } = fixture({ id });
  const p = await repository.getParcelaById(id);
  assert.equal(p.id, id);
  assert.equal(p.rendimiento_t_ha, 3.123456789);
  assert.equal(p.rango_probable, null);
  assert.equal(p.riesgo, null);
  assert.deepEqual(p.shap, []);
  assert.deepEqual(calls.map((url) => new URL(url).pathname), ['parcel', 'predict', 'explain', 'risk'].map((name) => `/${name}/${encodeURIComponent(id)}`));
  assert.equal('superficie_ha' in p, false);
});

test('503 no se convierte en cero, intervalo ni mock', async () => {
  const { repository } = fixture({ overrides: { '/predict/0001': { error: { code: 'PREDICTION_UNAVAILABLE', details: [] } } } });
  const p = await repository.getParcelaById('0001');
  assert.equal(p.rendimiento_t_ha, null);
  assert.equal(p.rango_probable, null);
  assert.equal(p.meta.mode, 'real');
  assert.match(p.avisos.join(' '), /predicción no está disponible/i);
});

test('rutas opcionales todavía ausentes dejan avisos legibles', async () => {
  const missing = { httpStatus: 404, error: { code: 'ROUTE_NOT_FOUND', details: [] } };
  const { repository } = fixture({ overrides: { '/explain/0001': missing, '/risk/0001': missing } });
  const p = await repository.getParcelaById('0001');
  assert.equal(p.rendimiento_t_ha, 3.123456789);
  assert.deepEqual(p.shap, []);
  assert.equal(p.riesgo, null);
  assert.match(p.avisos.join(' '), /todavía no está disponible/);
});

test('404 de parcela se conserva por código y estado HTTP', async () => {
  const { repository } = fixture({ overrides: { '/parcel/0001': { httpStatus: 404, error: { code: 'PARCEL_NOT_FOUND', details: [] } } } });
  await assert.rejects(repository.getParcelaById('0001'), (e) => e.code === 'PARCEL_NOT_FOUND' && e.status === 404);
});

test('conserva unidad y origen mock declarados por API', async () => {
  const context = { ...meta, mode: 'mock' };
  const { repository } = fixture({ context, overrides: { '/predict/0001': { ...prediction('0001'), unit: 'mock_unit', meta: context } } });
  const p = await repository.getParcelaById('0001');
  assert.equal(p.prediction_unit, 'mock_unit');
  assert.equal(p.meta.mode, 'mock');
});

test('rechaza mezclar mock/real, ciclos y versiones del contrato', async () => {
  for (const wrong of [{ ...meta, mode: 'mock' }, { ...meta, cycle: '2026' }, { ...meta, contract_version: '9.0' }]) {
    const { repository } = fixture({ overrides: { '/predict/0001': { ...prediction('0001'), meta: wrong } } });
    await assert.rejects(repository.getParcelaById('0001'), { code: 'INVALID_RESPONSE' });
  }
});

test('rechaza NaN, unidad real equivocada e intervalos parciales o invertidos', async () => {
  for (const wrong of [{ prediction: NaN }, { unit: 'kg/ha' }, { lower: 2 },
    { lower: 4, upper: 5, interval_level: 0.9, interval_method: 'example' }]) {
    const { repository } = fixture({ overrides: { '/predict/0001': { ...prediction('0001'), ...wrong } } });
    await assert.rejects(repository.getParcelaById('0001'), { code: 'INVALID_RESPONSE' });
  }
});

test('SHAP preserva features/escala y rechaza otra versión del modelo', async () => {
  const explanation = { parcel_id: '0001', status: 'available', reason: null, method: 'shap', model_version: 'yield-v1',
    output_space: 't/ha', base_value: 3, explained_output: 3.123456789,
    features: [{ feature: 'clima', friendly_name: 'Clima', impact: 0.123456789, direction: 'positive' }], meta };
  const { repository } = fixture({ overrides: { '/explain/0001': explanation } });
  const p = await repository.getParcelaById('0001');
  assert.equal(p.shap[0].valor, 0.123456789);
  assert.equal(p.explanation.output_space, 't/ha');
  const wrong = fixture({ overrides: { '/explain/0001': { ...explanation, model_version: 'old-v0' } } });
  await assert.rejects(wrong.repository.getParcelaById('0001'), { code: 'INVALID_RESPONSE' });
});

test('regiones usan claves del catálogo y preservan cobertura parcial/cero', async () => {
  const parcels = [{ id: '0001', region: 'A /#', geometry: null }, { id: '0002', region: 'B', geometry: null }, { id: '0003', region: null, geometry: null }];
  const zero = { region: 'B', parcel_count: 1, predicted_count: 0, mean_prediction: null, unit: null, model_version: null, meta };
  const { repository, calls } = fixture({ parcels, overrides: { '/regions/B': zero } });
  const data = await repository.getRegionResumen();
  assert.equal(data.items[0].predicted_count, 1);
  assert.equal(data.items[0].parcel_count, 3);
  assert.equal(data.items[1].mean_prediction, null);
  assert.equal(data.unassigned_count, 1);
  assert.ok(calls.some((url) => url.endsWith(`/regions/${encodeURIComponent('A /#')}`)));
});

test('región no disponible permanece ausente, sin agrupar por municipio', async () => {
  const { repository } = fixture({ overrides: { '/regions/zona%20A%2F1': { error: { code: 'REGION_DATA_UNAVAILABLE' } } } });
  const data = await repository.getRegionResumen();
  assert.deepEqual(data.items, []);
  assert.equal(data.unavailable[0].code, 'REGION_DATA_UNAVAILABLE');
});

test('rechaza catálogo con duplicados, geometría corrupta o total incoherente', async () => {
  for (const bad of [
    { items: [{ id: '1', region: null, geometry: null }], total: 197, meta },
    { items: [{ id: '1', region: null, geometry: null }, { id: '1', region: null, geometry: null }], total: 2, meta },
    { items: [{ id: '1', region: null, geometry: { type: 'Polygon', coordinates: [[]] } }], total: 1, meta },
  ]) {
    const { repository } = fixture({ overrides: { '/parcels': bad } });
    await assert.rejects(repository.getAllParcelas(), { code: 'INVALID_RESPONSE' });
  }
});

test('funciones fuera del contrato no realizan HTTP ni fabrican resultados', async () => {
  const { repository, calls } = fixture();
  assert.deepEqual(await repository.getVecinos('0001'), []);
  assert.deepEqual(await repository.getCortesTemporales('0001'), []);
  assert.equal(await repository.getMetricasModelo(), null);
  assert.equal(await repository.getResumenGlobal(), null);
  assert.deepEqual(calls, []);
});

test('un catálogo fallido se puede reintentar sin heredar un rechazo cacheado', async () => {
  let attempts = 0;
  const repository = createApiRepository({ fetchImpl: async () => {
    attempts++;
    if (attempts === 1) throw new Error('offline');
    return { ok: true, status: 200, json: async () => ({ items: [], total: 0, meta }) };
  } });
  await assert.rejects(repository.getAllParcelas(), { code: 'NETWORK_ERROR' });
  assert.deepEqual(await repository.getAllParcelas(), []);
  assert.equal(attempts, 2);
});
