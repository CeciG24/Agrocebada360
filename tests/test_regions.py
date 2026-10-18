import json

import pytest
from fastapi.testclient import TestClient

from api.app.main import create_app
from api.app.schemas.common import Meta
from api.app.schemas.parcels import ParcelSummary
from api.app.schemas.prediction import Prediction
from api.app.schemas.regions import RegionSummary
from api.app.services.region_summary import summarize_regions
from ml.data_handoff import DataHandoffError
from ml.region_adapter import build_regions


def prediction(parcel_id, value, **changes):
    return Prediction(parcel_id=parcel_id, prediction=value, unit=changes.get('unit', 't/ha'),
                      model_version=changes.get('model_version', 'yield-v1'), lower=None, upper=None,
                      interval_level=None, interval_method=None, meta=Meta(mode=changes.get('mode', 'real')))


def test_mean_weights_each_predicted_parcel_and_preserves_zero_coverage():
    parcels = {str(i): ParcelSummary(id=str(i), region='r' if i < 5 else 'empty') for i in range(6)}
    predictions = {'0': prediction('0', 2.), '1': prediction('1', 4.), '2': prediction('2', 9.)}
    summaries = summarize_regions(parcels, predictions, 'real')
    assert summaries['r'].parcel_count == 5
    assert summaries['r'].predicted_count == 3
    assert summaries['r'].mean_prediction == 5.  # No media de medias municipales ni valores observados.
    assert summaries['empty'].mean_prediction is None and summaries['empty'].predicted_count == 0


@pytest.mark.parametrize('changes', [{'unit': 'kg/ha'}, {'model_version': 'other'}, {'mode': 'mock'}])
def test_summary_rejects_mixed_units_models_and_origins(changes):
    parcels = {str(i): ParcelSummary(id=str(i), region='r') for i in range(2)}
    with pytest.raises(ValueError):
        summarize_regions(parcels, {'0': prediction('0', 2.), '1': prediction('1', 4., **changes)}, 'real')


def test_region_schema_rejects_false_coverage_and_nonfinite_mean():
    row = dict(region='r', parcel_count=2, predicted_count=1, mean_prediction=3., unit='t/ha', model_version='v1', meta=Meta(mode='real'))
    for changes in [{'predicted_count': 3}, {'predicted_count': 0}, {'mean_prediction': float('nan')}, {'parcel_count': True}]:
        with pytest.raises(ValueError):
            RegionSummary(**{**row, **changes})


@pytest.mark.parametrize('municipality', ['Desconocido', 'Almoloya'])
def test_mapping_requires_state_and_municipality_and_never_guesses(tmp_path, municipality):
    (tmp_path / 'parcel_master.csv').write_text(
        f'parcel_id,dataset_split,estado,municipio\n001,PREDICCION,Puebla,{municipality}\n', encoding='utf-8')
    schema = dict(prediction_unit='t/ha', model_version='v1', model_sha256='x', data_version='x')
    with pytest.raises(DataHandoffError):
        build_regions(tmp_path, schema, {'001': 3.})


def test_mock_regions_are_explicitly_synthetic_and_match_catalog():
    with TestClient(create_app()) as client:
        catalog = client.get('/parcels').json()['items']
        for key in {row['region'] for row in catalog}:
            response = client.get('/regions/' + key)
            assert response.status_code == 200
            row = response.json()
            assert row['meta']['mode'] == 'mock' and row['unit'] == 'mock_unit'
            assert row['predicted_count'] == row['parcel_count'] == sum(p['region'] == key for p in catalog)
        assert client.get('/regions/unknown').status_code == 404
