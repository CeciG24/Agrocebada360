"""Adaptadores de entrega Data/ML/ML avanzado para P4.6/P4.7, sin activar HTTP.

python -m ml.integration --data-root <canónico> --out <carpeta nueva>
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ml.artifact_contract import sha256
from ml.data_handoff import climate_provenance, verify_sources, DataHandoffError
from ml.inference import InferencePipeline, ParcelNotFound
from ml.model_bundle import create_bundle, read_json, inspect_bundle
from ml.src.contract import validate_catalog
from ml.src.split import load_official_ids, diff_split

ROOT = Path(__file__).resolve().parents[1]
META = {'mode': 'real', 'contract_version': '0.1.0', 'cycle': '2025-04/2025-10', 'data_cutoff': '2025-10-31'}
TOLERANCE = 1e-8
DELIVERY_FILES = ['feature_provenance.json', 'explanations.json', 'intervals.json', 'catalog.json', 'model/model_manifest.json']
RISK_FILES = ['risks.json', 'risk_method.json']


def dump(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')


def _frame(path, ids):
    frame = pd.read_csv(path, dtype={'parcel_id': str})
    if (frame.parcel_id.isna().any() or frame.parcel_id.duplicated().any()
            or set(frame.parcel_id) != set(ids)):
        raise DataHandoffError(f'IDs incompatibles en {path.name}.')
    return frame.set_index('parcel_id').loc[list(ids)]


def _catalog(root, ids):
    catalog = {i: {'id': i, 'region': None, 'geometry': None} for i in ids}
    geo_path = root / 'geometria/parcels.geojson'
    metadata_path = root / 'geometria/geometry_metadata.json'
    if not geo_path.exists() and not metadata_path.exists():
        return catalog, 'unavailable; geometry=null'
    from shapely.geometry import shape
    from pydantic import TypeAdapter
    from api.app.schemas.parcels import Geometry
    metadata = read_json(metadata_path)
    if not metadata.get('source_crs') or metadata.get('api_crs') != 'EPSG:4326':
        raise DataHandoffError('Falta CRS verificado del adaptador geoespacial.')
    geo = read_json(geo_path)
    seen = set()
    for feature in geo['features']:
        parcel_id = feature['properties']['parcel_id']
        if parcel_id not in catalog or parcel_id in seen:
            raise DataHandoffError('IDs GeoJSON incompatibles con el catálogo.')
        geometry = TypeAdapter(Geometry).validate_python(feature['geometry']).model_dump(mode='json')
        polygon = shape(geometry)
        if not polygon.is_valid or polygon.is_empty:
            raise DataHandoffError('Geometría inválida; no se repara silenciosamente.')
        catalog[parcel_id]['geometry'] = geometry
        seen.add(parcel_id)
    if seen != set(ids):
        raise DataHandoffError('Cobertura de geometrías incompleta.')
    return catalog, f'available; {len(seen)} geometrías EPSG:4326; source_crs={metadata["source_crs"]}'


def _advanced(results, schema, predictions):
    """Carga solo artefactos yield-v1 y verifica cada contribución contra la salida congelada."""
    paths = {
        'shap': results / 'rol3/shap_yield_v1/shap_valores_yield_v1.csv',
        'shap_meta': results / 'rol3/shap_yield_v1/shap_metadata_yield_v1.json',
        'intervals': results / 'rol3/intervalos_yield_v1/predicciones_intervalos_yield_v1.csv',
        'intervals_meta': results / 'rol3/intervalos_yield_v1/metadata_intervalos_yield_v1.json',
        'risk': results / 'rol3/riesgo_yield_v1/predicciones_riesgo_yield_v1.csv',
        'risk_meta': results / 'rol3/riesgo_yield_v1/metadata_riesgo_yield_v1.json',
    }
    meta = read_json(paths['shap_meta'])
    if any(meta.get(k) != schema[k] for k in ['model_version', 'data_version', 'model_sha256']):
        raise DataHandoffError('SHAP pertenece a otra entrega de modelo/datos.')
    if meta.get('unit') != schema['prediction_unit'] or meta.get('method') != 'shap.LinearExplainer':
        raise DataHandoffError('Escala o método de explicación incompatible.')
    ids = list(predictions)
    sh = _frame(paths['shap'], ids)
    features = schema['features']
    values = sh[features].to_numpy(float)
    base = sh.valor_base_shap_t_ha.to_numpy(float)
    expected = np.array([predictions[i] for i in ids])
    if (not np.isfinite(values).all() or not np.isfinite(base).all()
            or not np.allclose(base + values.sum(axis=1), expected, atol=TOLERANCE, rtol=0)
            or not np.allclose(sh.prediccion_t_ha, expected, atol=TOLERANCE, rtol=0)
            or not np.allclose(sh.prediccion_reconstruida_t_ha, expected, atol=TOLERANCE, rtol=0)):
        raise DataHandoffError('SHAP no reconstruye las predicciones del modelo cargado.')
    explanations = {}
    for parcel_id, row in sh.iterrows():
        impacts = [{'feature': feature, 'friendly_name': feature, 'impact': float(row[feature]),
                    'direction': 'positive' if row[feature] > 0 else 'negative' if row[feature] < 0 else 'neutral'}
                   for feature in features]
        impacts.sort(key=lambda item: (-abs(item['impact']), item['feature']))
        explanations[parcel_id] = {
            'parcel_id': parcel_id, 'status': 'available', 'reason': None, 'method': 'shap',
            'model_version': schema['model_version'], 'output_space': schema['prediction_unit'],
            'base_value': float(row.valor_base_shap_t_ha), 'explained_output': predictions[parcel_id],
            'features': impacts, 'meta': META,
        }
    interval_meta = read_json(paths['intervals_meta'])
    if any(interval_meta.get(k) != schema[k] for k in ['model_version', 'data_version']):
        raise DataHandoffError('Intervalos pertenecen a otra entrega.')
    intervals = _frame(paths['intervals'], ids)
    numbers = intervals[['rendimiento_pred_t_ha', 'limite_inferior_t_ha', 'limite_superior_t_ha', 'margen_exploratorio_t_ha']].to_numpy(float)
    nominal = interval_meta['nominal_level']
    if (not np.isfinite(numbers).all() or not 0 < nominal < 1
            or not np.allclose(numbers[:, 0], expected, atol=TOLERANCE, rtol=0)
            or not intervals.model_version.eq(schema['model_version']).all()
            or not (numbers[:, 1] <= expected).all() or not (expected <= numbers[:, 2]).all()
            or not np.allclose(numbers[:, 0] - numbers[:, 1], numbers[:, 3], atol=TOLERANCE, rtol=0)
            or not np.allclose(numbers[:, 2] - numbers[:, 0], numbers[:, 3], atol=TOLERANCE, rtol=0)):
        raise DataHandoffError('Intervalos inconsistentes.')
    adapted = {parcel_id: {'lower': float(row.limite_inferior_t_ha), 'upper': float(row.limite_superior_t_ha),
                           'interval_level': nominal,
                           'interval_method': 'Cuantil de residuos OOF promediados; exploratorio, sin garantía de cobertura'}
               for parcel_id, row in intervals.iterrows()}
    return explanations, adapted, {
        'explanation_version': 'linear-shap-adapter-v1', 'reconstruction_atol': TOLERANCE,
        'interval_method_version': 'mean-oof-residual-adapter-v1',
        'risk': {'status': 'unavailable', 'reason': 'RISK_NOT_READY', 'method_version': None},
        'version_scope': 'Versiones del perfil interno de adaptación; no se atribuyen como versiones del productor.',
        'producer_files_sha256': {p.relative_to(results).as_posix(): sha256(p) for p in paths.values()},
    }


def prepare_delivery(data_root, out, *, models=None, results=None):
    root, out = Path(data_root).resolve(), Path(out)
    models, results = Path(models or ROOT / 'ml/models'), Path(results or ROOT / 'ml/results')
    if out.exists():
        raise FileExistsError('La carpeta de entrega ya existe; usa una nueva.')
    schema = read_json(models / 'feature_schema.json')
    provenance = climate_provenance(root, schema)
    catalog = pd.read_csv(root / 'parcel_master.csv', dtype={'parcel_id': str})
    split = load_official_ids()
    if split is None or diff_split(catalog, split):
        raise DataHandoffError('El split no coincide con las listas versionadas de ML.')
    target = pd.read_csv(root / 'targets/rendimiento.csv', dtype={'parcel_id': str}).set_index('parcel_id')
    if (not target.loc[split['train_ids'], 'rendimiento_t_ha'].notna().all()
            or not target.loc[split['eval_ids'], 'rendimiento_t_ha'].isna().all()):
        raise DataHandoffError('El target no respeta la separación train/eval.')
    # Se escribe evidencia verificada antes de deserializar el artefacto de confianza.
    out.mkdir(parents=True)
    dump(out / 'feature_provenance.json', provenance)
    create_bundle(models / schema['model_file'], models / 'feature_schema.json', out / 'model')
    pipeline = InferencePipeline.from_bundle(out / 'model', root / 'features/features_master.csv',
                                             out / 'feature_provenance.json', catalog.parcel_id.tolist())
    pipeline.load_model()
    predictions = {i: pipeline.predict(i) for i in split['eval_ids']}
    official = _frame(results / 'predictions_raw.csv', list(predictions))
    if (not official.model_version.eq(schema['model_version']).all()
            or not np.allclose(official.rendimiento_pred_t_ha, list(predictions.values()), atol=TOLERANCE, rtol=0)):
        raise DataHandoffError('Las predicciones publicadas no coinciden con el modelo cargado.')
    explanations, intervals, advanced = _advanced(results, schema, predictions)
    dump(out / 'explanations.json', explanations)
    dump(out / 'intervals.json', intervals)
    risk_files = []
    if (results / 'rol3/riesgo_yield_v1/predicciones_riesgo_yield_v1.csv').exists():
        from ml.risk_adapter import adapt_risk, METHOD_VERSION
        risks, risk_method = adapt_risk(results, schema, predictions)
        dump(out / 'risks.json', risks)
        dump(out / 'risk_method.json', risk_method)
        risk_files = RISK_FILES
        advanced['risk'] = {'status': 'available', 'reason': None, 'method_version': METHOD_VERSION,
                            'scope': risk_method['scope'], 'n_assessments': len(risks)}
    parcels, geometry_status = _catalog(root, catalog.parcel_id.tolist())
    dump(out / 'catalog.json', parcels)
    # La fuente no define regiones ni polígonos en el CSV. No se infiere municipio -> región.
    manifest = {
        'integration_format_version': 'integration-v1',
        'contract_version': schema['contract_version'], 'model_version': schema['model_version'],
        'feature_schema_version': schema['feature_schema_version'], 'data_version': schema['data_version'],
        'model_sha256': schema['model_sha256'], 'n_parcels': len(catalog), 'n_eval': len(predictions),
        'split_status': split['status'], 'split_sha256': sha256(ROOT / 'ml/split/official_ids_v1.json'),
        'files_sha256': {name: sha256(out / name) for name in DELIVERY_FILES + risk_files},
        'advanced': advanced, 'geometry': geometry_status, 'regions': 'unavailable; region=null',
        'intervals_enabled_by_default': False,
    }
    dump(out / 'integration_manifest.json', manifest)
    return manifest


class IntegratedArtifacts:
    """Adaptador invocable desde un servicio; una carga y ninguna operación de entrenamiento."""
    def __init__(self, data_root, delivery):
        root, delivery = Path(data_root), Path(delivery)
        manifest = read_json(delivery / 'integration_manifest.json')
        if manifest['integration_format_version'] != 'integration-v1':
            raise DataHandoffError('Formato de integración incompatible.')
        declared = set(manifest['files_sha256'])
        if declared not in [set(DELIVERY_FILES), set(DELIVERY_FILES + RISK_FILES)]:
            raise DataHandoffError('Manifiesto de integración incompleto.')
        for name, expected in manifest['files_sha256'].items():
            path = (delivery / name).resolve()
            if not path.is_relative_to(delivery.resolve()) or sha256(path) != expected:
                raise DataHandoffError('Artefacto de integración alterado.')
        provenance = read_json(delivery / 'feature_provenance.json')
        verify_sources(root, provenance)
        validate_catalog(root)
        report = inspect_bundle(delivery / 'model')
        for key in ['contract_version', 'model_version', 'feature_schema_version', 'data_version']:
            if manifest[key] != report[key] or provenance['data_version'] != report['data_version']:
                raise DataHandoffError('Versiones de integración incompatibles.')
        self.catalog = read_json(delivery / 'catalog.json')
        self.explanations = read_json(delivery / 'explanations.json')
        self.intervals = read_json(delivery / 'intervals.json')
        self.pipeline = InferencePipeline.from_bundle(delivery / 'model', root / 'features/features_master.csv',
                                                     delivery / 'feature_provenance.json', list(self.catalog))
        self.pipeline.load_model()
        if set(self.catalog) != set(pd.read_csv(root / 'parcel_master.csv', dtype={'parcel_id': str}).parcel_id):
            raise DataHandoffError('El catálogo empaquetado no coincide con Data.')
        from api.app.services.risk_artifacts import load_risks
        self.risks = load_risks(delivery, manifest, self.pipeline, self.catalog,
                                sha256(delivery / 'model' / report['model_file']))

    def _require_parcel(self, parcel_id):
        if parcel_id not in self.catalog:
            raise ParcelNotFound('La parcela no existe en el catálogo.')

    def predict(self, parcel_id, *, exploratory_intervals=False):
        self._require_parcel(parcel_id)
        fields = dict.fromkeys(['lower', 'upper', 'interval_level', 'interval_method'])
        if exploratory_intervals:
            fields.update(self.intervals.get(parcel_id, {}))
        return {'parcel_id': parcel_id, 'prediction': self.pipeline.predict(parcel_id),
                'unit': self.pipeline.unit, 'model_version': self.pipeline.model_version, **fields, 'meta': dict(META)}

    def explain(self, parcel_id):
        self._require_parcel(parcel_id)
        return self.explanations.get(parcel_id, {
            'parcel_id': parcel_id, 'status': 'unavailable', 'reason': 'EXPLANATION_NOT_READY',
            **dict.fromkeys(['method', 'model_version', 'output_space', 'base_value', 'explained_output']),
            'features': [], 'meta': dict(META)})

    def risk(self, parcel_id):
        self._require_parcel(parcel_id)
        from api.app.schemas.risk import unavailable_risk
        return (self.risks.get(parcel_id) or unavailable_risk(parcel_id, 'real')).model_dump(mode='json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    print(json.dumps(prepare_delivery(args.data_root, args.out), indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
