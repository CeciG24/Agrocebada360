"""HTTP con pipeline sklearn sintético real; sin fallback de datos ni resultados."""
import json
from importlib.metadata import version
from pathlib import Path
import platform

import joblib
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from api.app.core.config import Settings, get_settings
from api.app.main import create_app
from ml.artifact_contract import sha256
from ml.data_handoff import INPUTS
from ml.model_bundle import create_bundle
from ml.src.provenance import dataset_fingerprint


def write(path, value):
    path.write_text(json.dumps(value), encoding='utf-8')


@pytest.fixture
def real_delivery(tmp_path):
    root, delivery = tmp_path / 'data', tmp_path / 'delivery'
    delivery.mkdir()
    files = {
        'parcel_master.csv': 'parcel_id,dataset_split\n001,ENTRENAMIENTO\n002,PREDICCION\n',
        'features/features_master.csv': 'parcel_id,rain,temp\n001,2,3\n002,4,5\n',
        'targets/rendimiento.csv': 'parcel_id,rendimiento_t_ha\n001,5\n002,\n',
        'topografia/topography_master.csv': 'parcel_id\n001\n002\n',
        'clima/climate_timeseries.csv': 'parcel_id\n001\n002\n',
    }
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
    model = make_pipeline(SimpleImputer(), StandardScaler(), LinearRegression())
    model.fit(pd.DataFrame([[0, 0], [1, 0], [0, 1], [1, 1]], columns=['rain', 'temp']), [0, 10, 1, 11])
    joblib.dump(model, tmp_path / 'model.joblib')
    schema = {
        'contract_version': '0.3.0', 'model_version': 'yield-v1', 'feature_schema_version': 'features-v1',
        'data_version': dataset_fingerprint(root)['data_version'], 'target_name': 'rendimiento_t_ha',
        'prediction_unit': 't/ha', 'target_cycle': '2025-04/2025-10', 'prediction_information_cutoff': '2025-10-31',
        'training_id_source': 'synthetic IDs, test only', 'missing_value_policy': 'documented',
        'missing_value_policy_detail': 'Imputer fit inside synthetic pipeline',
        'features': ['rain', 'temp'], 'n_features': 2, 'model_file': 'model.joblib',
        'model_sha256': sha256(tmp_path / 'model.joblib'),
        'environment': {'python': platform.python_version(), 'packages': {
            p: version(p) for p in ['numpy', 'pandas', 'joblib', 'scikit-learn']}},
    }
    write(tmp_path / 'feature_schema.json', schema)
    create_bundle(tmp_path / 'model.joblib', tmp_path / 'feature_schema.json', delivery / 'model')
    provenance = {'data_version': schema['data_version'],
                  'features_file_sha256': sha256(root / 'features/features_master.csv'),
                  'source_files_sha256': {rel: sha256(root / rel) for rel in INPUTS},
                  'features': {feature: {'source': 'synthetic test fixture', 'sensor_or_dataset': 'synthetic',
                                        'temporal_window': '2025-04/2025-10', 'transformation': 'synthetic',
                                        'missing_value_policy': 'inside frozen pipeline',
                                        'uses_historical_information': False, 'information_kind': 'temporal',
                                        'max_information_date': '2025-10-31'} for feature in ['rain', 'temp']}}
    write(delivery / 'feature_provenance.json', provenance)
    polygon = {'type': 'Polygon', 'coordinates': [[[-100, 20], [-99, 20], [-99, 21], [-100, 20]]]}
    write(delivery / 'catalog.json', {'001': {'id': '001', 'region': None, 'geometry': polygon},
                                     '002': {'id': '002', 'region': None, 'geometry': None}})
    manifest = {key: schema[key] for key in ['contract_version', 'model_version', 'feature_schema_version', 'data_version']}
    manifest.update({'integration_format_version': 'integration-v1', 'files_sha256': {
        name: sha256(delivery / name) for name in ['catalog.json', 'feature_provenance.json', 'model/model_manifest.json']}})
    write(delivery / 'integration_manifest.json', manifest)
    return Settings(mode='real', data_root=root, delivery_path=delivery)


