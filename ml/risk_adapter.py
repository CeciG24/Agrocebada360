"""Adaptación offline de P3.9: verifica resultados existentes, no entrena detectores."""
from collections import Counter

import numpy as np
import pandas as pd

from ml.artifact_contract import sha256
from ml.data_handoff import DataHandoffError
from ml.model_bundle import read_json

METHOD_VERSION = 'review-priority-adapter-v1'
PRIORITY_LEVELS = {
    'Prioridad alta de revision': 'high',
    'Revisar rendimiento estimado': 'medium',
    'Revisar caracteristicas inusuales': 'medium',
    'Sin alerta combinada': 'low',
}
DISCLAIMER = ('Prioridad operativa relativa al conjunto evaluado; no es una probabilidad de pérdida '
              'ni riesgo crediticio. Una alerta OOD no confirma un error predictivo; '
              'sin alerta combinada no significa ausencia de riesgo.')


def description(priority):
    return f'{priority}. {DISCLAIMER}'


def adapt_risk(results, schema, predictions):
    paths = {
        'risk': results / 'rol3/riesgo_yield_v1/predicciones_riesgo_yield_v1.csv',
        'risk_meta': results / 'rol3/riesgo_yield_v1/metadata_riesgo_yield_v1.json',
        'ood': results / 'rol3/ood_yield_v1/predicciones_ood_yield_v1.csv',
        'ood_meta': results / 'rol3/ood_yield_v1/metadata_ood_yield_v1.json',
    }
    risk_meta, ood_meta = read_json(paths['risk_meta']), read_json(paths['ood_meta'])
    if (any(ood_meta.get(key) != schema[key] for key in ['model_version', 'data_version', 'model_sha256'])
            or risk_meta.get('model_version') != schema['model_version']
            or ood_meta.get('method') != 'IsolationForest'
            or risk_meta.get('classification_method') != 'Terciles de predicciones de evaluacion'
            or risk_meta.get('priority_method') != 'Rendimiento bajo relativo y alerta OOD'):
        raise DataHandoffError('Riesgo/OOD pertenece a otro modelo, datos o metodología.')
    frames = {}
    for name in ['risk', 'ood']:
        frame = pd.read_csv(paths[name], dtype={'parcel_id': str, 'alerta_ood': str})
        if (frame.parcel_id.isna().any() or frame.parcel_id.duplicated().any()
                or set(frame.parcel_id) != set(predictions)
                or not frame.model_version.eq(schema['model_version']).all()):
            raise DataHandoffError('IDs o versión incompatibles en riesgo/OOD.')
        frame = frame.set_index('parcel_id').loc[list(predictions)]
        for col in ['rendimiento_pred_t_ha', 'score_ood', 'umbral_ood']:
            if not np.isfinite(frame[col].to_numpy(float)).all():
                raise DataHandoffError('Valores no finitos en riesgo/OOD.')
        if (not np.allclose(frame.rendimiento_pred_t_ha, list(predictions.values()), atol=1e-8, rtol=0)
                or not frame.alerta_ood.isin(['True', 'False']).all()):
            raise DataHandoffError('Predicciones o alertas incompatibles en riesgo/OOD.')
        frames[name] = frame
    risk, ood = frames['risk'], frames['ood']
    for col in ['score_ood', 'umbral_ood', 'rendimiento_pred_t_ha']:
        if not np.allclose(risk[col], ood[col], atol=1e-8, rtol=0):
            raise DataHandoffError('Riesgo no coincide con la fuente OOD.')
    threshold = ood_meta['threshold']
    flags = ood.alerta_ood.eq('True')
    if (not np.isfinite(threshold) or not np.allclose(ood.umbral_ood, threshold, atol=1e-8, rtol=0)
            or not flags.equals(ood.score_ood.lt(threshold))
            or not risk.alerta_ood.equals(ood.alerta_ood)):
        raise DataHandoffError('Alertas o umbral OOD inconsistentes.')
    q1, q2 = risk.rendimiento_pred_t_ha.quantile([1 / 3, 2 / 3]).tolist()
    if (not np.allclose([risk_meta['tercile_1'], risk_meta['tercile_2']], [q1, q2], atol=1e-8, rtol=0)
            or risk_meta['n_parcels'] != len(predictions)
            or risk_meta['n_ood_alerts'] != int(flags.sum()) or ood_meta['n_alerts'] != int(flags.sum())):
        raise DataHandoffError('Metadatos de riesgo incompatibles con las evaluaciones.')
    rows = {}
    for parcel_id, row in risk.iterrows():
        relative = ('Bajo relativo' if row.rendimiento_pred_t_ha <= q1 else
                    'Intermedio relativo' if row.rendimiento_pred_t_ha <= q2 else 'Alto relativo')
        low, outlier = relative == 'Bajo relativo', row.alerta_ood == 'True'
        expected = ('Prioridad alta de revision' if low and outlier else
                    'Revisar rendimiento estimado' if low else
                    'Revisar caracteristicas inusuales' if outlier else 'Sin alerta combinada')
        if row.nivel_relativo != relative or row.prioridad_revision != expected:
            raise DataHandoffError('La prioridad no respeta las reglas publicadas de P3.9.')
        rows[parcel_id] = {
            'parcel_id': parcel_id, 'status': 'available', 'reason': None,
            'level': PRIORITY_LEVELS[expected], 'method_version': METHOD_VERSION,
            'model_version': schema['model_version'], 'description': description(expected),
            'meta': {'mode': 'real', 'contract_version': '0.1.0',
                     'cycle': '2025-04/2025-10', 'data_cutoff': '2025-10-31'},
        }
    if (risk_meta['relative_levels'] != dict(Counter(risk.nivel_relativo))
            or risk_meta['review_priorities'] != dict(Counter(risk.prioridad_revision))):
        raise DataHandoffError('Los conteos publicados de riesgo no coinciden.')
    method = {
        'method_version': METHOD_VERSION, 'model_version': schema['model_version'],
        'model_sha256': schema['model_sha256'], 'data_version': schema['data_version'],
        'scope': 'Prioridades P3.9; mapeo de API definido por el equipo en P4.14, no por FIRA.',
        'priority_levels': PRIORITY_LEVELS, 'tercile_1': q1, 'tercile_2': q2,
        'ood_threshold': threshold, 'limitations': DISCLAIMER,
        'reference_predictions': predictions,
        'producer_files_sha256': {p.relative_to(results).as_posix(): sha256(p) for p in paths.values()},
    }
    return rows, method
