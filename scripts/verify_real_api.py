"""Aceptación HTTP P4.8/P4.9 sobre una entrega integrada de confianza."""
import argparse
from collections import Counter
import json
import logging
import math
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
from fastapi.testclient import TestClient

from api.app.core.config import Settings
from api.app.main import create_app
from ml import inference
from ml.artifact_contract import sha256
from api.app.services.feature_labels import load_feature_labels


def verify(data_root, delivery):
    logging.getLogger('httpx').setLevel(logging.WARNING)
    root = Path(__file__).resolve().parents[1]
    expected = pd.read_csv(root / 'ml/results/predictions_raw.csv', dtype={'parcel_id': str})
    errors = []
    explanation_errors = []
    risk_levels = []
    risk_source = pd.read_csv(root / 'ml/results/rol3/riesgo_yield_v1/predicciones_riesgo_yield_v1.csv',
                              dtype={'parcel_id': str}).set_index('parcel_id')
    from ml.risk_adapter import METHOD_VERSION, PRIORITY_LEVELS
    loads = []
    original = inference._deserialize

    def counted(path):
        loads.append(str(path))
        return original(path)

    settings = Settings(mode='real', data_root=Path(data_root), delivery_path=Path(delivery))
    schema_path = Path(delivery) / 'model/feature_schema.json'
    schema = json.loads(schema_path.read_text(encoding='utf-8'))
    labels = load_feature_labels(schema['model_sha256'], sha256(schema_path))
    with patch.object(inference, '_deserialize', counted), TestClient(create_app(settings)) as client:
        response = client.get('/health')
        assert response.status_code == 200
        health = response.json()
        assert health['mode'] == 'real' and health['model_loaded'] and health['data_ready']
        plain = client.get('/parcels').json()
        mapped = client.get('/parcels?include_geometry=true').json()
        assert plain['meta']['mode'] == mapped['meta']['mode'] == 'real'
        ids = [p['id'] for p in plain['items']]
        assert ids == sorted(set(ids)) and len(ids) == mapped['total']
        assert all(set(p) == {'id', 'region'} for p in plain['items'])
        region_keys = sorted({p['region'] for p in plain['items'] if p['region'] is not None})
        regional_results = []
        expected_predictions = expected.set_index('parcel_id').rendimiento_pred_t_ha.to_dict()
        with patch.object(client.app.state.service._pipeline, 'predict', side_effect=AssertionError('Regional HTTP cannot infer')):
            for key in region_keys:
                members = [p['id'] for p in plain['items'] if p['region'] == key]
                values = [expected_predictions[i] for i in members if i in expected_predictions]
                response = client.get('/regions/' + key)
                assert response.status_code == 200
                summary = response.json()
                assert summary['parcel_count'] == len(members) and summary['predicted_count'] == len(values)
                assert summary['meta'] == plain['meta']
                if values:
                    assert abs(summary['mean_prediction'] - math.fsum(values) / len(values)) < 1e-8
                    assert summary['unit'] == 't/ha' and summary['model_version'] == expected.model_version.iloc[0]
                regional_results.append(summary)
        if region_keys:
            assert sum(row['parcel_count'] for row in regional_results) == len(ids)
            assert sum(row['predicted_count'] for row in regional_results) == len(expected)
            assert client.get('/regions/unknown-id').json()['error']['code'] == 'REGION_NOT_FOUND'
            assert client.get('/regions/%20').status_code == 422
        for parcel in mapped['items']:
            response = client.get('/parcel/' + parcel['id'])
            assert response.status_code == 200
            detail = response.json()
            assert set(detail) == {'id', 'region', 'geometry', 'meta'}
            assert {key: detail[key] for key in parcel} == parcel
        service = client.app.state.service
        with patch.object(service._pipeline._model, 'fit', side_effect=AssertionError('HTTP cannot train')):
            for row in expected.itertuples(index=False):
                response = client.get('/predict/' + row.parcel_id)
                assert response.status_code == 200
                prediction = response.json()
                assert prediction['meta']['mode'] == 'real' and prediction['unit'] == 't/ha'
                assert prediction['model_version'] == row.model_version
                assert all(prediction[key] is None for key in ['lower', 'upper', 'interval_level', 'interval_method'])
                errors.append(abs(prediction['prediction'] - row.rendimiento_pred_t_ha))
                response = client.get('/explain/' + row.parcel_id)
                assert response.status_code == 200
                explanation = response.json()
                assert explanation['status'] == 'available' and explanation['meta'] == prediction['meta']
                assert explanation['model_version'] == prediction['model_version']
                assert explanation['output_space'] == prediction['unit'] and len(explanation['features']) == 30
                for feature in explanation['features']:
                    assert feature['friendly_name'] == labels.get(feature['feature'], feature['feature'])
                explained = explanation['base_value'] + math.fsum(f['impact'] for f in explanation['features'])
                explanation_errors.append(abs(explained - prediction['prediction']))
                response = client.get('/risk/' + row.parcel_id)
                assert response.status_code == 200
                risk = response.json()
                assert risk['status'] == 'available' and risk['meta'] == prediction['meta']
                assert risk['model_version'] == prediction['model_version']
                assert risk['method_version'] == METHOD_VERSION
                assert risk['level'] == PRIORITY_LEVELS[risk_source.loc[row.parcel_id, 'prioridad_revision']]
                assert 'no es una probabilidad' in risk['description']
                risk_levels.append(risk['level'])
        assert max(errors) < 1e-8 and len(loads) == 1
        assert max(explanation_errors) < 1e-8
        split = json.loads((root / 'ml/split/official_ids_v1.json').read_text())
        unavailable = client.get('/explain/' + split['train_ids'][0])
        assert unavailable.status_code == 200 and unavailable.json()['reason'] == 'EXPLANATION_NOT_READY'
        unavailable = client.get('/risk/' + split['train_ids'][0])
        assert unavailable.status_code == 200 and unavailable.json()['reason'] == 'RISK_NOT_READY'
        for route in ['/parcel/unknown-id', '/predict/unknown-id', '/explain/unknown-id', '/risk/unknown-id']:
            response = client.get(route)
            assert response.status_code == 404 and response.json()['error']['code'] == 'PARCEL_NOT_FOUND'
        assert client.get('/parcels?include_geometry=invalid').status_code == 422
    return {'status': 'passed', 'tasks': ['P4.8', 'P4.9', 'P4.12', 'P4.13', 'P4.14'] + (['P4.15'] if region_keys else []), 'transport': 'FastAPI TestClient HTTP/ASGI',
            'n_parcels': len(ids), 'n_predictions_checked': len(errors),
            'n_geometries': sum(p['geometry'] is not None for p in mapped['items']),
            'prediction_max_error': max(errors), 'deserializations': len(loads),
            'n_explanations_checked': len(explanation_errors), 'explanation_max_error': max(explanation_errors),
            'n_feature_labels': len(labels),
            'n_risks_checked': len(risk_levels), 'risk_levels': dict(Counter(risk_levels)),
            'risk_method_version': METHOD_VERSION,
            'regions': regional_results, 'n_regions_checked': len(region_keys),
            'health': health, 'unknown_ids_rejected': True, 'http_training_forbidden': True,
            'api_contract_version': '0.1.0', 'model_version': expected.model_version.iloc[0]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', required=True)
    parser.add_argument('--delivery', required=True)
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    report = verify(args.data_root, args.delivery)
    Path(args.report).write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
