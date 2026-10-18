import copy
import json
import platform
from importlib import metadata
from pathlib import Path

import pytest

from ml import inference
from ml.artifact_contract import ArtifactContractError, sha256, validate_feature_schema
from ml.inference import FeatureSchemaMismatch, InferencePipeline
from ml.model_bundle import create_bundle, inspect_bundle, read_json, main


@pytest.fixture
def delivery(tmp_path):
    import joblib
    import pandas as pd
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LinearRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    model = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LinearRegression())
    x = pd.DataFrame([[0, 0], [1, 0], [0, 1], [1, 1]], columns=["rain", "temp"])
    model.fit(x, [0, 10, 1, 11])
    model_path = tmp_path / "yield_model_v1.joblib"
    joblib.dump(model, model_path)
    schema = {
        "contract_version": "0.3.0", "model_version": "yield-v1",
        "feature_schema_version": "features-v1", "data_version": "synthetic-v1",
        "target_name": "yield_observed", "prediction_unit": "t/ha",
        "target_cycle": "2025-04/2025-10", "prediction_information_cutoff": "2025-10-31",
        "training_id_source": "synthetic_training_ids.json", "missing_value_policy": "documented",
        "missing_value_policy_detail": "Median learned from synthetic train, inside frozen model.",
        "features": ["rain", "temp"], "n_features": 2, "model_file": model_path.name,
        "model_sha256": sha256(model_path), "verified": True, "fast_mode": False,
        "environment": {"python": platform.python_version(), "packages": {
            name: metadata.version(name) for name in ("joblib", "numpy", "pandas", "scikit-learn")}},
    }
    schema_path = tmp_path / "feature_schema.json"
    schema_path.write_text(json.dumps(schema), encoding="utf-8")
    features = tmp_path / "features.csv"
    features.write_text("parcel_id,temp,rain,extra\n001,2,3,ignored\n", encoding="utf-8")
    provenance = tmp_path / "provenance.json"
    provenance.write_text(json.dumps({"data_version": "synthetic-v1", "features_file_sha256": sha256(features),
        "features": {name: {"source": "Synthetic fixture only", "sensor_or_dataset": "synthetic",
            "temporal_window": "2025-04/2025-10", "transformation": "mean", "missing_value_policy": "frozen imputer",
            "uses_historical_information": False, "information_kind": "temporal", "max_information_date": "2025-10-31"}
            for name in schema["features"]}}), encoding="utf-8")
    return model_path, schema_path, schema, features, provenance


def test_package_is_byte_preserving_and_does_not_deserialize(delivery, tmp_path, monkeypatch):
    import joblib
    model, schema_path, schema, _, _ = delivery
    monkeypatch.setattr(joblib, "load", lambda *_: pytest.fail("pack/inspect must not deserialize"))
    out = tmp_path / "bundle"
    report = create_bundle(model, schema_path, out)
    assert (out / model.name).read_bytes() == model.read_bytes()
    assert (out / "feature_schema.json").read_bytes() == schema_path.read_bytes()
    assert report["status"] == "ARTIFACTS_VERIFIED"
    assert report["deserialized"] is False
    assert report["data_provenance_checked"] is False
    assert report["data_version"] == schema["data_version"]
    assert inspect_bundle(out)["environment"]["python"]["matches"] is True


def test_from_bundle_loads_once_with_named_frozen_preprocessing(delivery, tmp_path, monkeypatch):
    import joblib
    model, schema_path, _, features, provenance = delivery
    out = tmp_path / "bundle"
    create_bundle(model, schema_path, out)
    calls = []

    def deserialize(path):
        calls.append(path)
        return joblib.load(path)

    monkeypatch.setattr(inference, "_deserialize", deserialize)
    pipeline = InferencePipeline.from_bundle(out, features, provenance, ["001", "002"])
    pipeline.load_model()
    pipeline.load_model()
    assert pipeline.predict("001") == pytest.approx(32)
    assert pipeline.preprocess("001") == [[3.0, 2.0]]
    assert len(calls) == 1


def test_native_ml_model_hash_supported_without_external_manifest(delivery):
    model, schema_path, _, features, provenance = delivery
    pipeline = InferencePipeline(model, schema_path, features, provenance, ["001"])
    pipeline.load_model()
    assert pipeline.predict("001") == pytest.approx(32)
    assert pipeline.model_version == "yield-v1"


@pytest.mark.parametrize("change", [
    {"prediction_unit": "kg/ha"}, {"prediction_information_cutoff": "2026-12-31"},
    {"model_version": None}, {"data_version": "PENDIENTE"}, {"missing_value_policy": "<confirmar>"},
    {"features": ["rain", "rain"]}, {"n_features": 3}, {"n_features": True},
    {"features": ["rain", "yield_observed"]}, {"model_sha256": "fake"},
    {"model_file": "../outside.joblib"}, {"model_file": "C:\\outside.joblib"},
    {"verified": False}, {"verified": "true"}, {"fast_mode": True},
    {"environment": {"python": "3.13", "packages": {"joblib": "1.0"}}},
])
def test_rejects_invalid_delivery_before_writing_or_deserializing(delivery, tmp_path, monkeypatch, change):
    model, schema_path, schema, features, provenance = delivery
    schema.update(change)
    schema_path.write_text(json.dumps(schema), encoding="utf-8")
    out = tmp_path / "bundle"
    with pytest.raises(ArtifactContractError):
        create_bundle(model, schema_path, out)
    assert not out.exists()
    monkeypatch.setattr(inference, "_deserialize", lambda *_: pytest.fail("invalid schema reached deserialize"))
    pipeline = InferencePipeline(model, schema_path, features, provenance, ["001"])
    with pytest.raises(FeatureSchemaMismatch):
        pipeline.load_model()


