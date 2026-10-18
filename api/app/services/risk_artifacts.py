"""Carga atómica del módulo opcional de prioridades; sin clasificación en HTTP."""
import math

from api.app.schemas.common import Meta
from api.app.schemas.risk import Risk


def load_risks(delivery, manifest, pipeline, parcels, model_sha256):
    from ml.artifact_contract import sha256
    from ml.model_bundle import read_json
    from ml.risk_adapter import METHOD_VERSION, PRIORITY_LEVELS, description

    names = ['risks.json', 'risk_method.json']
    declared = [name in manifest['files_sha256'] for name in names]
    if not any(declared):
        if manifest.get('advanced', {}).get('risk', {}).get('status') == 'available':
            raise ValueError('Riesgo disponible declarado sin artefactos.')
        return {}  # Entregas anteriores sin módulo: ausencia esperada.
    if not all(declared):
        raise ValueError('Módulo de riesgo incompleto.')
    for name in names:
        if sha256(delivery / name) != manifest['files_sha256'][name]:
            raise ValueError('Artefacto de riesgo alterado.')
    method = read_json(delivery / 'risk_method.json')
    if (method['method_version'] != METHOD_VERSION or method['priority_levels'] != PRIORITY_LEVELS
            or method['model_version'] != pipeline.model_version
            or method['model_sha256'] != model_sha256 or method['data_version'] != manifest['data_version']):
        raise ValueError('Riesgo incompatible con el modelo/dataset o metodología.')
    rows = read_json(delivery / 'risks.json')
    predictions = method['reference_predictions']
    if (not isinstance(rows, dict) or not isinstance(predictions, dict)
            or set(rows) != set(predictions) or set(rows) - set(parcels)
            or ('n_eval' in manifest and len(rows) != manifest['n_eval'])):
        raise ValueError('IDs de riesgo incompatibles.')
    valid_descriptions = {description(priority): level for priority, level in PRIORITY_LEVELS.items()}
    validated = {}
    for parcel_id, payload in rows.items():
        row = Risk.model_validate(payload)
        value = predictions[parcel_id]
        if (row.parcel_id != parcel_id or row.meta != Meta(mode='real') or row.status != 'available'
                or row.method_version != METHOD_VERSION or row.model_version != pipeline.model_version
                or valid_descriptions.get(row.description) != row.level
                or isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
                or not math.isclose(value, pipeline.predict(parcel_id), abs_tol=1e-8, rel_tol=0)):
            raise ValueError('Evaluación de riesgo incompatible con la salida/contexto del modelo.')
        validated[parcel_id] = row
    return validated
