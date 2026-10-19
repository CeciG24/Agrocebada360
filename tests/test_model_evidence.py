import copy
import json
from pathlib import Path
import pytest
from scripts import build_model_evidence as builder
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/integrated/verified-2026-10-17/data'
pytestmark = pytest.mark.skipif(not DATA.exists(), reason='Requiere el dataset auditado local; no usa datos sintéticos como evidencia.')
def test_frozen_model_evidence_is_reproducible():
    expected=json.loads((ROOT/'frontend/src/data/model/model-evidence.json').read_text(encoding='utf-8'))
    assert builder.build(DATA)==expected
    assert {p['parcel_id'] for p in expected['oof']['points']}.isdisjoint({expected['reference_prediction']['parcel_id']})
@pytest.mark.parametrize('damage', ['target', 'evaluation_id'])
def test_oof_targets_and_ids_must_match_known_training_only(monkeypatch, damage):
    original=builder.indexed
    def changed(path):
        result=original(path)
        if path.name=='E4_clima__ridge.csv':
            result=copy.deepcopy(result)
            if damage=='target': result[next(iter(result))]['y']='100'
            else: result['AGC_003']=result.pop(next(iter(result)))
        return result
    monkeypatch.setattr(builder,'indexed',changed)
    with pytest.raises(ValueError): builder.build(DATA)
def test_shap_from_other_model_cannot_enter_report(monkeypatch):
    original=builder.read
    def changed(path):
        result=original(path)
        if path.name=='shap_metadata_yield_v1.json': result['model_sha256']='other'
        return result
    monkeypatch.setattr(builder,'read',changed)
    with pytest.raises(ValueError): builder.build(DATA)
