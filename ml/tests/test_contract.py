"""Tests de contrato (DoD §15, lado Modelado). Requiere CEBADA_DATA y haber corrido make_baseline_predictions.py."""
import numpy as np, pandas as pd, pytest
from src import config as C, contract as K
from src.data import load, families, columns_for

tr, ev = load()

def test_ids_are_strings_unique():
    K.validate_ids(tr); K.validate_ids(ev)
    assert all(isinstance(i, str) for i in tr[C.ID])

def test_eval_has_no_target():
    assert ev[C.TARGET].isna().all() and len(ev) == 59 and len(tr) == 138

def test_schema_features_are_original_columns_in_order():
    model, schema = K.load_artifacts()
    assert schema["unit"] == "t/ha" and schema["data_cutoff"] == C.DATA_CUTOFF
    assert not [f for f in schema["features"] if f.startswith("mun_") or f in ("grupo_espacial",)]
    pred = K.predict_frame(model, schema, ev)
    assert np.isfinite(pred.values).all()

def test_missing_feature_fails_explicitly():
    model, schema = K.load_artifacts()
    with pytest.raises(K.FeatureSchemaMismatch):
        K.predict_frame(model, schema, ev.drop(columns=[schema["features"][0]]))

def test_predictions_csv_contract():
    out = pd.read_csv(C.RESULTS / "predictions_raw.csv", dtype={C.ID: str})
    assert list(out.columns) == [C.ID, "rendimiento_pred_t_ha", "model_version"]
    K.validate_predictions(out, ev[C.ID])
