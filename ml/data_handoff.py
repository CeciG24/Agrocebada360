"""Procedencia comprobada del perfil climático P1.9 usado por yield-v1.

No certifica publicación de rasters ni convierte alias internos en nombres oficiales.
Verifica todas las features requeridas y todos los IDs, sin muestrear parcelas.
"""
from pathlib import Path
import json

import numpy as np
import pandas as pd

from ml.artifact_contract import sha256
from ml.src.provenance import dataset_fingerprint
from ml.src.contract import validate_catalog


class DataHandoffError(ValueError):
    pass


OPERATIONS = {
    'precip_total_mm': ('precip_mm', 'sum'),
    'precip_mean_mm': ('precip_mm', 'mean'),
    'tmin_mean_c': ('tmin_c', 'mean'),
    'tmax_mean_c': ('tmax_c', 'mean'),
    'amplitud_termica_mean_c': ('amplitud_termica_c', 'mean'),
    'amplitud_termica_std_c': ('amplitud_termica_c', 'std'),
}
WINDOWS = {
    '2022': ('2022-01-01', '2022-12-31'),
    '2023': ('2023-01-01', '2023-12-31'),
    '2024': ('2024-01-01', '2024-12-31'),
    '2025': ('2025-04-01', '2025-10-31'),
    '2022_2025': ('2022-01-01', '2025-10-31'),
}
INPUTS = ['features/features_master.csv', 'targets/rendimiento.csv', 'parcel_master.csv',
          'topografia/topography_master.csv', 'clima/climate_timeseries.csv']
OPTIONAL_INPUTS = ['geometria/parcels.geojson', 'geometria/geometry_metadata.json', 'data_compatibility.json']


def climate_provenance(root, schema):
    root = Path(root)
    validate_catalog(root)
    fingerprint = dataset_fingerprint(root)
    if fingerprint['data_version'] != schema['data_version']:
        raise DataHandoffError('La versión de datos no coincide con el modelo; no se reetiqueta.')
    fm = pd.read_csv(root / INPUTS[0], dtype={'parcel_id': str}).set_index('parcel_id')
    climate = pd.read_csv(root / 'clima/climate_timeseries.csv', dtype={'parcel_id': str})
    if climate.parcel_id.isna().any() or set(climate.parcel_id) != set(fm.index):
        raise DataHandoffError('IDs climáticos incompatibles con el catálogo.')
    climate['date'] = pd.to_datetime(climate.fecha_captura, errors='raise')
    if climate.date.isna().any() or climate.duplicated(['parcel_id', 'date']).any():
        raise DataHandoffError('Fechas climáticas faltantes o duplicadas por parcela.')
    climate['amplitud_termica_c'] = climate.tmax_c - climate.tmin_c
    if not np.isfinite(climate[['precip_mm', 'tmin_c', 'tmax_c']].to_numpy(float)).all():
        raise DataHandoffError('Fuentes climáticas no finitas; se requiere política explícita.')
    metadata = {}
    cutoff = pd.Timestamp(schema['prediction_information_cutoff'])
    permitted = ((climate.date.dt.year.isin([2022, 2023, 2024]))
                 | climate.date.between('2025-04-01', min(cutoff, pd.Timestamp('2025-10-31'))))
    for feature in schema['features']:
        candidates = [(prefix, window, col, operation)
                      for prefix, (col, operation) in OPERATIONS.items() for window in WINDOWS
                      if feature == f'{prefix}_{window}']
        if len(candidates) != 1:
            raise DataHandoffError(f'No hay transformación respaldada para {feature}.')
        _, window, column, operation = candidates[0]
        start, end = WINDOWS[window]
        rows = climate.loc[permitted & climate.date.between(start, min(pd.Timestamp(end), cutoff))]
        counts = rows.groupby('parcel_id').size().reindex(fm.index, fill_value=0)
        if (counts < (2 if operation == 'std' else 1)).any():
            raise DataHandoffError(f'Cobertura temporal insuficiente para {feature}.')
        calculated = rows.groupby('parcel_id')[column].agg(operation).reindex(fm.index)
        actual = pd.to_numeric(fm[feature], errors='raise').to_numpy(float)
        if not np.isfinite(actual).all() or not np.allclose(actual, calculated, atol=1e-9, rtol=1e-9):
            raise DataHandoffError(f'{feature} no reproduce la transformación temporal P1.9.')
        historical = window != '2025'
        metadata[feature] = {
            'source': 'clima/climate_timeseries.csv; extracción scripts_limpieza/p1_5.py',
            'sensor_or_dataset': 'CHIRPS para precipitación; Reto_AgroCebada_Temperatura_2022_2025 para temperatura',
            'temporal_window': f'{start}/{end}' + ('; excluye enero-marzo 2025' if window == '2022_2025' else ''),
            'transformation': f'{operation}({column}) por parcel_id; std usa ddof=1; amplitud=tmax_c-tmin_c',
            'missing_value_policy': 'Sin faltantes en la matriz comprobada; imputación aprendida dentro del modelo congelado si aplica.',
            'uses_historical_information': historical,
            'information_kind': 'temporal',
            'max_information_date': rows.date.max().date().isoformat(),
            'max_information_date_basis': 'Fecha de observación en serie mensual; no acredita fecha de publicación del raster.',
            'checked_rows': len(actual), 'comparison_atol': 1e-9, 'comparison_rtol': 1e-9,
        }
        if historical:
            metadata[feature]['historical_context'] = 'Contexto ambiental; no implica cultivo histórico de cebada.'
    code_root = Path(__file__).resolve().parents[1]
    return {
        'provenance_format_version': 'climate-handoff-v1',
        'data_version': fingerprint['data_version'],
        'features_file_sha256': sha256(root / INPUTS[0]),
        'source_files_sha256': {rel: sha256(root / rel) for rel in INPUTS + OPTIONAL_INPUTS if (root / rel).exists()},
        'transformation_code_sha256': {
            rel: sha256(code_root / rel) for rel in ['scripts_limpieza/p1_5.py', 'scripts_limpieza/p1_9.py', 'ml/data_handoff.py']},
        'features': metadata,
        'scope': 'Todas las features del schema y todos los IDs; valida agregados desde series ya extraídas, no disponibilidad de publicación ni extracción raster.',
    }


def verify_sources(root, provenance):
    """Evita reutilizar evidencia si cambian las fuentes aunque no cambie el maestro."""
    root = Path(root).resolve()
    hashes = provenance.get('source_files_sha256', {})
    if not set(INPUTS).issubset(hashes) or set(hashes) - set(INPUTS + OPTIONAL_INPUTS):
        raise DataHandoffError('Procedencia incompleta de las fuentes.')
    for rel, expected in hashes.items():
        path = (root / rel).resolve()
        if not path.is_relative_to(root) or sha256(path) != expected:
            raise DataHandoffError(f'Cambió la fuente auditada: {rel}.')


def write_provenance(root, schema_path, destination):
    schema = json.loads(Path(schema_path).read_text(encoding='utf-8'))
    result = climate_provenance(root, schema)
    Path(destination).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    return result
