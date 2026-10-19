import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createApiRepository } from '../src/data/api/ApiRepository.js';
const report = JSON.parse(readFileSync(new URL('../src/data/model/model-evidence.json', import.meta.url), 'utf8'));
const prediction = () => ({ ...report.reference_prediction, lower: null, upper: null, interval_level: null, interval_method: null, meta: { ...report.meta } });
function repository(body, evidence = report) {
  const calls = [];
  return { calls, repo: createApiRepository({ modelEvidence: evidence, fetchImpl: async (url) => {
    calls.push(url);
    return { ok: true, status: 200, json: async () => body };
  } }) };
}
test('ficha real usa una ruta existente y conserva los pares OOF y métricas', async () => {
  const { repo, calls } = repository(prediction());
  const evidence = await repo.getMetricasModelo();
  assert.equal(evidence.model_version, 'yield-v1');
  assert.equal(evidence.rmse, 0.514672258022233);
  assert.equal(evidence.oof.points.length, 138);
  assert.equal(evidence.features.length, 30);
  assert.deepEqual(calls, ['/predict/' + report.reference_prediction.parcel_id]);
  assert.ok(evidence.oof.points.every((p) => Number.isFinite(p.observed) && Number.isFinite(p.predicted)));
});
for (const field of ['model_version', 'prediction', 'unit', 'cycle', 'data_cutoff', 'parcel_id']) {
  test(`rechaza ficha incompatible por ${field}`, async () => {
    const body = prediction();
    if (['cycle', 'data_cutoff'].includes(field)) body.meta[field] = 'other';
    else body[field] = field === 'prediction' ? body.prediction + 1 : 'other';
    const { repo } = repository(body);
    await assert.rejects(repo.getMetricasModelo());
  });
}
test('API mock no recibe las métricas reales', async () => {
  const body = prediction(); body.meta.mode = 'mock'; body.unit = 'mock_unit'; body.model_version = 'mock-v1';
  assert.equal(await repository(body).repo.getMetricasModelo(), null);
});
test('ficha sin pares OOF válidos no se muestra como evidencia', async () => {
  const invalid = structuredClone(report); invalid.oof.points[0].predicted = null;
  await assert.rejects(repository(prediction(), invalid).repo.getMetricasModelo(), { code: 'MODEL_EVIDENCE_MISMATCH' });
});
