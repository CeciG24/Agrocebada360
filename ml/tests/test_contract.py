"""Tests de contrato v0.3.0 (DoD §15, lado Modelado).

- Sintéticos (no requieren datos): schema, asociación modelo<->schema, 4 decimales, cobertura de IDs, puerta de auditoría.
- Con dataset (CEBADA_DATA): partición = lista oficial, features permitidas. Se omiten si no hay datos.
- Con artefactos finales (tras train_final_model.py / generate_predictions.py): se omiten si aún no existen.
"""
import json
import warnings

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LinearRegression

from src import config as C, contract as K, provenance as PV


# ---------------- helpers sintéticos ----------------
def _frame(n=30, k=5, seed=0):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame(rng.normal(size=(n, k)), columns=[f"f{i}" for i in range(k)])
    df[C.ID] = [f"P{i:03d}" for i in range(n)]
    df[C.TARGET] = df.f0 * 2 + rng.normal(0, .1, n)
    return df


@pytest.fixture
def fake_version(monkeypatch):
    monkeypatch.setattr(PV, "data_version", lambda root=None: "sha256:test")


def _save(tmp_path, df, feats, version="yield-test", **extra):
    m = LinearRegression().fit(df[feats], df[C.TARGET])             # DataFrame => feature_names_in_
    sch = K.build_schema(feats, model_version=version, extra=extra)
    K.save_artifacts(m, sch, tmp_path)
    return m, sch


# ---------------- features ----------------
def test_validate_features_rejects_derived_and_forbidden():
    df = _frame(); df["mun_puebla"] = 1.0; df["fecha_siembra_dias"] = 1.0
    with pytest.raises(K.FeatureSchemaMismatch):
        K.validate_features(df, ["f0", "mun_puebla"])
    with pytest.raises(K.FeatureSchemaMismatch):
        K.validate_features(df, ["f0", "fecha_siembra_dias"])        # §5.6
    with pytest.raises(K.FeatureSchemaMismatch):
        K.validate_features(df, ["f0", "no_existe"])
    K.validate_features(df, ["f0", "f1"])


# ---------------- schema 0.3.0 ----------------
def test_schema_has_contract_030_fields(tmp_path, fake_version):
    _, sch = _save(tmp_path, _frame(), ["f0", "f1", "f2"])
    stored = json.loads((tmp_path / "feature_schema.json").read_text())
    for k in K.REQUIRED_SCHEMA_KEYS:
        assert k in stored, k
    assert stored["contract_version"] == C.CONTRACT_VERSION == "0.3.0"
    assert stored["prediction_unit"] == "t/ha" and stored["prediction_information_cutoff"] == C.DATA_CUTOFF
    assert stored["n_features"] == 3 and len(stored["model_sha256"]) == 64


def test_incomplete_schema_is_rejected():
    with pytest.raises(K.FeatureSchemaMismatch):
        K.validate_schema({"features": ["a"], "model_version": "x"})


# ---------------- asociación verificable modelo <-> schema ----------------
def test_roundtrip_predicts_with_schema_order(tmp_path, fake_version):
    df = _frame(); _save(tmp_path, df, ["f0", "f1", "f2"])
    model, sch = K.load_artifacts(tmp_path)
    pred = K.predict_frame(model, sch, df.sample(frac=1, random_state=1))     # columnas/filas desordenadas: se elige por nombre
    assert np.isfinite(pred.values).all() and len(pred) == len(df)


def test_tampered_model_is_detected_by_hash(tmp_path, fake_version):
    import joblib
    df = _frame(); _save(tmp_path, df, ["f0", "f1", "f2"])
    joblib.dump(LinearRegression().fit(df[["f0", "f1", "f2"]], df[C.TARGET] * 3), tmp_path / "yield_model_test.joblib")
    with pytest.raises(K.ArtifactMismatch):
        K.load_artifacts(tmp_path)


def test_feature_count_mismatch_is_not_silent(tmp_path, fake_version):
    """audit-2026-10-14: un modelo de 23 features pasaba como si fueran 32. Ahora es error."""
    df = _frame(k=6); m = LinearRegression().fit(df[["f0", "f1", "f2"]], df[C.TARGET])
    sch = K.build_schema(["f0", "f1", "f2", "f3"], model_version="yield-test")
    with pytest.raises(K.ArtifactMismatch):
        K.save_artifacts(m, sch, tmp_path)


def test_feature_order_mismatch_is_detected(tmp_path, fake_version):
    df = _frame(); m = LinearRegression().fit(df[["f0", "f1", "f2"]], df[C.TARGET])
    sch = K.build_schema(["f2", "f1", "f0"], model_version="yield-test")
    with pytest.raises(K.ArtifactMismatch):
        K.save_artifacts(m, sch, tmp_path)


def test_missing_feature_fails_explicitly(tmp_path, fake_version):
    df = _frame(); _save(tmp_path, df, ["f0", "f1", "f2"])
    model, sch = K.load_artifacts(tmp_path)
    with pytest.raises(K.FeatureSchemaMismatch):
        K.predict_frame(model, sch, df.drop(columns=["f1"]))


