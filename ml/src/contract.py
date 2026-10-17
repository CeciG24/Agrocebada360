"""Validaciones del system-contract.md (v0.3.0) del lado de Modelado.

- §5 datos/IDs/faltantes · §7 feature_schema.json y artefactos · §8 inferencia · §12 versiones · §14 submission.
Nada aquí inventa columnas, imputa por su cuenta ni sustituye fallos por valores sintéticos.

Cambios clave frente a v0.1.0 (audit-2026-10-14, Persona 2):
  * schema 0.3.0 (target_name, prediction_unit, target_cycle, prediction_information_cutoff, training_id_source, data_version…)
  * asociación VERIFICABLE modelo<->schema: sha256 del joblib, versión, nº de features y orden (feature_names_in_)
  * exportar exige auditoría válida PARA ESE dataset (hash), salvo --allow-unverified explícito
  * ya no se valida contra constantes 138/59 sino contra listas oficiales de IDs
"""
import hashlib
import json
import warnings
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from . import config as C
from . import provenance as PV


# ---- §13 errores internos explícitos ----
class ContractError(Exception): ...
class FeatureSchemaMismatch(ContractError): ...
class ModelNotLoaded(ContractError): ...
class ArtifactMismatch(ContractError): ...          # el modelo no corresponde al schema (hash/versión/nº o orden de features)
class AuditNotValid(ContractError): ...             # no hay auditoría válida para el dataset concreto
class ParcelNotFound(ContractError): ...
class PredictionUnavailable(ContractError): ...


# ---- §5 datos de entrada ----
def validate_ids(df, name="df"):
    ids = df[C.ID]
    if ids.isna().any():
        raise ContractError(f"{name}: {C.ID} con nulos")
    if not ids.map(lambda v: isinstance(v, str)).all():
        raise ContractError(f"{name}: {C.ID} debe ser string (§5.1), no convertir a entero")
    if ids.duplicated().any():
        raise ContractError(f"{name}: {C.ID} duplicados: {ids[ids.duplicated()].tolist()[:5]}")


def validate_catalog(root=None):
    """IDs coinciden entre parcel_master, features_master, rendimiento y topografía (DoD §18)."""
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


# §5.6: no existen a nivel parcela; no deben usarse como features oficiales.
FORBIDDEN_FEATURE_HINTS = ("siembra", "planting", "dosis", "variedad", "variety", "josefa", "voyager",
                           "siniestro", "granizo", "helada", "plaga", "historial_cultivo")


def TARGET_LIKE(cols):
    return [c for c in cols if c == C.TARGET or "rendimiento" in c.lower() or "yield" in c.lower()]


def validate_features(df, cols):
    """Features finitas, numéricas, sin target-like, sin variables no disponibles (§5.6) ni derivadas por Modelado."""
    derived = [c for c in cols if c.startswith("mun_") or c == "grupo_espacial"]
    if derived:
        raise FeatureSchemaMismatch(f"Features derivadas en Modelado no pueden entrar al schema oficial: {derived[:5]}")
    if len(set(cols)) != len(cols):
        raise FeatureSchemaMismatch("Features duplicadas en la lista")
    bad = [c for c in cols if c not in df.columns]
    if bad:
        raise FeatureSchemaMismatch(f"Faltan features requeridas: {bad[:10]}")
    forb = [c for c in cols if any(h in c.lower() for h in FORBIDDEN_FEATURE_HINTS)]
    if forb:
        raise FeatureSchemaMismatch(f"Variables no disponibles a nivel parcela (§5.6): {forb[:5]}")
    X = df[list(cols)]
    nonnum = [c for c in cols if not pd.api.types.is_numeric_dtype(X[c])]
    if nonnum:
        raise FeatureSchemaMismatch(f"Features no numéricas: {nonnum[:10]}")
    if np.isinf(X.to_numpy(float)).any():
        raise ContractError("Features con infinitos")
    if TARGET_LIKE(cols):
        raise ContractError(f"Posible fuga de target en features: {TARGET_LIKE(cols)}")


# ---- auditoría válida para el dataset concreto (audit-2026-10-14, Persona 2, pend. 4) ----
def require_valid_audit(root=None, allow_unverified=False):
    """Devuelve el estado de la auditoría. Si no es válida y el modo es estricto, lanza AuditNotValid."""
    st = PV.audit_state(root)
    if not st["valid"]:
        if C.STRICT_CUTOFF and not allow_unverified:
            raise AuditNotValid("Exportación bloqueada: " + st["reason"] +
                                " (para pruebas exploratorias: --allow-unverified; el artefacto quedará marcado como NO verificado)")
        warnings.warn("ARTEFACTO NO VERIFICADO: " + st["reason"])
    return st


