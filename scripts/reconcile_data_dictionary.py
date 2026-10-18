"""Contrasta la transcripción de Persona 1 con un dataset; no modifica datos.

Uso: python scripts/reconcile_data_dictionary.py --data-root <dataset integrado>
El JSON fuente conserva las tablas del DOCX entregado y su SHA256.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/persona1-data-dictionary-source.json'


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, list(reader)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reconcile(data_root):
    source = json.loads(SOURCE.read_text(encoding='utf-8'))
    tables = source['tables']
    labels = json.loads((ROOT / 'api/app/catalogs/feature_labels.json').read_text(encoding='utf-8'))
    records = {}
    for name, friendly, description, kind, unit in tables[2][1:]:
        records[name] = dict(group='identificacion', friendly_name=friendly,
                             definition=description, type=kind, unit=unit,
                             calculation_source='scripts_limpieza/p1_1.py')
    stats = {'mean': 'Media', 'median': 'Mediana', 'max': 'Máximo',
             'min': 'Mínimo', 'std': 'Desviación estándar muestral (ddof=1)',
             'range': 'Rango (máximo menos mínimo)'}
    for table in tables[3:6]:
        for prefix, category, meaning, count in table[1:]:
            base = prefix.removesuffix('_*')
            assert int(count) == len(stats)
            for stat, description in stats.items():
                records[f'{base}_{stat}'] = dict(
                    group='satelitales', friendly_name=f'{description} de {base}',
                    definition=f'{description} de las observaciones disponibles de {base} dentro del ciclo.',
                    type='Decimal', unit='Unidad/escala del producto fuente; pendiente ficha del proveedor',
                    temporal_window='2025-04-01 a 2025-10-31',
                    source_category=category, source_interpretation=meaning,
                    interpretation_status='Descripción de Persona 1; fórmula, escala y unidad física no verificadas.',
                    calculation_source='scripts_limpieza/p1_7.py')
    for sensor in ['sentinel2', 'planet']:
        for suffix, friendly, description, kind, unit in tables[6][1:]:
            corrected_unit = {'_auc': 'NDVI × día', '_growth_rate': 'NDVI/día',
                              '_decay_rate': 'NDVI/día'}.get(suffix, unit)
            records[f'{sensor}_ndvi{suffix}'] = dict(
                group='fenologia', friendly_name=f'{friendly} ({sensor})',
                definition=description, type=kind, unit=corrected_unit,
                temporal_window='2025-04-01 a 2025-10-31',
                calculation_source='scripts_limpieza/p1_8.py')
            supplements = {
                '_peak': ('max(NDVI)', 'Máximo de los promedios por fecha; si hay empate se toma la primera fecha ordenada.'),
                '_peak_date': ('fecha de idxmax(NDVI)', 'Fecha ISO YYYY-MM-DD de la primera ocurrencia del máximo.'),
                '_peak_doy': ('dayofyear(fecha del pico)', 'Día del año de la fecha del máximo; en 2025 el rango calendario es 1–365.'),
                '_auc': ('trapezoid(NDVI, días desde primera fecha)', 'Integral trapezoidal entre fechas observadas; NaN con menos de dos fechas. No extrapola al ciclo completo.'),
                '_growth_rate': ('(NDVI_pico - NDVI_inicial) / días_hasta_pico', 'NaN si el pico es la primera observación o no hay intervalo positivo.'),
                '_decay_rate': ('(NDVI_final - NDVI_pico) / días_después_pico', 'Tasa firmada, normalmente negativa; NaN si no hay observaciones posteriores al pico.'),
                '_std_temporal': ('std(NDVI por fecha, ddof=1)', 'Desviación muestral; P1.8 devuelve 0.0 si solo hay una fecha válida.'),
            }
            formula, note = supplements[suffix]
            records[f'{sensor}_ndvi{suffix}'].update(transformation=formula, implementation_note=note)
    documented_climate = {
        f'{base}{suffix}'
        for base, *_ in tables[7][1:]
        for suffix, count, period in tables[8][1:]
    }
    if documented_climate != set(labels['features']):
        raise ValueError('Las variables climáticas documentadas difieren de P4.13.')
    for name, record in labels['features'].items():
        records[name] = dict(record, group='clima', type='Decimal',
                             unit=record['variable_unit'], calculation_source='scripts_limpieza/p1_9.py')
    for name, friendly, description, unit, origin in tables[9][1:]:
        records[name] = dict(group='topografia', friendly_name=friendly,
                             definition=description, type='Decimal', unit=unit,
                             source=origin, calculation_source='scripts_limpieza/p1_6.py')

    columns, rows = read_csv(data_root / 'features/features_master.csv')
    if len(columns) != len(set(columns)) or set(columns) != set(records):
        raise ValueError(f'Cobertura incompleta: sin definición={set(columns)-set(records)}, '
                         f'fuera del maestro={set(records)-set(columns)}')
    ids = [row['parcel_id'] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('parcel_id duplicado en el maestro.')
    schema = json.loads((ROOT / 'ml/models/feature_schema.json').read_text(encoding='utf-8'))
    if not set(schema['features']) <= set(columns):
        raise ValueError('Features del modelo ausentes del maestro.')
    for name in columns:
        records[name]['used_by_yield_v1'] = name in schema['features']
        records[name]['observed_missing_ids'] = [row['parcel_id'] for row in rows if row[name] == '']
    target_columns, targets = read_csv(data_root / 'targets/rendimiento.csv')
    if target_columns != ['parcel_id', 'rendimiento_t_ha']:
        raise ValueError('Schema del target distinto del auditado.')
    if len({row['parcel_id'] for row in targets}) != len(targets):
        raise ValueError('Targets duplicados.')
    by_id = {row['parcel_id']: row['rendimiento_t_ha'] for row in targets}
    if set(by_id) != set(ids):
        raise ValueError('IDs de targets y maestro no coinciden.')
    train = [row['parcel_id'] for row in rows if row['dataset_split'] == 'ENTRENAMIENTO']
    prediction = [row['parcel_id'] for row in rows if row['dataset_split'] == 'PREDICCION']
    if len(train) + len(prediction) != len(rows):
        raise ValueError('Partición no reconocida.')
    if any(not by_id[pid] for pid in train) or any(by_id[pid] for pid in prediction):
        raise ValueError('Target ausente en entrenamiento o conocido en predicción.')
    climate_columns, climate_rows = read_csv(data_root / 'clima/climate_timeseries.csv')
    assert 'fecha_captura' in climate_columns
    years = sorted({int(row['fecha_captura'][:4]) for row in climate_rows})
    name, friendly, description, unit, origin = tables[10][1]
    paths = ['features/features_master.csv', 'targets/rendimiento.csv', 'clima/climate_timeseries.csv']
    sources = ['scripts_limpieza/p1_1.py', 'scripts_limpieza/p1_6.py',
               'scripts_limpieza/p1_7.py', 'scripts_limpieza/p1_8.py', 'scripts_limpieza/p1_9.py',
               'docs/system-contract.md', 'ml/models/feature_schema.json']
    result = dict(
        dictionary_version='data-dictionary-v1',
        source_document={'file': source['source_file'], 'sha256': source['sha256'],
                         'status': source['provenance']},
        scope='Dataset integrado auditado; los nulos observados no son una política general de imputación.',
        evidence={'rows': len(rows), 'columns': len(columns),
                  'groups': dict(Counter(records[name]['group'] for name in columns)),
                  'model_features': len(schema['features']), 'train': len(train),
                  'prediction': len(prediction), 'climate_years_observed': years,
                  'dataset_sha256': {path: digest(data_root / path) for path in paths},
                  'repository_sha256': {path: digest(ROOT / path) for path in sources}},
        fields={name: records[name] for name in columns},
        target={'name': name, 'friendly_name': friendly, 'definition': description,
                'unit': unit, 'source': origin, 'included_in_features_master': False,
                'observed_known': len(train), 'observed_missing': len(prediction)})
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=ROOT / 'docs/data-dictionary.json')
    args = parser.parse_args()
    result = reconcile(args.data_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result['evidence'], ensure_ascii=False, indent=2))
