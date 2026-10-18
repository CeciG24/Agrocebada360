import hashlib
import json
from pathlib import Path

import pytest

from api.app.services.feature_labels import load_feature_labels, DICTIONARY_PATH

ROOT = Path(__file__).resolve().parents[1]


def dictionary():
    return json.loads(DICTIONARY_PATH.read_text(encoding='utf-8'))


def test_dictionary_covers_frozen_schema_and_distinguishes_temporal_meanings():
    catalog = dictionary()
    schema_path = ROOT / 'ml/models/feature_schema.json'
    schema = json.loads(schema_path.read_text(encoding='utf-8'))
    assert set(catalog['features']) == set(schema['features'])
    labels = load_feature_labels(schema['model_sha256'], hashlib.sha256(schema_path.read_bytes()).hexdigest())
    assert len(labels) == 30 and len(set(labels.values())) == 30
    assert labels['precip_mean_mm_2025'] == 'Precipitación mensual media · abr–oct 2025'
    assert 'histórico + ciclo 2025' in labels['precip_mean_mm_2022_2025']
    record = catalog['features']['amplitud_termica_std_c_2025']
    assert record['transformation'] == 'std(tmax_c - tmin_c, ddof=1)'
    assert record['variable_unit'] == '°C'
    assert 'no es incertidumbre' in record['definition']
    assert catalog['features']['precip_mean_mm_2025']['temporal_start'] == '2025-04-01'
    assert 'no implica' in catalog['features']['precip_total_mm_2022']['historical_context']


@pytest.mark.parametrize('mismatch', ['model', 'schema'])
def test_labels_do_not_cross_model_or_schema_boundaries(mismatch):
    scope = dictionary()['scope']
    model = 'different' if mismatch == 'model' else scope['model_sha256']
    schema = 'different' if mismatch == 'schema' else scope['feature_schema_sha256']
    assert load_feature_labels(model, schema) == {}


def test_missing_or_unknown_label_keeps_technical_name(tmp_path):
    assert load_feature_labels('a', 'b', path=tmp_path / 'missing.json') == {}
    scope = dictionary()['scope']
    labels = load_feature_labels(scope['model_sha256'], scope['feature_schema_sha256'])
    assert labels.get('unconfirmed_feature', 'unconfirmed_feature') == 'unconfirmed_feature'


@pytest.mark.parametrize('invalid', [[], None, {'dictionary_version': 'unknown'},
                                     {'dictionary_version': 'feature-labels-v1', 'scope': [], 'features': {}},
                                     {'dictionary_version': 'feature-labels-v1', 'scope': {'model_sha256': 'a', 'feature_schema_sha256': 'b'}, 'features': {'x': None}}])
def test_invalid_dictionary_falls_back_without_disabling_model(tmp_path, invalid):
    path = tmp_path / 'invalid.json'
    path.write_text(json.dumps(invalid), encoding='utf-8')
    assert load_feature_labels('a', 'b', path=path) == {}
