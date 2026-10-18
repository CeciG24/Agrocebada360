from collections import Counter
import json

import pandas as pd
import pytest

from api.app.schemas.risk import Risk, unavailable_risk
from ml.data_handoff import DataHandoffError
from ml.risk_adapter import adapt_risk


@pytest.fixture
def risk_sources(tmp_path):
    risk_dir = tmp_path / 'rol3/riesgo_yield_v1'
    ood_dir = tmp_path / 'rol3/ood_yield_v1'
    risk_dir.mkdir(parents=True)
    ood_dir.mkdir()
    predictions = {f'{i:03}': float(i) for i in range(1, 7)}
    schema = {'model_version': 'test-model', 'data_version': 'test-data', 'model_sha256': 'test-hash'}
    # Six ordered values: q1=2+2/3, q2=4+1/3. OOD on one low and one high yield.
    priorities = ['Prioridad alta de revision', 'Revisar rendimiento estimado',
                  'Sin alerta combinada', 'Sin alerta combinada',
                  'Revisar caracteristicas inusuales', 'Sin alerta combinada']
    relative = ['Bajo relativo'] * 2 + ['Intermedio relativo'] * 2 + ['Alto relativo'] * 2
    rows = [{'parcel_id': pid, 'rendimiento_pred_t_ha': value, 'model_version': 'test-model',
             'score_ood': -.8 if value in [1, 5] else -.1, 'alerta_ood': value in [1, 5],
             'umbral_ood': -.5} for pid, value in predictions.items()]
    pd.DataFrame(rows).to_csv(ood_dir / 'predicciones_ood_yield_v1.csv', index=False)
    for i, row in enumerate(rows):
        row.update(prioridad_revision=priorities[i], nivel_relativo=relative[i])
    pd.DataFrame(rows).to_csv(risk_dir / 'predicciones_riesgo_yield_v1.csv', index=False)
    (risk_dir / 'metadata_riesgo_yield_v1.json').write_text(json.dumps({
        'model_version': 'test-model', 'tercile_1': 8 / 3, 'tercile_2': 13 / 3,
        'n_parcels': 6, 'n_ood_alerts': 2, 'relative_levels': dict(Counter(relative)),
        'review_priorities': dict(Counter(priorities)),
        'classification_method': 'Terciles de predicciones de evaluacion',
        'priority_method': 'Rendimiento bajo relativo y alerta OOD'}), encoding='utf-8')
    (ood_dir / 'metadata_ood_yield_v1.json').write_text(json.dumps({
        **schema, 'method': 'IsolationForest', 'threshold': -.5, 'n_alerts': 2}), encoding='utf-8')
    return tmp_path, schema, predictions


def test_risk_mapping_preserves_all_four_producer_priorities(risk_sources):
    rows, method = adapt_risk(*risk_sources)
    assert [rows[f'{i:03}']['level'] for i in range(1, 7)] == ['high', 'medium', 'low', 'low', 'medium', 'low']
    assert len(method['producer_files_sha256']) == 4
    for row in rows.values():
        assert Risk.model_validate(row).status == 'available'
        assert 'no es una probabilidad' in row['description']
        assert 'no significa ausencia de riesgo' in row['description']


@pytest.mark.parametrize('damage', ['id', 'prediction', 'priority', 'relative', 'flag', 'nan', 'version'])
def test_incompatible_producer_result_is_rejected(risk_sources, damage):
    results, schema, predictions = risk_sources
    path = results / 'rol3/riesgo_yield_v1/predicciones_riesgo_yield_v1.csv'
    frame = pd.read_csv(path, dtype={'parcel_id': str})
    column, value = {
        'id': ('parcel_id', 'unknown'), 'prediction': ('rendimiento_pred_t_ha', 99.),
        'priority': ('prioridad_revision', 'Sin alerta combinada'),
        'relative': ('nivel_relativo', 'Alto relativo'), 'flag': ('alerta_ood', False),
        'nan': ('score_ood', float('nan')), 'version': ('model_version', 'other'),
    }[damage]
    frame.loc[0, column] = value
    frame.to_csv(path, index=False)
    with pytest.raises(DataHandoffError):
        adapt_risk(results, schema, predictions)


@pytest.mark.parametrize('key', ['model_version', 'model_sha256', 'data_version'])
def test_ood_cannot_cross_model_or_data_boundaries(risk_sources, key):
    results, schema, predictions = risk_sources
    schema[key] = 'wrong'
    with pytest.raises(DataHandoffError):
        adapt_risk(results, schema, predictions)


def test_unavailable_risk_requires_null_context():
    payload = unavailable_risk('001', 'real').model_dump()
    assert payload['reason'] == 'RISK_NOT_READY'
    payload['level'] = 'low'
    with pytest.raises(ValueError):
        Risk.model_validate(payload)