def test_missing_files_raise_model_not_loaded(tmp_path):
    with pytest.raises(K.ModelNotLoaded):
        K.load_artifacts(tmp_path)


# ---------------- predicciones (§14) ----------------
def _preds(ids, vals):
    return pd.DataFrame({C.ID: ids, C.PRED_COL: vals})


def test_validate_predictions_uses_official_ids_not_fixed_count():
    ids = [f"P{i}" for i in range(7)]                               # 7, no 59: la cantidad la define la lista oficial
    K.validate_predictions(_preds(ids, np.linspace(1, 5, 7)), ids)
    with pytest.raises(K.ContractError):
        K.validate_predictions(_preds(ids[:-1], np.ones(6)), ids)    # falta una
    with pytest.raises(K.ContractError):
        K.validate_predictions(_preds(ids[:-1] + ["X"], np.ones(7)), ids)   # ID distinto
    with pytest.raises(K.ContractError):
        K.validate_predictions(_preds(ids, [1, 2, np.nan, 4, 5, 6, 7]), ids)
    with pytest.raises(K.ContractError):
        K.validate_predictions(_preds(ids[:-1] + [ids[0]], np.ones(7)), ids)   # duplicado


def test_four_decimals_enforced():
    ids = ["A", "B"]
    K.validate_predictions(_preds(ids, [3.1234, 4.5]), ids, decimals=4)
    with pytest.raises(K.ContractError):
        K.validate_predictions(_preds(ids, [3.12345, 4.5]), ids, decimals=4)


# ---------------- puerta de auditoría ----------------
def test_strict_gate_blocks_without_valid_audit(monkeypatch):
    monkeypatch.setattr(PV, "audit_state", lambda root=None: {"valid": False, "cutoff_ok": None, "data_version": None, "reason": "sin auditoría"})
    monkeypatch.setattr(C, "STRICT_CUTOFF", True)
    with pytest.raises(K.AuditNotValid):
        K.require_valid_audit()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        assert K.require_valid_audit(allow_unverified=True)["valid"] is False
    assert any("NO VERIFICADO" in str(x.message) for x in w)


def test_audit_state_ties_audit_to_dataset_hash(tmp_path, monkeypatch):
    from ml.data_handoff import INPUTS
    root = tmp_path / "ds"
    for rel in INPUTS:
        (root / rel).parent.mkdir(parents=True, exist_ok=True); (root / rel).write_text("a,b\n1,2\n")
    monkeypatch.setattr(C, "RESULTS", tmp_path / "res"); (tmp_path / "res").mkdir()
    audit = {"cutoff_ok": True, "data_fingerprint": PV.dataset_fingerprint(root),
             "required_model_features_validation": {"valid": True},
             "source_files_sha256": {rel: PV.sha256_file(root / rel) for rel in INPUTS}}
    PV.audit_path().write_text(json.dumps(audit))
    assert PV.audit_state(root)["valid"]
    climate = root / 'clima/climate_timeseries.csv'
    original = climate.read_text()
    climate.write_text('a,b\n9,9\n')
    assert not PV.audit_state(root)["valid"]  # Fuente cambió, aunque features y data_version no.
    climate.write_text(original)
    (root / "parcel_master.csv").write_text("a,b\n9,9\n")           # otro dataset => el "OK" no se hereda
    st = PV.audit_state(root); assert not st["valid"] and "otro dataset" in st["reason"]
    PV.audit_path().write_text(json.dumps({"cutoff_ok": False}))
    assert not PV.audit_state(root)["valid"]


# ---------------- con dataset real ----------------
def test_ids_are_strings_unique(tr, ev):
    K.validate_ids(tr); K.validate_ids(ev)
    assert all(isinstance(i, str) for i in tr[C.ID])


def test_partition_matches_official_list_and_eval_has_no_target(tr, ev):
    from src.split import load_official_ids
    off = load_official_ids()
    if off is None:
        pytest.skip("falta split/official_ids_v1.json")
    assert set(tr[C.ID]) == set(off["train_ids"]) and set(ev[C.ID]) == set(off["eval_ids"])
    assert tr[C.TARGET].notna().all() and ev[C.TARGET].isna().all()


def test_official_experiments_pass_feature_validation(tr):
    from src.data import families, columns_for
    fam = families(tr)
    for e in C.OFFICIAL_EXPERIMENTS:
        K.validate_features(tr, columns_for(e, fam))


# ---------------- con artefactos finales (tras P2.9/P2.10) ----------------
def test_final_artifacts_and_predictions(ev):
    if not (C.MODELS / "feature_schema.json").exists() or not (C.RESULTS / "predictions_raw.csv").exists():
        pytest.skip("aún no se han generado los artefactos finales (train_final_model.py / generate_predictions.py)")
    model, sch = K.load_artifacts()
    assert not [f for f in sch["features"] if f.startswith("mun_") or f == "grupo_espacial"]
    assert np.isfinite(K.predict_frame(model, sch, ev).values).all()
    raw = pd.read_csv(C.RESULTS / "predictions_raw.csv", dtype={C.ID: str})
    assert list(raw.columns) == [C.ID, C.PRED_COL, "model_version"]
    K.validate_predictions(raw, ev[C.ID])
