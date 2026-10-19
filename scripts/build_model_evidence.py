"""Ficha de validación para el frontend; no carga ni entrena el modelo."""
import argparse, ast, csv, hashlib, json, math, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def read(p):
    # Los metadatos históricos de ML fueron exportados por Windows en CP1252.
    raw = p.read_bytes()
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = raw.decode('cp1252')
    return json.loads(text)

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def rows(p):
    with p.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def indexed(p):
    r = rows(p)
    if any((not x['parcel_id'].strip() for x in r)) or len({x['parcel_id'] for x in r}) != len(r):
        raise ValueError('IDs vacíos/duplicados')
    return {x['parcel_id']: x for x in r}

def num(v):
    v = float(v)
    if not math.isfinite(v):
        raise ValueError('Número no finito')
    return v

def build(data_root):
    from ml.src.provenance import dataset_fingerprint
    schema_path = ROOT / 'ml/models/feature_schema.json'
    s = read(schema_path)
    c = read(ROOT / 'ml/results/final_model_config.json')
    meta = read(ROOT / 'ml/results/leaderboard_meta.json')
    labels = read(ROOT / 'api/app/catalogs/feature_labels.json')
    features = s['features']
    m = c['cv_metrics']
    if c['experiment'] != 'E4_clima' or c['spec']['model'] != 'ridge' or c['features'] != features or (c['model_version'] != s['model_version']) or (digest(ROOT / 'ml/models' / s['model_file']) != s['model_sha256']) or (labels['scope']['model_sha256'] != s['model_sha256']) or (labels['scope']['feature_schema_sha256'] != digest(schema_path)) or (set(labels['features']) != set(features)) or (meta['data_version'] != s['data_version']) or meta['fast'] or meta['provisional'] or (not meta['audit_valid_for_dataset']) or (dataset_fingerprint(data_root)['data_version'] != s['data_version']):
        raise ValueError('Modelo/schema/datos/evidencia incompatibles')
    constants = {}
    for node in ast.parse((ROOT / 'ml/src/config.py').read_text(encoding='utf-8-sig')).body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            constants.update({t.id: node.value.value for t in node.targets if isinstance(t, ast.Name)})
    if m['repeats'] != meta['repeats'] or m['repeats'] != constants['N_REPEATS']:
        raise ValueError('Protocolo incompatible')
    lb = [r for r in rows(ROOT / 'ml/results/leaderboard.csv') if r['exp'] == c['experiment'] and r['model'] == 'ridge']
    if len(lb) != 1 or any((not math.isclose(num(lb[0][k]), num(m[k]), abs_tol=1e-12, rel_tol=0) for k in ['rmse', 'mae', 'r2', 'rmse_spatial', 'r2_spatial'])):
        raise ValueError('Métricas incompatibles con leaderboard')
    master = indexed(data_root / 'parcel_master.csv')
    targets = indexed(data_root / 'targets/rendimiento.csv')
    train = {k for k, r in master.items() if r['dataset_split'] == 'ENTRENAMIENTO'}
    evaluation = {k for k, r in master.items() if r['dataset_split'] == 'PREDICCION'}
    oof = indexed(ROOT / 'ml/results/oof/E4_clima__ridge.csv')
    if set(oof) != train or any((targets[k]['rendimiento_t_ha'] for k in evaluation)):
        raise ValueError('OOF fuera de las parcelas etiquetadas')
    points = []
    for k, r in oof.items():
        y, p = (num(r['y']), num(r['oof']))
        if not math.isclose(y, num(targets[k]['rendimiento_t_ha']), abs_tol=1e-10, rel_tol=0):
            raise ValueError('Target OOF incompatible')
        points.append(dict(parcel_id=k, observed=y, predicted=p))
    shap_dir = ROOT / 'ml/results/rol3/shap_yield_v1'
    sm = read(shap_dir / 'shap_metadata_yield_v1.json')
    sh = indexed(shap_dir / 'shap_valores_yield_v1.csv')
    predictions = indexed(ROOT / 'ml/results/predictions_raw.csv')
    if any((sm[k] != s[k] for k in ['model_version', 'model_sha256', 'data_version'])) or sm['unit'] != 't/ha' or set(sh) != evaluation or (set(predictions) != evaluation):
        raise ValueError('SHAP incompatible')
    for k, r in sh.items():
        if not math.isclose(num(r['valor_base_shap_t_ha']) + math.fsum((num(r[f]) for f in features)), num(predictions[k]['rendimiento_pred_t_ha']), abs_tol=1e-08, rel_tol=0):
            raise ValueError('SHAP no reconstruye la predicción')
    importance = rows(shap_dir / 'shap_importancia_yield_v1.csv')
    records = []
    if len(importance) != len(features) or {r['variable'] for r in importance} != set(features):
        raise ValueError('Cobertura SHAP incompatible')
    for r in importance:
        f = r['variable']
        v = num(r['importancia_shap_media_t_ha'])
        expected = math.fsum((abs(num(x[f])) for x in sh.values())) / len(sh)
        if v < 0 or not math.isclose(v, expected, abs_tol=1e-10, rel_tol=0):
            raise ValueError('Importancia SHAP incompatible')
        records.append(dict(feature=f, **labels['features'][f], mean_abs_shap=v))
    records.sort(key=lambda r: (-r['mean_abs_shap'], r['feature']))
    source_paths = ['ml/models/feature_schema.json', 'ml/results/final_model_config.json', 'ml/results/leaderboard.csv', 'ml/results/leaderboard_meta.json', 'ml/results/oof/E4_clima__ridge.csv', 'ml/src/cv.py', 'ml/src/config.py', 'ml/src/data.py', 'api/app/catalogs/feature_labels.json'] + [f'ml/results/rol3/shap_yield_v1/{n}' for n in ['shap_metadata_yield_v1.json', 'shap_valores_yield_v1.csv', 'shap_importancia_yield_v1.csv']]
    reference = sorted(evaluation)[0]
    return dict(
        format_version='model-evidence-v1',
        modelo_oficial='Ridge · variables climáticas',
        model_version=s['model_version'],
        model_sha256=s['model_sha256'],
        data_version=s['data_version'],
        n_train=len(train),
        n_evaluation=len(evaluation),
        n_features=len(features),
        rmse=num(m['rmse']),
        mae=num(m['mae']),
        r2=num(m['r2']),
        cv_aleatoria=dict(rmse=m['rmse'], r2=m['r2'], folds=constants['N_SPLITS'], repeats=m['repeats'], seed=constants['SEED'], method=f"KFold con mezcla: {constants['N_SPLITS']} folds × {m['repeats']} repeticiones. Métricas medias por repetición."),
        cv_espacial=dict(rmse=m['rmse_spatial'], r2=m['r2_spatial'], method=f"GroupKFold: {constants['N_SPLITS']} folds sobre {constants['N_SPATIAL_GROUPS']} grupos KMeans de centroides. Diagnóstico de generalización geográfica; no reproduce el muestreo oficial."),
        oof=dict(points=points, method=f"Predicción fuera de fold por parcela, promediada entre las {m['repeats']} repeticiones.", note='Las tarjetas muestran métricas medias por repetición; no se recalculan desde estos puntos promediados.'),
        features=records,
        shap_population=len(sh),
        sources=[dict(name='Series climáticas del dataset del reto', path='clima/climate_timeseries.csv', window='2022–2024 y abril–octubre de 2025', transformation='Agregados de precipitación, temperaturas y amplitud térmica por P1.9.', note='El histórico es contexto ambiental; no implica cultivo de cebada en esos años.')],
        limitations=['Validación interna; no es la calificación sobre el conjunto oculto de FIRA.', 'El error espacial es mayor: la generalización geográfica es una limitación.', 'La selección usa esta evidencia de validación; no constituye una evaluación externa independiente.', 'Las variables correlacionadas pueden compartir importancia SHAP; sus efectos no son causales.', 'El modelo final usa clima; satélites y topografía se exploraron, pero no son entradas de yield-v1.'],
        reference_prediction=dict(parcel_id=reference, prediction=num(predictions[reference]['rendimiento_pred_t_ha']), unit=s['prediction_unit'], model_version=s['model_version']),
        meta=dict(mode='real', contract_version='0.1.0', cycle=s['target_cycle'], data_cutoff=s['prediction_information_cutoff']),
        provenance={p: digest(ROOT / p) for p in source_paths},
    )
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=ROOT / 'frontend/src/data/model/model-evidence.json')
    args = parser.parse_args()
    report = build(args.data_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(f"Ficha {report['model_version']}: {len(report['oof']['points'])} pares OOF y {report['n_features']} variables.")
