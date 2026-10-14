import json
import math

import pytest

from ml import inference
from ml.inference import (
    FeatureSchemaMismatch, InferencePipeline, ModelNotLoaded,
    ParcelNotFound, PredictionUnavailable,
)


class Predictor:
    n_features_in_ = 2

    def predict(self, rows):
        return [rows[0][0] * 10 + rows[0][1]]


def refresh_provenance(pipeline):
    evidence = json.loads(pipeline.provenance_path.read_text(encoding="utf-8"))
    evidence["features_file_sha256"] = inference._sha256(pipeline.features_path)
    pipeline.provenance_path.write_text(json.dumps(evidence), encoding="utf-8")


@pytest.fixture
def bundle(tmp_path, monkeypatch):
    schema = {
        "contract_version": "0.3.0", "model_version": "test-v1",
        "feature_schema_version": "test-features-v1", "data_version": "test-data-v1",
        "target_name": "observed_yield", "prediction_unit": "t/ha",
        "features": ["b", "a"], "missing_value_policy": "reject",
        "target_cycle": "2025-04/2025-10",
        "prediction_information_cutoff": "2025-10-31",
        "training_id_source": "official_training_ids.csv",
    }
    (tmp_path / "schema.json").write_text(json.dumps(schema), encoding="utf-8")
    (tmp_path / "features.csv").write_text("parcel_id,a,b\n001,2,3\n", encoding="utf-8")
    evidence = {
        "data_version": schema["data_version"],
        "features_file_sha256": inference._sha256(tmp_path / "features.csv"),
        "features": {name: {
            "source": "Synthetic fixture", "sensor_or_dataset": "test-sensor",
            "temporal_window": "2025-04/2025-10", "transformation": "mean",
            "missing_value_policy": "reject", "uses_historical_information": False,
            "information_kind": "temporal", "max_information_date": "2025-10-30",
        } for name in ("a", "b")},
    }
    (tmp_path / "provenance.json").write_text(json.dumps(evidence), encoding="utf-8")
    metadata = {field: schema[field] for field in inference.VERSION_FIELDS}
    metadata["features"] = schema["features"]
    artifact = {"model": Predictor(), "features": ["b", "a"], "version": "test-v1",
                "metadata": metadata}
    calls = []

    def deserialize(path):
        calls.append(path)
        return artifact

    monkeypatch.setattr(inference, "_deserialize", deserialize)
    pipeline = InferencePipeline(
        tmp_path / "model.joblib", tmp_path / "schema.json",
        tmp_path / "features.csv", tmp_path / "provenance.json", ["001", "002"],
    )
    return pipeline, schema, artifact, calls


def test_load_once_preserves_ids_order_and_precision(bundle):
    pipeline, _, _, calls = bundle
    with pytest.raises(ModelNotLoaded):
        pipeline.predict("001")
    pipeline.load_model()
    pipeline.load_model()
    assert pipeline.preprocess("001") == [[3.0, 2.0]]
    assert pipeline.predict("001") == 32.0
    assert pipeline.predict("001") == 32.0
    assert len(calls) == 1
    assert pipeline.unit == "t/ha"
    assert pipeline.model_version == "test-v1"
    with pytest.raises(ParcelNotFound):
        pipeline.predict("1")
    with pytest.raises(PredictionUnavailable):
        pipeline.predict("002")


@pytest.mark.parametrize("field,value", [
    ("version", "wrong"), ("features", ["a", "b"]), ("model", None),
])
def test_incompatible_artifact_is_not_loaded(bundle, field, value):
    pipeline, _, artifact, _ = bundle
    artifact[field] = value
    with pytest.raises((FeatureSchemaMismatch, ModelNotLoaded)):
        pipeline.load_model()
    assert not pipeline.model_loaded


@pytest.mark.parametrize("change", [
    {"prediction_information_cutoff": "2025-11-01"}, {"features": ["a", "a"]},
    {"missing_value_policy": "documented"}, {"prediction_unit": ""},
    {"target_name": "PENDIENTE"}, {"training_id_source": "<lista oficial>"},
    {"contract_version": "0.1.0"}, {"prediction_unit": "kg/ha"},
    {"target_cycle": "2024-04/2024-10"}, {"data_version": ""},
    {"features": ["a", "observed_yield"]},
])
def test_invalid_schema(bundle, change):
    pipeline, schema, _, calls = bundle
    schema.update(change)
    pipeline.schema_path.write_text(json.dumps(schema), encoding="utf-8")
    with pytest.raises(FeatureSchemaMismatch):
        pipeline.load_model()
    assert calls == []


@pytest.mark.parametrize("evidence", [None, '{}'])
def test_temporal_evidence_required(bundle, evidence):
    pipeline, _, _, calls = bundle
    if evidence is None:
        pipeline.provenance_path.unlink()
    else:
        pipeline.provenance_path.write_text(evidence, encoding="utf-8")
    with pytest.raises(FeatureSchemaMismatch):
        pipeline.load_model()
    assert not pipeline.model_loaded
    assert calls == []


