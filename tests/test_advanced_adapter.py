import json

import pandas as pd
import pytest

from ml.integration import _advanced
from ml.data_handoff import DataHandoffError


@pytest.fixture
def advanced(tmp_path):
    base = tmp_path / 'rol3'
    for folder in ['shap_yield_v1', 'intervalos_yield_v1', 'riesgo_yield_v1']:
        (base / folder).mkdir(parents=True)
    schema = {'model_version': 'yield-v1', 'data_version': 'test', 'model_sha256': 'test',
              'prediction_unit': 't/ha', 'features': ['a', 'b']}
    (base / 'shap_yield_v1/shap_metadata_yield_v1.json').write_text(json.dumps({
        **schema, 'method': 'shap.LinearExplainer', 'unit': 't/ha'}))
    pd.DataFrame([{'parcel_id': '001', 'prediccion_t_ha': 3., 'prediccion_reconstruida_t_ha': 3.,
                   'valor_base_shap_t_ha': 2., 'a': 2., 'b': -1.}]).to_csv(base / 'shap_yield_v1/shap_valores_yield_v1.csv', index=False)
    (base / 'intervalos_yield_v1/metadata_intervalos_yield_v1.json').write_text(json.dumps({
        'model_version': 'yield-v1', 'data_version': 'test', 'nominal_level': .9}))
    pd.DataFrame([{'parcel_id': '001', 'model_version': 'yield-v1', 'rendimiento_pred_t_ha': 3.,
                   'limite_inferior_t_ha': 2., 'limite_superior_t_ha': 4., 'margen_exploratorio_t_ha': 1.}]).to_csv(
        base / 'intervalos_yield_v1/predicciones_intervalos_yield_v1.csv', index=False)
    (base / 'riesgo_yield_v1/predicciones_riesgo_yield_v1.csv').write_text('parcel_id\n001\n')
    (base / 'riesgo_yield_v1/metadata_riesgo_yield_v1.json').write_text('{}')
    return tmp_path, schema


def test_adapter_preserves_explanation_and_does_not_invent_risk(advanced):
    results, schema = advanced
    explanations, intervals, metadata = _advanced(results, schema, {'001': 3.})
    row = explanations['001']
    assert row['features'][0]['feature'] == 'a'
    assert row['features'][1]['direction'] == 'negative'
    assert row['base_value'] + sum(f['impact'] for f in row['features']) == row['explained_output']
    assert intervals['001']['interval_level'] == .9
    assert metadata['risk']['status'] == 'unavailable'
    assert metadata['risk']['method_version'] is None


def test_wrong_model_is_rejected(advanced):
    results, schema = advanced
    schema['model_sha256'] = 'other'
    with pytest.raises(DataHandoffError, match='otra entrega'):
        _advanced(results, schema, {'001': 3.})


def test_explanation_cannot_reuse_ids_with_different_predictions(advanced):
    results, schema = advanced
    with pytest.raises(DataHandoffError, match='no reconstruye'):
        _advanced(results, schema, {'001': 5.})