@pytest.mark.parametrize("tamper", ["model", "schema", "version", "path", "format"])
def test_package_tampering_is_rejected(delivery, tmp_path, tamper):
    model, schema_path, _, _, _ = delivery
    out = tmp_path / "bundle"
    create_bundle(model, schema_path, out)
    if tamper in ("model", "schema"):
        path = out / (model.name if tamper == "model" else "feature_schema.json")
        path.write_bytes(path.read_bytes() + b" ")
    else:
        path = out / "model_manifest.json"
        manifest = read_json(path)
        key, value = {"version": ("data_version", "other"), "path": ("model_file", "../outside.joblib"),
                      "format": ("bundle_format_version", "999.0")}[tamper]
        manifest[key] = value
        path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ArtifactContractError):
        inspect_bundle(out)


def test_native_model_tampered_hash_is_checked_before_deserialization(delivery, monkeypatch):
    model, schema_path, _, features, provenance = delivery
    model.write_bytes(model.read_bytes() + b"tamper")
    monkeypatch.setattr(inference, "_deserialize", lambda *_: pytest.fail("hash checked too late"))
    pipeline = InferencePipeline(model, schema_path, features, provenance, ["001"])
    with pytest.raises(FeatureSchemaMismatch):
        pipeline.load_model()
    assert not pipeline.model_loaded


def test_package_never_replaces_existing_delivery(delivery, tmp_path):
    model, schema_path, _, _, _ = delivery
    out = tmp_path / "bundle"
    create_bundle(model, schema_path, out)
    before = (out / "model_manifest.json").read_bytes()
    with pytest.raises(FileExistsError):
        create_bundle(model, schema_path, out)
    assert (out / "model_manifest.json").read_bytes() == before


def test_package_integrity_does_not_bypass_missing_data_provenance(delivery, tmp_path, monkeypatch):
    model, schema_path, _, features, _ = delivery
    out = tmp_path / "bundle"
    create_bundle(model, schema_path, out)
    monkeypatch.setattr(inference, "_deserialize", lambda *_: pytest.fail("unverified data reached deserialize"))
    pipeline = InferencePipeline.from_bundle(out, features, tmp_path / "missing.json", ["001"])
    with pytest.raises(FeatureSchemaMismatch):
        pipeline.load_model()
    assert not pipeline.model_loaded


def test_named_features_not_just_count_must_match_model(delivery):
    model, schema_path, schema, features, provenance = delivery
    schema["features"] = ["temp", "rain"]
    schema_path.write_text(json.dumps(schema), encoding="utf-8")
    pipeline = InferencePipeline(model, schema_path, features, provenance, ["001"])
    with pytest.raises(FeatureSchemaMismatch, match="nombres"):
        pipeline.load_model()


def test_environment_differences_are_reported_not_installed_or_hidden(delivery, tmp_path):
    model, schema_path, schema, _, _ = delivery
    schema["environment"]["python"] = "3.99.0"
    schema["environment"]["packages"]["cebada-nonexistent-fixture"] = "1.0.0"
    schema_path.write_text(json.dumps(schema), encoding="utf-8")
    report = create_bundle(model, schema_path, tmp_path / "bundle")
    assert report["environment"]["python"]["matches"] is False
    assert report["environment"]["packages"]["cebada-nonexistent-fixture"]["current"] is None


@pytest.mark.parametrize("raw", ['{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'])
def test_strict_json_rejects_ambiguous_or_nonfinite_metadata(tmp_path, raw):
    path = tmp_path / "invalid.json"
    path.write_text(raw, encoding="utf-8")
    with pytest.raises(ArtifactContractError):
        read_json(path)


def test_cli_rejects_bad_package_with_failure_exit(tmp_path, capsys):
    with pytest.raises(SystemExit) as error:
        main(["inspect", "--bundle", str(tmp_path)])
    assert error.value.code == 1
    assert "Paquete rechazado" in capsys.readouterr().err


def test_legacy_schema_remains_supported_but_not_publishable_as_new_delivery(delivery):
    _, _, schema, _, _ = delivery
    legacy = copy.deepcopy(schema)
    for key in ("model_sha256", "model_file", "n_features", "environment"):
        del legacy[key]
    validate_feature_schema(legacy)
    with pytest.raises(ArtifactContractError):
        validate_feature_schema(legacy, delivery=True)


def test_json_schema_documents_parse_and_match_delivered_filenames(delivery):
    import re
    root = Path(__file__).resolve().parents[1] / "docs/schemas"
    for path in root.glob("*.schema.json"):
        assert read_json(path)["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    document = read_json(root / "model-artifact.schema.json")
    pattern = document["properties"]["model_file"]["pattern"]
    assert re.fullmatch(pattern, delivery[0].name)
    assert re.fullmatch(pattern, "../escape.joblib") is None
