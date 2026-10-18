"""Catálogo real y pipeline congelado; ninguna consulta entrena o recarga archivos."""
import csv
import logging
import math
from pathlib import Path

from api.app.core.errors import ServiceError
from api.app.schemas.common import Meta
from api.app.schemas.parcels import ParcelDetail, ParcelList, ParcelMapItem, ParcelMapList, ParcelSummary
from api.app.schemas.prediction import Prediction
from api.app.schemas.explanation import Explanation, RECONSTRUCTION_ATOL, unavailable_explanation
from api.app.schemas.risk import unavailable_risk

logger = logging.getLogger(__name__)


class RealService:
    def __init__(self, data_root: Path, delivery_path: Path):
        self.data_root = Path(data_root)
        self.delivery_path = Path(delivery_path)
        self.parcels: dict[str, ParcelMapItem] = {}
        self.data_ready = False
        self._pipeline = None
        self._explanations = {}
        self._explanation_failed = False
        self._feature_labels = {}
        self._risks = {}
        self._risk_failed = False

    def _load_explanations(self, manifest):
        from ml.model_bundle import read_json
        from ml.artifact_contract import sha256
        expected_hash = manifest['files_sha256'].get('explanations.json')
        if expected_hash is None:
            return  # Entrega sin módulo SHAP: ausencia esperada, no error operativo.
        path = self.delivery_path / 'explanations.json'
        if sha256(path) != expected_hash:
            raise ValueError('Las explicaciones no corresponden a la entrega integrada.')
        rows = read_json(path)
        if not isinstance(rows, dict) or set(rows) - set(self.parcels):
            raise ValueError('IDs de explicación incompatibles con el catálogo.')
        validated = {}
        for parcel_id, payload in rows.items():
            explanation = Explanation.model_validate(payload)
            if explanation.parcel_id != parcel_id or explanation.meta != Meta(mode='real'):
                raise ValueError('Contexto de explicación incompatible con la fuente real.')
            if explanation.status == 'available':
                if (explanation.model_version != self._pipeline.model_version
                        or explanation.output_space != self._pipeline.unit
                        or set(f.feature for f in explanation.features) != set(self._pipeline.feature_names)
                        or not math.isclose(explanation.explained_output, self._pipeline.predict(parcel_id),
                                            rel_tol=0, abs_tol=RECONSTRUCTION_ATOL)):
                    raise ValueError('La explicación no corresponde a las features/salida del modelo cargado.')
                # La capa semántica se aplica después de verificar la explicación original.
                for impact in explanation.features:
                    impact.friendly_name = self._feature_labels.get(impact.feature, impact.feature)
            validated[parcel_id] = explanation
        self._explanations = validated  # Publicación atómica: nada parcial si falla una fila.

    @property
    def model_loaded(self) -> bool:
        return self._pipeline is not None and self._pipeline.model_loaded

    def _load_catalog(self):
        # Imports ML solo en real; instalar la API mock no obliga a cargar sklearn.
        from ml.model_bundle import read_json
        from ml.artifact_contract import sha256
        from ml.data_handoff import verify_sources
        from ml.src.provenance import dataset_fingerprint

        manifest = read_json(self.delivery_path / 'integration_manifest.json')
        if (manifest.get('integration_format_version') != 'integration-v1'
                or manifest.get('contract_version') != '0.3.0'
                or manifest.get('data_version') != dataset_fingerprint(self.data_root)['data_version']):
            raise ValueError('Entrega incompatible con los datos o contrato.')
        for name in ['catalog.json', 'feature_provenance.json']:
            if sha256(self.delivery_path / name) != manifest['files_sha256'][name]:
                raise ValueError('El catálogo o su procedencia fueron alterados.')
        provenance = read_json(self.delivery_path / 'feature_provenance.json')
        if provenance['data_version'] != manifest['data_version']:
            raise ValueError('La procedencia pertenece a otra entrega.')
        verify_sources(self.data_root, provenance)
        with (self.data_root / 'parcel_master.csv').open(encoding='utf-8-sig', newline='') as stream:
            ids = [row['parcel_id'] for row in csv.DictReader(stream)]
        if any(not i.strip() for i in ids) or len(ids) != len(set(ids)):
            raise ValueError('IDs inválidos en el catálogo de origen.')
        catalog = read_json(self.delivery_path / 'catalog.json')
        if not isinstance(catalog, dict) or set(catalog) != set(ids):
            raise ValueError('Los IDs del catálogo no coinciden con Data.')
        parcels = {i: ParcelMapItem.model_validate(row) for i, row in catalog.items()}
        if any(key != parcel.id for key, parcel in parcels.items()) or not parcels:
            raise ValueError('Catálogo vacío o con IDs incompatibles.')
        # En este perfil no existe fuente autorizada de regiones. No inferir municipio.
        if any(parcel.region is not None for parcel in parcels.values()):
            raise ValueError('integration-v1 aún no declara fuente de regiones.')
        self.parcels, self.data_ready = parcels, True
        return manifest

    def load(self) -> None:
        if self.model_loaded:
            return
        try:
            manifest = self._load_catalog()
        except Exception:
            self.parcels, self.data_ready = {}, False
            logger.exception('No se pudo cargar el catálogo REAL validado')
            return
        try:
            from ml.inference import InferencePipeline
            from ml.model_bundle import inspect_bundle
            from ml.artifact_contract import sha256
            if (sha256(self.delivery_path / 'model/model_manifest.json')
                    != manifest['files_sha256']['model/model_manifest.json']):
                raise ValueError('El paquete del modelo no corresponde a la entrega integrada.')
            report = inspect_bundle(self.delivery_path / 'model')
            for field in ['contract_version', 'model_version', 'feature_schema_version', 'data_version']:
                if report[field] != manifest[field]:
                    raise ValueError('Modelo y entrega tienen versiones incompatibles.')
            pipeline = InferencePipeline.from_bundle(
                self.delivery_path / 'model', self.data_root / 'features/features_master.csv',
                self.delivery_path / 'feature_provenance.json', list(self.parcels))
            pipeline.load_model()
            if pipeline.unit != 't/ha':
                raise ValueError('Unidad real incompatible.')
            self._pipeline = pipeline
            from api.app.services.feature_labels import load_feature_labels
            self._feature_labels = load_feature_labels(
                sha256(self.delivery_path / 'model' / report['model_file']),
                sha256(self.delivery_path / 'model' / report['feature_schema_file']))
            logger.info('Servicio REAL listo: %d parcelas; modelo %s', len(self.parcels), pipeline.model_version)
            model_hash = sha256(self.delivery_path / 'model' / report['model_file'])
        except Exception:
            self._pipeline = None
            logger.exception('Catálogo REAL disponible, pero el modelo no pudo inicializarse')
        if self.model_loaded:
            try:
                self._load_explanations(manifest)
            except Exception:
                self._explanations, self._explanation_failed = {}, True
                logger.exception('El módulo de explicación REAL no pudo inicializarse')
            try:
                from api.app.services.risk_artifacts import load_risks
                self._risks = load_risks(self.delivery_path, manifest, self._pipeline, self.parcels, model_hash)
            except Exception:
                self._risks, self._risk_failed = {}, True
                logger.exception('El módulo de riesgo REAL no pudo inicializarse')

    def require_data(self):
        if not self.data_ready:
            raise ServiceError(503, 'DATA_UNAVAILABLE', 'El catálogo no está disponible.')

    def list_parcels(self, region, include_geometry):
        self.require_data()
        items = [p for p in sorted(self.parcels.values(), key=lambda p: p.id)
                 if region is None or p.region == region]
        if include_geometry:
            return ParcelMapList(items=items, total=len(items), meta=Meta(mode='real'))
        return ParcelList(items=[ParcelSummary(id=p.id, region=p.region) for p in items],
                          total=len(items), meta=Meta(mode='real'))

    def get_parcel(self, parcel_id):
        self.require_data()
        parcel = self.parcels.get(parcel_id)
        if parcel is None:
            raise ServiceError(404, 'PARCEL_NOT_FOUND', 'No se encontró la parcela solicitada.')
        return ParcelDetail(**parcel.model_dump(), meta=Meta(mode='real'))

    def get_prediction(self, parcel_id):
        self.get_parcel(parcel_id)
        if not self.model_loaded:
            raise ServiceError(503, 'MODEL_UNAVAILABLE', 'El modelo no está disponible.')
        from ml.inference import PredictionUnavailable, ModelNotLoaded, FeatureSchemaMismatch
        try:
            value = self._pipeline.predict(parcel_id)
            return Prediction(parcel_id=parcel_id, prediction=value, unit=self._pipeline.unit,
                              lower=None, upper=None, interval_level=None, interval_method=None,
                              model_version=self._pipeline.model_version, meta=Meta(mode='real'))
        except (PredictionUnavailable, FeatureSchemaMismatch):
            logger.exception('Predicción REAL no disponible')
            raise ServiceError(503, 'PREDICTION_UNAVAILABLE', 'La predicción no está disponible.') from None
        except ModelNotLoaded:
            logger.exception('El modelo REAL no está cargado')
            raise ServiceError(503, 'MODEL_UNAVAILABLE', 'El modelo no está disponible.') from None

    def get_explanation(self, parcel_id):
        self.get_parcel(parcel_id)
        if not self.model_loaded or self._explanation_failed:
            raise ServiceError(503, 'EXPLANATION_UNAVAILABLE', 'La explicación no está disponible.')
        return self._explanations.get(parcel_id) or unavailable_explanation(parcel_id, 'real')

    def get_risk(self, parcel_id):
        self.get_parcel(parcel_id)
        if not self.model_loaded or self._risk_failed:
            raise ServiceError(503, 'RISK_UNAVAILABLE', 'La evaluación de riesgo no está disponible.')
        return self._risks.get(parcel_id) or unavailable_risk(parcel_id, 'real')
