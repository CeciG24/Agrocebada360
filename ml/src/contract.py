"""Validaciones del system-contract.md (v0.1.0) del lado de Modelado.

- §3 IDs/faltantes, §5 feature_schema.json, §6 inferencia, §13 errores explícitos.
Nada aquí inventa columnas, imputa por su cuenta ni sustituye fallos por valores sintéticos.
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from . import config as C


# ---- §13 errores internos explícitos ----
class ContractError(Exception): ...
class FeatureSchemaMismatch(ContractError): ...
class ModelNotLoaded(ContractError): ...
class ParcelNotFound(ContractError): ...
class PredictionUnavailable(ContractError): ...


# ---- §3 datos de entrada ----
def validate_ids(df, name="df"):
    ids = df[C.ID]
    if ids.isna().any():
        raise ContractError(f"{name}: {C.ID} con nulos")
    if not ids.map(lambda v: isinstance(v, str)).all():
        raise ContractError(f"{name}: {C.ID} debe ser string (§3.2), no convertir a entero")
    if ids.duplicated().any():
        raise ContractError(f"{name}: {C.ID} duplicados: {ids[ids.duplicated()].tolist()[:5]}")


def validate_catalog(root=None):
    """IDs coinciden entre parcel_master, features_master, rendimiento y topografía (DoD §15)."""
    root = Path(root or C.DATA_ROOT)
    rd = lambda p: pd.read_csv(root / p, dtype={C.ID: str})
    sets = {"parcel_master": rd("parcel_master.csv"), "features_master": rd("features/features_master.csv"),
            "rendimiento": rd("targets/rendimiento.csv"), "topografia": rd("topografia/topography_master.csv")}
    ref = set(sets["parcel_master"][C.ID])
    for n, d in sets.items():
        validate_ids(d, n)
        if set(d[C.ID]) != ref:
            raise ContractError(f"{n}: IDs no coinciden con parcel_master "
                                f"(faltan {len(ref - set(d[C.ID]))}, sobran {len(set(d[C.ID]) - ref)})")
    return sets["parcel_master"]


def validate_features(df, cols):
    """Features finitas, numéricas, sin target-like y sin columnas derivadas por Modelado (no inventar columnas)."""
    derived = [c for c in cols if c.startswith("mun_") or c == "grupo_espacial"]
    if derived:
        raise FeatureSchemaMismatch(f"Features derivadas en Modelado no pueden entrar al schema oficial: {derived[:5]}")
    bad = [c for c in cols if c not in df.columns]
    if bad:
        raise FeatureSchemaMismatch(f"Faltan features requeridas: {bad[:10]}")
    X = df[cols]
    nonnum = [c for c in cols if not pd.api.types.is_numeric_dtype(X[c])]
    if nonnum:
        raise FeatureSchemaMismatch(f"Features no numéricas: {nonnum[:10]}")
    if np.isinf(X.to_numpy(float)).any():
        raise ContractError("Features con infinitos")
    if TARGET_LIKE(cols):
        raise ContractError(f"Posible fuga de target en features: {TARGET_LIKE(cols)}")


def TARGET_LIKE(cols):
    return [c for c in cols if c == C.TARGET or "rendimiento" in c.lower() or "yield" in c.lower()]


# ---- §5 feature_schema.json ----
def build_schema(features, *, model_version=None, extra=None):
    schema = {
        "model_version": model_version or C.MODEL_VERSION,
        "feature_schema_version": C.FEATURE_SCHEMA_VERSION,
        "contract_version": C.CONTRACT_VERSION,
        "target": "yield",
        "target_column": C.TARGET,
        "unit": C.UNIT,
        "id_column": C.ID,
        "features": list(features),               # el ORDEN es contractual (§5.2)
        "missing_value_policy": "documented",
        "missing_value_policy_detail": ("features_master.csv no contiene NaN. Si aparecieran, el Pipeline imputa con la "
                                        "mediana del train (SimpleImputer ajustado dentro del fit); el backend no imputa."),
        "data_cutoff": C.DATA_CUTOFF,
    }
    schema.update(extra or {})
    return schema


def save_artifacts(model, schema, models_dir=None):
    d = Path(models_dir or C.MODELS); d.mkdir(parents=True, exist_ok=True)
    stem = "yield_model_" + schema["model_version"].replace("yield-", "")
    mp, sp = d / f"{stem}.joblib", d / "feature_schema.json"
    joblib.dump(model, mp)                         # solo el modelo; las features viven en el schema
    sp.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")
    return mp, sp


def load_artifacts(models_dir=None, model_path=None):
    d = Path(models_dir or C.MODELS)
    sp = d / "feature_schema.json"
    if not sp.exists():
        raise ModelNotLoaded(f"No existe {sp}")
    schema = json.loads(sp.read_text(encoding="utf-8"))
    stem = "yield_model_" + schema["model_version"].replace("yield-", "")
    mp = Path(model_path) if model_path else d / f"{stem}.joblib"
    if not mp.exists():
        raise ModelNotLoaded(f"No existe {mp} (la versión del schema {schema['model_version']} no coincide con ningún artefacto)")
    try:
        model = joblib.load(mp)
    except Exception as e:                         # noqa: BLE001
        raise ModelNotLoaded(f"No se pudo cargar {mp}: {e}") from e
    return model, schema


# ---- §6 inferencia ----
def predict_frame(model, schema, df):
    """Selecciona features EXACTAMENTE en el orden del schema, valida y predice. Falla si algo no cuadra."""
    feats = schema["features"]
    missing = [c for c in feats if c not in df.columns]
    if missing:
        raise FeatureSchemaMismatch(f"Faltan features del schema: {missing[:10]}")
    validate_features(df, feats)
    pred = np.asarray(model.predict(df[feats].to_numpy(float)), float)
    if not np.isfinite(pred).all():
        raise PredictionUnavailable("El modelo produjo NaN/inf (§6)")
    return pd.Series(pred, index=df[C.ID].values, name="prediction")


def validate_predictions(out, expected_ids, n_expected=C.N_EVAL):
    if len(out) != n_expected:
        raise ContractError(f"Se esperaban {n_expected} predicciones y hay {len(out)}")
    validate_ids(out, "predictions")
    if set(out[C.ID]) != set(expected_ids):
        raise ContractError("IDs de predicciones no coinciden con las parcelas de evaluación")
    v = out["rendimiento_pred_t_ha"].to_numpy(float)
    if not np.isfinite(v).all():
        raise ContractError("Predicciones con NaN/inf")
