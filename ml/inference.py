"""Inferencia sin entrenamiento, según system-contract v0.3.0.

Los formatos de manifest/procedencia son decisiones internas documentadas en
docs/inference-pipeline.md; no se presentan como requisitos oficiales de FIRA.
"""

import csv
import hashlib
import math
from datetime import date
from numbers import Real
from pathlib import Path

from ml.artifact_contract import (
    ArtifactContractError, VERSION_FIELDS, validate_feature_schema, verify_model_file,
)
from ml.model_bundle import MANIFEST_FILE, inspect_bundle, read_json


class InferenceError(Exception):
    """Error interno que el adaptador HTTP debe traducir al contrato público."""


class FeatureSchemaMismatch(InferenceError):
    pass


class ModelNotLoaded(InferenceError):
    pass


class ParcelNotFound(InferenceError):
    pass


class PredictionUnavailable(InferenceError):
    pass


def _read_json(path):
    return read_json(path)


def _deserialize(path):
    # Solo cargar artefactos de confianza: joblib puede ejecutar código.
    import joblib
    return joblib.load(path)


def _valid_id(value):
    return isinstance(value, str) and bool(value.strip())


def _confirmed(value):
    return (_valid_id(value) and "PENDIENTE" not in value.upper()
            and not value.strip().startswith("<"))


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _date(value):
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise FeatureSchemaMismatch("Las fechas requieren formato YYYY-MM-DD.")
    return parsed