@pytest.mark.parametrize("csv_text", [
    "parcel_id,a\n001,2\n", "parcel_id,a,a\n001,2,3\n",
    "parcel_id,a,b\n001,2,3\n001,4,5\n", "parcel_id,a,b\n999,2,3\n",
    "parcel_id,a,b\n,2,3\n", "parcel_id,a,b\n001,2\n",
])
def test_invalid_feature_table(bundle, csv_text):
    pipeline, _, _, _ = bundle
    pipeline.features_path.write_text(csv_text, encoding="utf-8")
    refresh_provenance(pipeline)
    with pytest.raises(FeatureSchemaMismatch):
        pipeline.load_model()


@pytest.mark.parametrize("value", ["", "NaN", "inf", "-inf", "texto"])
def test_invalid_numeric_feature(bundle, value):
    pipeline, _, _, _ = bundle
    pipeline.features_path.write_text(f"parcel_id,a,b\n001,2,{value}\n", encoding="utf-8")
    refresh_provenance(pipeline)
    pipeline.load_model()
    with pytest.raises(PredictionUnavailable):
        pipeline.predict("001")


def test_missing_values_are_delegated_to_exported_pipeline(bundle):
    pipeline, schema, artifact, _ = bundle
    schema["missing_value_policy"] = "documented"
    schema["missing_value_policy_detail"] = "Exported model replaces NaN using its learned imputer."
    pipeline.schema_path.write_text(json.dumps(schema), encoding="utf-8")
    pipeline.features_path.write_text("parcel_id,a,b\n001,2,\n", encoding="utf-8")
    refresh_provenance(pipeline)

    class ImputingPredictor:
        def predict(self, rows):
            assert math.isnan(rows[0][0])
            return [2.123456789]

    artifact["model"] = ImputingPredictor()
    pipeline.load_model()
    assert pipeline.predict("001") == 2.123456789


@pytest.mark.parametrize("output", [[math.nan], [math.inf], [-math.inf], [], [1, 2], ["2"], [[2]]])
def test_invalid_prediction(bundle, output):
    pipeline, _, artifact, _ = bundle
    artifact["model"].predict = lambda rows: output
    pipeline.load_model()
    with pytest.raises(PredictionUnavailable):
        pipeline.predict("001")


def test_deserialization_failure(bundle, monkeypatch):
    pipeline, _, _, _ = bundle

    def fail(path):
        raise OSError("private file path")

    monkeypatch.setattr(inference, "_deserialize", fail)
    with pytest.raises(ModelNotLoaded, match="No se pudo cargar"):
        pipeline.load_model()
    assert not pipeline.model_loaded


def test_real_serialized_sklearn_pipeline(bundle, monkeypatch):
    import joblib
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LinearRegression
    from sklearn.pipeline import make_pipeline

    pipeline, _, artifact, _ = bundle
    model = make_pipeline(SimpleImputer(), LinearRegression())
    model.fit([[0, 0], [1, 0], [0, 1], [1, 1]], [0, 10, 1, 11])
    joblib.dump({**artifact, "model": model}, pipeline.model_path)
    monkeypatch.setattr(inference, "_deserialize", joblib.load)
    pipeline.load_model()
    assert pipeline.predict("001") == pytest.approx(32)


def test_extra_columns_ignored(bundle):
    pipeline, _, _, _ = bundle
    pipeline.features_path.write_text(
        "parcel_id,region,b,observed_yield,a,aux\n001,north,3,,2,not_numeric\n", encoding="utf-8")
    refresh_provenance(pipeline)
    pipeline.load_model()
    assert pipeline.preprocess("001") == [[3.0, 2.0]]
    assert pipeline.predict("001") == 32


@pytest.mark.parametrize("change", [
    {"max_information_date": "2025-11-01"}, {"max_information_date": None},
    {"source": "PENDIENTE"}, {"sensor_or_dataset": ""},
    {"temporal_window": ""}, {"transformation": ""},
    {"uses_historical_information": "false"}, {"information_kind": "unknown"},
    {"uses_historical_information": True},
])
def test_invalid_feature_provenance(bundle, change):
    pipeline, _, _, _ = bundle
    evidence = json.loads(pipeline.provenance_path.read_text(encoding="utf-8"))
    evidence["features"]["a"].update(change)
    pipeline.provenance_path.write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(FeatureSchemaMismatch):
        pipeline.load_model()


def test_static_and_historical_information_allowed(bundle):
    pipeline, _, _, _ = bundle
    evidence = json.loads(pipeline.provenance_path.read_text(encoding="utf-8"))
    evidence["features"]["a"].update(
        uses_historical_information=True, temporal_window="2022-01/2024-12",
        max_information_date="2024-12-31",
        historical_context="Environmental cover context; crop identification unavailable.",
    )
    evidence["features"]["b"].update(
        information_kind="static", temporal_window="static", max_information_date=None,
    )
    pipeline.provenance_path.write_text(json.dumps(evidence), encoding="utf-8")
    pipeline.load_model()
    assert pipeline.predict("001") == 32


