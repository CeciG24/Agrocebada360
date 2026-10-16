import assert from 'node:assert/strict';
import { createApiRepository } from '../src/data/api/ApiRepository.js';

const baseUrl = process.argv[2] ?? 'http://127.0.0.1:8000';
const calls = [];
const repository = createApiRepository({ baseUrl, fetchImpl: (url, options) => { calls.push(url); return fetch(url, options); } });
const [parcels, geometries] = await Promise.all([repository.getAllParcelas(), repository.getGeometrias()]);
assert.equal(calls.filter((url) => new URL(url).pathname === '/parcels').length, 1);
assert.ok(parcels.length > 0, 'La prueba necesita un catálogo no vacío');
const detail = await repository.getParcelaById(parcels[0].id);
assert.equal(detail.id, parcels[0].id);
assert.equal(detail.meta.mode, parcels[0].meta.mode);
assert.ok(detail.rendimiento_t_ha === null || Number.isFinite(detail.rendimiento_t_ha));
const regions = await repository.getRegionResumen();
console.log(JSON.stringify({ parcels: parcels.length, geometries: geometries.features.length, id: detail.id,
  mode: detail.meta.mode, prediction: detail.rendimiento_t_ha, unit: detail.prediction_unit,
  unavailable: detail.avisos, regions: regions.items.length, unavailableRegions: regions.unavailable.length }, null, 2));
