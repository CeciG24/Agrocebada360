"""Aceptación HTTP P4.8/P4.9 sobre una entrega integrada de confianza."""
import argparse
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


def verify(data_root, delivery):
    logging.getLogger('httpx').setLevel(logging.WARNING)
    root = Path(__file__).resolve().parents[1]
    expected = pd.read_csv(root / 'ml/results/predictions_raw.csv', dtype={'parcel_id': str})
    errors = []
    explanation_errors = []
    loads = []
    original = inference._deserialize

    def counted(path):
        loads.append(str(path))
        return original(path)

    settings = Settings(mode='real', data_root=Path(data_root), delivery_path=Path(delivery))
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
        assert all(p['region'] is None for p in plain['items'])
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
                explained = explanation['base_value'] + math.fsum(f['impact'] for f in explanation['features'])
                explanation_errors.append(abs(explained - prediction['prediction']))
        assert max(errors) < 1e-8 and len(loads) == 1
        assert max(explanation_errors) < 1e-8
        split = json.loads((root / 'ml/split/official_ids_v1.json').read_text())
        unavailable = client.get('/explain/' + split['train_ids'][0])
        assert unavailable.status_code == 200 and unavailable.json()['reason'] == 'EXPLANATION_NOT_READY'
        for route in ['/parcel/unknown-id', '/predict/unknown-id', '/explain/unknown-id']:
            response = client.get(route)
            assert response.status_code == 404 and response.json()['error']['code'] == 'PARCEL_NOT_FOUND'
        assert client.get('/parcels?include_geometry=invalid').status_code == 422
    return {'status': 'passed', 'tasks': ['P4.8', 'P4.9', 'P4.12'], 'transport': 'FastAPI TestClient HTTP/ASGI',
            'n_parcels': len(ids), 'n_predictions_checked': len(errors),
            'n_geometries': sum(p['geometry'] is not None for p in mapped['items']),
            'prediction_max_error': max(errors), 'deserializations': len(loads),
            'n_explanations_checked': len(explanation_errors), 'explanation_max_error': max(explanation_errors),
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