def test_real_http_prediction_catalog_and_precision(real_delivery, monkeypatch):
    from ml import inference
    from api.app.services.mock import MockService
    original = inference._deserialize
    loads = []
    def counted(path):
        loads.append(path)
        return original(path)
    monkeypatch.setattr(inference, '_deserialize', counted)
    monkeypatch.setattr(MockService, 'load', lambda self: pytest.fail('Real mode cannot use mocks'))
    with TestClient(create_app(real_delivery)) as client:
        assert client.get('/health').json() == {'status': 'ok', 'mode': 'real', 'contract_version': '0.1.0',
                                              'data_ready': True, 'model_loaded': True}
        base = client.get('/parcels').json()
        mapped = client.get('/parcels?include_geometry=true').json()
        assert [p['id'] for p in base['items']] == ['001', '002']
        assert 'geometry' not in base['items'][0]
        assert mapped['items'][1]['geometry'] is None
        assert client.get('/parcel/001').json()['geometry'] == mapped['items'][0]['geometry']
        assert client.get('/parcels?region=unconfirmed').json()['total'] == 0
        service = client.app.state.service
        def forbidden(*args, **kwargs):
            pytest.fail('HTTP must never train or reload')
        monkeypatch.setattr(service._pipeline._model, 'fit', forbidden)
        monkeypatch.setattr(service._pipeline, 'load_model', forbidden)
        for _ in range(3):
            response = client.get('/predict/002')
            assert response.status_code == 200
            body = response.json()
            assert body['parcel_id'] == '002' and body['meta']['mode'] == 'real'
            assert body['unit'] == 't/ha' and body['model_version'] == 'yield-v1'
            assert body['prediction'] == service._pipeline.predict('002')
            assert body['prediction'] == pytest.approx(45)
            assert body['interval_method'] is None and body['lower'] is None
        assert len(loads) == 1
        assert client.get('/predict/not-known').json()['error']['code'] == 'PARCEL_NOT_FOUND'
        assert client.get('/parcel/not-known').status_code == 404


def test_missing_model_keeps_catalog_available_without_fallback(real_delivery):
    (real_delivery.delivery_path / 'model/model.joblib').unlink()
    with TestClient(create_app(real_delivery), raise_server_exceptions=False) as client:
        health = client.get('/health')
        assert health.status_code == 503
        assert health.json()['data_ready'] and not health.json()['model_loaded']
        assert client.get('/parcels').status_code == 200
        assert client.get('/predict/002').json()['error']['code'] == 'MODEL_UNAVAILABLE'
        assert client.get('/predict/not-known').status_code == 404


def test_tampered_catalog_is_not_served(real_delivery):
    path = real_delivery.delivery_path / 'catalog.json'
    path.write_text('{}')
    with TestClient(create_app(real_delivery), raise_server_exceptions=False) as client:
        assert client.get('/health').status_code == 503
        assert client.get('/parcels').json()['error']['code'] == 'DATA_UNAVAILABLE'


def test_replaced_bundle_manifest_is_rejected_even_with_same_versions(real_delivery):
    path = real_delivery.delivery_path / 'model/model_manifest.json'
    path.write_text(path.read_text() + '\n')
    with TestClient(create_app(real_delivery), raise_server_exceptions=False) as client:
        assert client.get('/health').status_code == 503
        assert client.get('/parcels').status_code == 200
        assert client.get('/predict/002').json()['error']['code'] == 'MODEL_UNAVAILABLE'


def test_missing_features_do_not_become_synthetic_values(real_delivery, monkeypatch):
    from ml.inference import PredictionUnavailable
    with TestClient(create_app(real_delivery), raise_server_exceptions=False) as client:
        def missing(*args):
            raise PredictionUnavailable('private-internal-path')
        monkeypatch.setattr(client.app.state.service._pipeline, 'predict', missing)
        response = client.get('/predict/002')
        assert response.status_code == 503
        assert response.json()['error']['code'] == 'PREDICTION_UNAVAILABLE'
        assert 'private-internal-path' not in response.text


def test_changed_source_rejected_before_model_deserialization(real_delivery, monkeypatch):
    from ml import inference
    path = real_delivery.data_root / 'clima/climate_timeseries.csv'
    path.write_text(path.read_text() + '\n')
    monkeypatch.setattr(inference, '_deserialize', lambda path: pytest.fail('Invalid source cannot load model'))
    with TestClient(create_app(real_delivery)) as client:
        assert client.get('/health').status_code == 503
        assert client.get('/predict/002').json()['error']['code'] == 'DATA_UNAVAILABLE'


def test_configuration_requires_explicit_real_paths_and_rejects_unknown_mode(monkeypatch):
    from pydantic import ValidationError
    monkeypatch.setenv('CEBADA_MODE', 'real')
    monkeypatch.delenv('CEBADA_DATA', raising=False)
    monkeypatch.delenv('CEBADA_DELIVERY', raising=False)
    with pytest.raises(ValidationError):
        get_settings()
    monkeypatch.setenv('CEBADA_MODE', 'typo')
    with pytest.raises(ValidationError):
        get_settings()
    monkeypatch.delenv('CEBADA_MODE')
    assert get_settings().mode == 'mock'
