"""Perfil interno de artefactos, compatible con System Contract 0.3.0.

No importa joblib ni ejecuta modelos. Los hashes vinculan archivos; no certifican
su autoría, sus datos de entrenamiento ni el corte temporal de las features.
"""
import hashlib
import re
from datetime import date
from pathlib import Path

VERSION_FIELDS = ("contract_version", "model_version", "feature_schema_version", "data_version")
BUNDLE_VERSION = "1.0.0"


class ArtifactContractError(ValueError):
    pass


def confirmed(value):
    return (isinstance(value, str) and bool(value.strip()) and "PENDIENTE" not in value.upper()
            and not value.strip().startswith("<"))


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def valid_digest(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def filename(value, suffix):
    if (not confirmed(value) or value != value.strip() or any(c in value for c in '/\\:\x00')
            or Path(value).suffix != suffix or value in (".", "..")):
        raise ArtifactContractError("El artefacto requiere un nombre de archivo local válido.")
    return value


def validate_feature_schema(schema, *, delivery=False):
    if not isinstance(schema, dict):
        raise ArtifactContractError("Schema inválido.")
    for field in (*VERSION_FIELDS, "target_name", "prediction_unit", "target_cycle",
                  "prediction_information_cutoff", "training_id_source", "missing_value_policy"):
        if not confirmed(schema.get(field)):
            raise ArtifactContractError(f"Falta confirmar {field} en el schema.")
    if schema["contract_version"] != "0.3.0":
        raise ArtifactContractError("El schema requiere contract_version 0.3.0.")
    if schema["prediction_unit"] != "t/ha" or schema["target_cycle"] != "2025-04/2025-10":
        raise ArtifactContractError("Unidad o ciclo incompatible con el rendimiento solicitado.")
    features = schema.get("features")
    if (not isinstance(features, list) or not features or any(not confirmed(f) for f in features)
            or len(set(features)) != len(features) or "parcel_id" in features
            or schema["target_name"] in features
            or (schema.get("target_column") and schema["target_column"] in features)):
        raise ArtifactContractError("Lista de features inválida o contiene el target.")
    if "id_column" in schema and schema["id_column"] != "parcel_id":
        raise ArtifactContractError("El CSV de inferencia requiere el alias interno parcel_id.")
    if "n_features" in schema and (type(schema["n_features"]) is not int or schema["n_features"] != len(features)):
        raise ArtifactContractError("n_features no coincide con la lista de features.")
    if schema["missing_value_policy"] == "documented" and not confirmed(schema.get("missing_value_policy_detail")):
        raise ArtifactContractError("La política documented requiere su descripción técnica.")
    try:
        cutoff = date.fromisoformat(schema["prediction_information_cutoff"])
    except (ValueError, TypeError) as exc:
        raise ArtifactContractError("Corte temporal inválido.") from exc
    if cutoff.isoformat() != schema["prediction_information_cutoff"] or cutoff > date(2025, 10, 31):
        raise ArtifactContractError("El schema excede el cierre operativo o no usa YYYY-MM-DD.")
    for field in ("model_sha256",):
        if field in schema and not valid_digest(schema[field]):
            raise ArtifactContractError(f"{field} no es un SHA256 válido.")
    if "model_file" in schema:
        filename(schema["model_file"], ".joblib")
    for field, rejected in (("verified", False), ("fast_mode", True)):
        if field in schema and (type(schema[field]) is not bool or schema[field] == rejected):
            raise ArtifactContractError(f"{field} identifica un artefacto no aceptable para inferencia final.")
    if "environment" in schema:
        validate_environment(schema["environment"])
    if delivery:
        for field in ("model_file", "model_sha256", "n_features", "environment"):
            if field not in schema:
                raise ArtifactContractError(f"La entrega versionada requiere {field}.")
    return features, cutoff


def validate_environment(environment):
    if not isinstance(environment, dict) or not isinstance(environment.get("python"), str):
        raise ArtifactContractError("Falta el entorno de exportación del modelo.")
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:[a-zA-Z0-9.+-]*)?", environment["python"]):
        raise ArtifactContractError("La versión de Python exportador no es válida.")
    packages = environment.get("packages")
    if not isinstance(packages, dict) or not confirmed(packages.get("joblib")):
        raise ArtifactContractError("Se requiere la versión de joblib usada al exportar.")
    if any(not confirmed(k) or (v is not None and not confirmed(v)) for k, v in packages.items()):
        raise ArtifactContractError("Versiones de paquetes inválidas.")


def verify_model_file(model_path, schema):
    """Comprueba una asociación declarada por ML, antes de deserializar."""
    if "model_file" in schema and Path(model_path).name != schema["model_file"]:
        raise ArtifactContractError("El nombre del modelo no coincide con el schema.")
    if "model_sha256" not in schema:
        return False
    if sha256(model_path) != schema["model_sha256"]:
        raise ArtifactContractError("El SHA256 del modelo no coincide con el schema.")
    return True
