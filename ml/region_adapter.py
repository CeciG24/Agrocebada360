"""Agrupación documentada por estado/municipio; no modifica el modelo ni los datos."""
import csv
import math
from pathlib import Path

from ml.artifact_contract import sha256
from ml.data_handoff import DataHandoffError
from ml.model_bundle import read_json

REGION_POLICY_PATH = Path(__file__).resolve().parents[1] / 'api/app/catalogs/regions.json'


def build_regions(data_root, schema, predictions):
    policy = read_json(REGION_POLICY_PATH)
    if (policy['region_definition_version'] != 'state-regions-v1'
            or policy['summary_population'] != 'evaluation_predictions_only'):
        raise DataHandoffError('Política regional incompatible.')
    mapping, keys = {}, set()
    for region in policy['regions']:
        key = region['region_key']
        if (not isinstance(key, str) or not key.strip() or key in keys
                or not region['region_label'].strip() or not region['region_source'].startswith('https://')):
            raise DataHandoffError('Definición regional inválida o duplicada.')
        keys.add(key)
        for municipality in region['municipios_presentes']:
            pair = (region['state'], municipality)
            if pair in mapping:
                raise DataHandoffError('Un municipio tiene más de una región.')
            mapping[pair] = key
    master_path = Path(data_root) / 'parcel_master.csv'
    with master_path.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    assignments, eval_ids = {}, set()
    for row in rows:
        parcel_id = row['parcel_id']
        pair = (row['estado'], row['municipio'])
        if not parcel_id.strip() or parcel_id in assignments or pair not in mapping:
            raise DataHandoffError('ID duplicado o municipio sin correspondencia regional.')
        if row['dataset_split'] not in ['ENTRENAMIENTO', 'PREDICCION']:
            raise DataHandoffError('Partición desconocida para la cobertura regional.')
        assignments[parcel_id] = mapping[pair]
        if row['dataset_split'] == 'PREDICCION':
            eval_ids.add(parcel_id)
    if (not assignments or set(predictions) != eval_ids
            or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
                   for v in predictions.values()) or schema['prediction_unit'] != 't/ha'):
        raise DataHandoffError('La población regional no coincide con las predicciones de evaluación.')
    return {
        'region_definition_version': policy['region_definition_version'],
        'policy_sha256': sha256(REGION_POLICY_PATH), 'policy': policy,
        'parcel_master_sha256': sha256(master_path),
        'model_version': schema['model_version'], 'model_sha256': schema['model_sha256'],
        'data_version': schema['data_version'], 'prediction_unit': schema['prediction_unit'],
        'assignments': assignments, 'evaluation_predictions': predictions,
        'meta': {'mode': 'real', 'contract_version': '0.1.0',
                 'cycle': '2025-04/2025-10', 'data_cutoff': '2025-10-31'},
    }


def load_regions(delivery, manifest, data_root, parcels):
    expected_hash = manifest['files_sha256'].get('regions.json')
    if expected_hash is None:
        if any(p.region is not None for p in parcels.values()) or isinstance(manifest.get('regions'), dict):
            raise DataHandoffError('Regiones declaradas sin fuente integrada.')
        return None
    path = Path(delivery) / 'regions.json'
    if sha256(path) != expected_hash:
        raise DataHandoffError('Artefacto regional alterado.')
    artifact = read_json(path)
    schema = {key: artifact[key] for key in ['model_version', 'model_sha256']}
    schema['data_version'] = manifest['data_version']
    schema['prediction_unit'] = 't/ha'
    expected = build_regions(data_root, schema, artifact['evaluation_predictions'])
    if artifact != expected or {key: p.region for key, p in parcels.items()} != artifact['assignments']:
        raise DataHandoffError('Asignaciones/contexto regional incompatibles con la fuente.')
    return artifact


def verified_summaries(artifact, parcels, pipeline, model_sha256):
    from api.app.schemas.prediction import Prediction
    from api.app.schemas.common import Meta
    if (artifact['model_version'] != pipeline.model_version or artifact['model_sha256'] != model_sha256
            or artifact['prediction_unit'] != pipeline.unit):
        raise DataHandoffError('El resumen no pertenece al modelo cargado.')
    predictions = {}
    for key, value in artifact['evaluation_predictions'].items():
        if not math.isclose(value, pipeline.predict(key), abs_tol=1e-8, rel_tol=0):
            raise DataHandoffError('Una predicción regional no corresponde al modelo congelado.')
        predictions[key] = Prediction(parcel_id=key, prediction=value, unit=pipeline.unit,
                                     model_version=pipeline.model_version, lower=None, upper=None,
                                     interval_level=None, interval_method=None, meta=Meta(mode='real'))
    from api.app.services.region_summary import summarize_regions
    return summarize_regions(parcels, predictions, 'real')
