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


def install_explanation(settings, mutate=None):
    row = {'parcel_id': '002', 'status': 'available', 'reason': None, 'method': 'shap',
           'model_version': 'yield-v1', 'output_space': 't/ha', 'base_value': 0., 'explained_output': 45.,
           'features': [{'feature': 'rain', 'friendly_name': 'rain', 'impact': 40., 'direction': 'positive'},
                        {'feature': 'temp', 'friendly_name': 'temp', 'impact': 5., 'direction': 'positive'}],
           'meta': {'mode': 'real', 'contract_version': '0.1.0', 'cycle': '2025-04/2025-10', 'data_cutoff': '2025-10-31'}}
    if mutate:
        mutate(row)
    path = settings.delivery_path / 'explanations.json'
    write(path, {'002': row})
    manifest_path = settings.delivery_path / 'integration_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['files_sha256']['explanations.json'] = sha256(path)
    write(manifest_path, manifest)


def test_real_explanation_matches_prediction_and_is_cached(real_delivery, monkeypatch):
    install_explanation(real_delivery)
    with TestClient(create_app(real_delivery)) as client:
        from ml import model_bundle
        monkeypatch.setattr(model_bundle, 'read_json', lambda *a: pytest.fail('No file reads during requests'))
        monkeypatch.setattr(client.app.state.service._pipeline._model, 'fit', lambda *a: pytest.fail('No training'))
        prediction = client.get('/predict/002').json()
        for _ in range(3):
            body = client.get('/explain/002').json()
            assert body['status'] == 'available'
            assert body['explained_output'] == pytest.approx(prediction['prediction'])
            assert body['model_version'] == prediction['model_version']
            assert body['base_value'] + sum(f['impact'] for f in body['features']) == body['explained_output']
        assert client.get('/explain/001').json()['status'] == 'unavailable'
        assert client.get('/explain/unknown').status_code == 404
        assert client.get('/explain/%20').status_code == 422


def test_no_explanation_module_is_expected_absence(real_delivery):
    with TestClient(create_app(real_delivery)) as client:
        response = client.get('/explain/002')
        assert response.status_code == 200
        assert response.json()['reason'] == 'EXPLANATION_NOT_READY'
        assert response.json()['features'] == []


@pytest.mark.parametrize('damage', ['version', 'scale', 'output', 'features', 'sign', 'sort', 'context', 'sum', 'id'])
def test_invalid_explanations_do_not_disable_prediction(real_delivery, damage):
    def mutate(row):
        if damage == 'version': row['model_version'] = 'yield-v2'
        if damage == 'scale': row['output_space'] = 'log-yield'
        if damage == 'output':
            row['base_value'], row['explained_output'] = 5., 50.  # aditividad válida pero otro predictor
        if damage == 'features': row['features'][0]['feature'] = 'unknown'
        if damage == 'sign': row['features'][0]['direction'] = 'negative'
        if damage == 'sort': row['features'].reverse()
        if damage == 'context': row['meta']['mode'] = 'mock'
        if damage == 'sum': row['base_value'] = 1.
        if damage == 'id': row['parcel_id'] = '001'
    install_explanation(real_delivery, mutate)
    with TestClient(create_app(real_delivery), raise_server_exceptions=False) as client:
        response = client.get('/explain/002')
        assert response.status_code == 503
        assert response.json()['error']['code'] == 'EXPLANATION_UNAVAILABLE'
        assert client.get('/predict/002').status_code == 200
        assert client.get('/health').status_code == 200


def test_declared_explanation_file_missing_is_operational_error(real_delivery):
    install_explanation(real_delivery)
    (real_delivery.delivery_path / 'explanations.json').unlink()
    with TestClient(create_app(real_delivery), raise_server_exceptions=False) as client:
        response = client.get('/explain/002')
        assert response.status_code == 503
        assert response.json()['error']['code'] == 'EXPLANATION_UNAVAILABLE'