class InferencePipeline:
    """Carga una vez el modelo, schema y features; predict nunca entrena.

    Data/ETL entrega la procedencia por feature y su vínculo con el CSV.
    Los IDs proceden del catálogo oficial validado por el adaptador de Data.
    Modelo directo: vínculo mediante SHA256 en schema o manifest de ML.
    El paquete P4.7 añade el hash del schema, sin alterar el joblib de ML.
    """

    def __init__(self, model_path, schema_path, features_path, provenance_path, catalog_ids,
                 *, model_manifest_path=None):
        if isinstance(catalog_ids, (str, bytes)):
            raise FeatureSchemaMismatch("Se requiere una lista de IDs del catálogo, no una cadena.")
        ids = list(catalog_ids)
        if any(not _valid_id(value) for value in ids) or len(set(ids)) != len(ids):
            raise FeatureSchemaMismatch("El catálogo requiere IDs string únicos y no vacíos.")
        self.model_path = Path(model_path)
        self.schema_path = Path(schema_path)
        self.features_path = Path(features_path)
        self.provenance_path = Path(provenance_path)
        self.model_manifest_path = Path(model_manifest_path) if model_manifest_path is not None else None
        self.catalog_ids = frozenset(ids)
        self._model = None
        self._schema = None
        self._rows = None

    @classmethod
    def from_bundle(cls, bundle_path, features_path, provenance_path, catalog_ids):
        """Verifica el paquete P4.7; load_model aún exige procedencia de Data."""
        try:
            report = inspect_bundle(bundle_path)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            raise FeatureSchemaMismatch("Paquete de modelo inválido.") from exc
        root = Path(bundle_path)
        return cls(root / report["model_file"], root / report["feature_schema_file"],
                   features_path, provenance_path, catalog_ids,
                   model_manifest_path=root / MANIFEST_FILE)

    @property
    def model_loaded(self):
        return self._model is not None

    @property
    def model_version(self):
        self._require_loaded()
        return self._schema["model_version"]

    @property
    def unit(self):
        self._require_loaded()
        return self._schema["prediction_unit"]

    def _validate_schema(self, schema):
        try:
            return validate_feature_schema(schema)
        except ArtifactContractError as exc:
            raise FeatureSchemaMismatch(str(exc)) from exc

    def _validate_provenance(self, schema, cutoff):
        provenance = _read_json(self.provenance_path)
        if not isinstance(provenance, dict) or provenance.get("data_version") != schema["data_version"]:
            raise FeatureSchemaMismatch("Versión de datos incompatible con la procedencia.")
        if provenance.get("features_file_sha256") != _sha256(self.features_path):
            raise FeatureSchemaMismatch("La evidencia no corresponde al CSV de features cargado.")
        metadata = provenance.get("features")
        if not isinstance(metadata, dict):
            raise FeatureSchemaMismatch("Falta metadata técnica por feature.")
        for feature in schema["features"]:
            item = metadata.get(feature)
            if not isinstance(item, dict):
                raise FeatureSchemaMismatch(f"Falta procedencia para {feature}.")
            for field in ("source", "sensor_or_dataset", "temporal_window", "transformation",
                          "missing_value_policy"):
                if not _confirmed(item.get(field)):
                    raise FeatureSchemaMismatch(f"Falta confirmar {field} de {feature}.")
            if type(item.get("uses_historical_information")) is not bool:
                raise FeatureSchemaMismatch(f"Falta declarar el uso histórico de {feature}.")
            if item.get("information_kind") not in ("static", "temporal"):
                raise FeatureSchemaMismatch(f"Tipo de información no declarado para {feature}.")
            maximum = item.get("max_information_date")
            if item["information_kind"] == "temporal" and maximum is None:
                raise FeatureSchemaMismatch(f"Falta la fecha máxima de información para {feature}.")
            if maximum is not None and _date(maximum) > cutoff:
                raise FeatureSchemaMismatch(f"{feature} utiliza información posterior al corte.")
            if (item["uses_historical_information"]
                    and not _confirmed(item.get("historical_context"))):
                raise FeatureSchemaMismatch(f"Falta documentar la semántica histórica de {feature}.")

    def _validate_manifest(self, schema):
        if self.model_manifest_path is None:
            return False
        manifest = _read_json(self.model_manifest_path)
        if isinstance(manifest, dict) and "bundle_format_version" in manifest:
            if self.model_manifest_path.name != MANIFEST_FILE:
                raise FeatureSchemaMismatch("Nombre de manifest P4.7 incompatible.")
            report = inspect_bundle(self.model_manifest_path.parent)
            if (report["model_file"] != self.model_path.name
                    or report["feature_schema_file"] != self.schema_path.name
                    or self.model_path.resolve().parent != self.model_manifest_path.resolve().parent
                    or self.schema_path.resolve().parent != self.model_manifest_path.resolve().parent):
                raise FeatureSchemaMismatch("Las rutas no corresponden al paquete verificado.")
        if not isinstance(manifest, dict) or any(
                manifest.get(field) != schema[field] for field in VERSION_FIELDS):
            raise FeatureSchemaMismatch("Versiones del manifest incompatibles con el schema.")
        if (manifest.get("model_sha256") != _sha256(self.model_path)
                or manifest.get("feature_schema_sha256") != _sha256(self.schema_path)):
            raise FeatureSchemaMismatch("El manifest no corresponde al modelo y schema congelados.")
        return True

    def _require_loaded(self):
        if not self.model_loaded:
            raise ModelNotLoaded("El pipeline no está cargado.")

    def load_model(self):
        """Carga atómica e idempotente. Un fallo deja el pipeline sin cargar."""
        if self.model_loaded:
            return self._model
        try:
            schema = _read_json(self.schema_path)
            features, cutoff = self._validate_schema(schema)
            self._validate_provenance(schema, cutoff)
            rows = self._load_features(features)
        except InferenceError:
            raise
        except (OSError, ValueError, TypeError, KeyError, csv.Error) as exc:
            raise FeatureSchemaMismatch("Schema, features o evidencia temporal inválidos.") from exc

        try:
            schema_verified = verify_model_file(self.model_path, schema)
            manifest_verified = self._validate_manifest(schema)
        except InferenceError:
            raise
        except OSError as exc:
            raise ModelNotLoaded("No se pudo leer el modelo o manifest.") from exc
        except (ValueError, TypeError, KeyError) as exc:
            raise FeatureSchemaMismatch("Manifest del modelo inválido.") from exc
        try:
            artifact = _deserialize(self.model_path)
        except Exception as exc:
            raise ModelNotLoaded("No se pudo cargar el artefacto del modelo.") from exc
        if isinstance(artifact, dict):
            if (not isinstance(artifact.get("features"), list)
                    or artifact.get("version") != schema["model_version"]
                    or artifact["features"] != features):
                raise FeatureSchemaMismatch("Versión u orden de features incompatible con el modelo.")
            model = artifact.get("model")
            metadata = artifact.get("metadata", {})
        else:
            model = artifact
            metadata = getattr(model, "cebada_metadata_", {})
        if metadata:
            if not isinstance(metadata, dict) or any(
                    metadata.get(field) != schema[field] for field in VERSION_FIELDS):
                raise FeatureSchemaMismatch("Las versiones del modelo y schema no coinciden.")
            if metadata.get("features") != features:
                raise FeatureSchemaMismatch("El orden de features del modelo y schema no coincide.")
        elif not (manifest_verified or schema_verified):
            raise FeatureSchemaMismatch("Falta vincular modelo y schema mediante metadata o manifest de ML.")
        if not callable(getattr(model, "predict", None)):
            raise ModelNotLoaded("El artefacto no contiene un predictor.")
        if getattr(model, "n_features_in_", len(features)) != len(features):
            raise FeatureSchemaMismatch("El modelo espera otra cantidad de features.")
        names = getattr(model, "feature_names_in_", None)
        if names is not None and list(names) != features:
            raise FeatureSchemaMismatch("Los nombres del modelo no coinciden con el schema.")
        self._schema, self._rows, self._model = schema, rows, model
        return model

    def _load_features(self, features):
        rows = {}
        with self.features_path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            fields = reader.fieldnames or []
            if (len(fields) != len(set(fields))
                    or not {"parcel_id", *features}.issubset(fields)):
                raise FeatureSchemaMismatch("Falta parcel_id o una feature requerida; encabezados inválidos.")
            for row in reader:
                parcel_id = row["parcel_id"]
                if (not _valid_id(parcel_id) or parcel_id in rows
                        or parcel_id not in self.catalog_ids or None in row
                        or any(value is None for value in row.values())):
                    raise FeatureSchemaMismatch("Fila o ID incompatible con el catálogo.")
                # §7.3: metadata/columnas extra no se convierten en features.
                rows[parcel_id] = {feature: row[feature] for feature in features}
        return rows

    def preprocess(self, parcel_id):
        """Selecciona y ordena features; no ajusta imputación ni escalado."""
        self._require_loaded()
        if not _valid_id(parcel_id):
            raise FeatureSchemaMismatch("parcel_id debe ser una cadena no vacía.")
        if parcel_id not in self.catalog_ids:
            raise ParcelNotFound("La parcela no existe en el catálogo.")
        row = self._rows.get(parcel_id)
        if row is None:
            raise PredictionUnavailable("La parcela no tiene features disponibles.")
        values = []
        for feature in self._schema["features"]:
            raw = row[feature]
            try:
                # Solo el vacío y NaN numérico representan faltantes; no se
                # convierten textos arbitrarios a datos ausentes.
                value = float(raw) if raw.strip() else math.nan
            except (ValueError, TypeError) as exc:
                raise PredictionUnavailable("Feature no numérica.") from exc
            if math.isinf(value):
                raise PredictionUnavailable("Feature infinita.")
            if math.isnan(value) and self._schema["missing_value_policy"] == "reject":
                raise PredictionUnavailable("Feature faltante no permitida.")
            values.append(value)
        return [values]

    def predict(self, parcel_id):
        """Devuelve un float finito, sin redondeo, recorte ni mocks."""
        values = self.preprocess(parcel_id)
        try:
            if getattr(self._model, "feature_names_in_", None) is not None:
                # Los ColumnTransformer congelados pueden seleccionar por nombre.
                import pandas as pd
                values = pd.DataFrame(values, columns=self._schema["features"])
            output = self._model.predict(values)
            if (isinstance(output, (dict, str, bytes)) or len(output) != 1
                    or not isinstance(output[0], Real) or isinstance(output[0], bool)):
                raise ValueError("Salida incompatible.")
            prediction = float(output[0])
            if not math.isfinite(prediction):
                raise ValueError("Salida no finita.")
        except Exception as exc:
            raise PredictionUnavailable("El modelo no produjo una predicción utilizable.") from exc
        return prediction