def test_stale_csv_evidence_rejected(bundle):
    pipeline, _, _, _ = bundle
    pipeline.features_path.write_text("parcel_id,a,b\n001,20,30\n", encoding="utf-8")
    with pytest.raises(FeatureSchemaMismatch, match="CSV"):
        pipeline.load_model()


def test_data_version_mismatch_rejected(bundle):
    pipeline, _, _, _ = bundle
    evidence = json.loads(pipeline.provenance_path.read_text(encoding="utf-8"))
    evidence["data_version"] = "other-data"
    pipeline.provenance_path.write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(FeatureSchemaMismatch, match="Versión"):
        pipeline.load_model()


def test_model_data_version_mismatch_rejected(bundle):
    pipeline, _, artifact, _ = bundle
    artifact["metadata"]["data_version"] = "other-data"
    with pytest.raises(FeatureSchemaMismatch, match="versiones"):
        pipeline.load_model()


def test_raw_predictor_with_embedded_metadata(bundle, monkeypatch):
    pipeline, _, artifact, _ = bundle
    model = artifact["model"]
    model.cebada_metadata_ = artifact["metadata"]
    monkeypatch.setattr(inference, "_deserialize", lambda path: model)
    pipeline.load_model()
    assert pipeline.predict("001") == 32


def test_unbound_raw_model_is_rejected(bundle, monkeypatch):
    pipeline, _, artifact, _ = bundle
    monkeypatch.setattr(inference, "_deserialize", lambda path: artifact["model"])
    with pytest.raises(FeatureSchemaMismatch, match="vincular"):
        pipeline.load_model()


def write_manifest(pipeline, schema):
    manifest = {field: schema[field] for field in inference.VERSION_FIELDS}
    manifest.update(model_sha256=inference._sha256(pipeline.model_path),
                    feature_schema_sha256=inference._sha256(pipeline.schema_path))
    pipeline.model_manifest_path = pipeline.schema_path.parent / "manifest.json"
    pipeline.model_manifest_path.write_text(json.dumps(manifest), encoding="utf-8")


@pytest.mark.parametrize("tamper", [None, "schema", "model", "manifest"])
def test_real_raw_model_manifest_binding(bundle, monkeypatch, tamper):
    import joblib
    from sklearn.linear_model import LinearRegression

    pipeline, schema, _, _ = bundle
    model = LinearRegression().fit([[0, 0], [1, 0], [0, 1], [1, 1]], [0, 10, 1, 11])
    joblib.dump(model, pipeline.model_path)
    write_manifest(pipeline, schema)
    monkeypatch.setattr(inference, "_deserialize", joblib.load)
    if tamper == "schema":
        schema["features"] = ["a", "b"]
        pipeline.schema_path.write_text(json.dumps(schema), encoding="utf-8")
    elif tamper == "model":
        with pipeline.model_path.open("ab") as stream:
            stream.write(b"different model")
    elif tamper == "manifest":
        manifest = json.loads(pipeline.model_manifest_path.read_text(encoding="utf-8"))
        manifest["model_version"] = "other-model"
        pipeline.model_manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    if tamper:
        with pytest.raises(FeatureSchemaMismatch):
            pipeline.load_model()
        assert not pipeline.model_loaded
    else:
        pipeline.load_model()
        assert pipeline.predict("001") == pytest.approx(32)


def test_no_fixed_parcel_count_or_training_during_prediction(bundle):
    pipeline, _, artifact, _ = bundle

    def forbidden(*args):
        raise AssertionError("Training during inference")

    artifact["model"].fit = forbidden
    pipeline.load_model()
    # Solo dos IDs en este catálogo: no se exige una constante 138/59/197.
    assert pipeline.predict("001") == 32


def test_named_model_features_must_match_schema(bundle):
    pipeline, _, artifact, _ = bundle
    artifact["model"].feature_names_in_ = ["a", "b"]
    with pytest.raises(FeatureSchemaMismatch, match="nombres"):
        pipeline.load_model()


def test_frozen_named_preprocessing_is_preserved(bundle, monkeypatch):
    import joblib
    import pandas as pd
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LinearRegression
    from sklearn.pipeline import make_pipeline

    pipeline, _, artifact, _ = bundle
    X = pd.DataFrame([[0, 0], [1, 0], [0, 1], [1, 1]], columns=["b", "a"])
    model = make_pipeline(
        ColumnTransformer([("numbers", SimpleImputer(), ["b", "a"])]),
        LinearRegression(),
    ).fit(X, [0, 10, 1, 11])
    model.cebada_metadata_ = artifact["metadata"]
    joblib.dump(model, pipeline.model_path)
    monkeypatch.setattr(inference, "_deserialize", joblib.load)
    pipeline.load_model()
    assert pipeline.predict("001") == pytest.approx(32)