# ---- §7.2 feature_schema.json ----
REQUIRED_SCHEMA_KEYS = ("model_version", "feature_schema_version", "contract_version", "data_version", "target_name",
                        "prediction_unit", "target_cycle", "prediction_information_cutoff", "training_id_source",
                        "missing_value_policy", "features", "model_file", "model_sha256")


def build_schema(features, *, model_version=None, extra=None, root=None):
    """Schema alineado con contrato 0.3.0 §7.2 (+ campos de trazabilidad). `model_file`/`model_sha256` los fija save_artifacts."""
    schema = {
        "model_version": model_version or C.MODEL_VERSION,
        "feature_schema_version": C.FEATURE_SCHEMA_VERSION,
        "contract_version": C.CONTRACT_VERSION,
        "data_version": PV.data_version(root),
        "target_name": C.TARGET,
        "target_name_status": "alias interno (mapeo observado RENDIMIENTO_T_HA -> rendimiento_t_ha); nombre oficial PENDIENTE (§20)",
        "prediction_unit": C.UNIT,
        "target_cycle": C.TARGET_CYCLE,
        "prediction_information_cutoff": C.DATA_CUTOFF,
        "prediction_information_cutoff_note": "convención técnica de cierre de octubre-2025 (§2.3); FIRA confirma el mes, no el día",
        "training_id_source": "split/official_ids_v1.json (derivada de dataset_split; contrastar con la lista oficial de FIRA, §20)",
        "id_column": C.ID,
        "id_source_name": "ID_POLIGONO (mapeo observado; nombre oficial PENDIENTE, §20)",
        "features": list(features),                # el ORDEN es contractual (§7.3)
        "n_features": len(features),
        "missing_value_policy": "documented",
        "missing_value_policy_detail": ("Los NaN se imputan con la MEDIANA DEL TRAIN mediante SimpleImputer dentro del Pipeline "
                                        "(ajustado en fit); el backend no imputa. En el dataset revisado hay 2 NaN en "
                                        "planet_ndvi_decay_rate (parcelas de evaluación), compatibles con parcelas sin días "
                                        "posteriores al pico; no se rellenaron aguas arriba."),
        "history_note": "Hay features con histórico 2022–2024 usado como CONTEXTO AMBIENTAL; no implica cultivo de cebada en esos años (§2.2, §5.4).",
        "unavailable_variables_excluded": ["fecha de siembra", "dosis de siembra", "historial de cultivo 2022-2024",
                                           "siniestros 2025", "variedad por parcela"],
        "environment": PV.env_versions(),
        "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    schema.update(extra or {})
    return schema


def validate_schema(schema):
    miss = [k for k in REQUIRED_SCHEMA_KEYS if k not in schema]
    if miss:
        raise FeatureSchemaMismatch(f"feature_schema.json incompleto (contrato 0.3.0 §7.2). Faltan: {miss}")
    f = schema["features"]
    if not isinstance(f, list) or not f or len(set(f)) != len(f):
        raise FeatureSchemaMismatch("`features` debe ser una lista no vacía y sin duplicados")
    if any(c.startswith("mun_") or c == "grupo_espacial" for c in f):
        raise FeatureSchemaMismatch("El schema incluye columnas derivadas por Modelado (mun_*, grupo_espacial)")
    if schema.get("n_features", len(f)) != len(f):
        raise FeatureSchemaMismatch("n_features no coincide con len(features)")
    if str(schema["contract_version"]).split(".")[:2] != C.CONTRACT_VERSION.split(".")[:2]:
        raise ArtifactMismatch(f"El schema es del contrato {schema['contract_version']} y el código es {C.CONTRACT_VERSION}")


def _stem(model_version):
    return "yield_model_" + model_version.replace("yield-", "")


def _n_features(model):
    n = getattr(model, "n_features_in_", None)
    if n is None and hasattr(model, "feature_names_"):          # CatBoost
        n = len(model.feature_names_)
    return None if n is None else int(n)


def _feature_names(model):
    names = getattr(model, "feature_names_in_", None)
    if names is None and hasattr(model, "feature_names_"):
        names = model.feature_names_
    return None if names is None else [str(x) for x in names]


def save_artifacts(model, schema, models_dir=None):
    """Guarda SOLO el modelo (joblib) y el schema, y los ata: sha256 del archivo, nº de features y orden se verifican al cargar."""
    sch = {k: v for k, v in schema.items()}
    d = Path(models_dir or C.MODELS); d.mkdir(parents=True, exist_ok=True)
    feats = list(schema["features"])
    n = _n_features(model)
    if n is not None and n != len(feats):
        raise ArtifactMismatch(f"El modelo se entrenó con {n} features y el schema declara {len(feats)}")
    names = _feature_names(model)
    if names is not None and names != feats:
        raise ArtifactMismatch("El orden/nombres de features del modelo no coincide con el schema")
    mp, sp = d / f"{_stem(schema['model_version'])}.joblib", d / "feature_schema.json"
    joblib.dump(model, mp)
    sch["model_file"] = mp.name
    sch["model_sha256"] = PV.sha256_file(mp)
    validate_schema(sch)
    sp.write_text(json.dumps(sch, indent=2, ensure_ascii=False), encoding="utf-8")
    return mp, sp


def load_artifacts(models_dir=None, model_path=None):
    """Carga y VERIFICA: sha256, versión, nº de features y orden. Nunca acepta un modelo "parecido" sin error.

    Antes (audit-2026-10-14): pasar otro archivo de modelo se aceptaba sin comprobar nada y una prueba sintética dio
    23 predicciones en vez de 32 sin error. Ahora cualquier discrepancia lanza ArtifactMismatch.
    """
    d = Path(models_dir or C.MODELS)
    sp = d / "feature_schema.json"
    if not sp.exists():
        raise ModelNotLoaded(f"No existe {sp}")
    schema = PV.read_json_tolerant(sp)
    validate_schema(schema)
    mp = Path(model_path) if model_path else d / schema["model_file"]
    if not mp.exists():
        raise ModelNotLoaded(f"No existe {mp}")
    if _stem(schema["model_version"]) != Path(schema["model_file"]).stem:
        raise ArtifactMismatch("model_file no corresponde a model_version en el schema")
    if PV.sha256_file(mp) != schema["model_sha256"]:
        raise ArtifactMismatch(f"{mp.name}: el sha256 no coincide con el del schema (modelo distinto al declarado)")
    try:
        model = joblib.load(mp)
    except Exception as e:                         # noqa: BLE001
        raise ModelNotLoaded(f"No se pudo cargar {mp}: {e}") from e
    feats = schema["features"]
    n = _n_features(model)
    if n is not None and n != len(feats):
        raise ArtifactMismatch(f"El modelo espera {n} features y el schema declara {len(feats)}")
    names = _feature_names(model)
    if names is not None and names != feats:
        raise ArtifactMismatch("El orden/nombres de features del modelo no coincide con el schema")
    cur = PV.env_versions()["packages"]; was = schema.get("environment", {}).get("packages", {})
    for pkg in ("scikit-learn", "catboost", "xgboost", "lightgbm"):
        if was.get(pkg) and cur.get(pkg) and was[pkg] != cur[pkg]:
            warnings.warn(f"{pkg} {cur[pkg]} difiere de {was[pkg]} usado al entrenar: reproducibilidad no garantizada")
    return model, schema


# ---- §8 inferencia ----
def predict_frame(model, schema, df):
    """Selecciona features EXACTAMENTE en el orden del schema (DataFrame: sklearn verifica nombres), valida y predice."""
    feats = schema["features"]
    missing = [c for c in feats if c not in df.columns]
    if missing:
        raise FeatureSchemaMismatch(f"Faltan features del schema: {missing[:10]}")
    validate_features(df, feats)
    X = df[feats]
    pred = np.asarray(model.predict(X), float)
    if pred.shape != (len(df),):
        raise PredictionUnavailable(f"El modelo devolvió {pred.shape} para {len(df)} filas")
    if not np.isfinite(pred).all():
        raise PredictionUnavailable("El modelo produjo NaN/inf (§8)")
    return pd.Series(pred, index=df[C.ID].values, name="prediction")


def validate_predictions(out, expected_ids, *, decimals=None, col=None):
    """§14: cobertura EXACTA de la lista oficial de IDs (sin número fijo), únicos, finitos; `decimals` exige esa precisión."""
    col = col or C.PRED_COL
    expected = set(expected_ids)
    if len(out) != len(expected):
        raise ContractError(f"Se esperaban {len(expected)} predicciones (lista oficial) y hay {len(out)}")
    validate_ids(out, "predictions")
    got = set(out[C.ID])
    if got != expected:
        raise ContractError(f"IDs no coinciden con la lista oficial (faltan {sorted(expected - got)[:5]}, sobran {sorted(got - expected)[:5]})")
    v = out[col].to_numpy(float)
    if not np.isfinite(v).all():
        raise ContractError("Predicciones con NaN/inf")
    if decimals is not None and not np.allclose(v, np.round(v, decimals), atol=0, rtol=0):
        raise ContractError(f"Las predicciones deben exportarse con {decimals} decimales (§1.1/§14)")
