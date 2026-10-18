"""Genera el diccionario P4.13 del cálculo P1.9 auditado; no carga el modelo."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'scripts_limpieza/p1_9.py'
AUDITED_SOURCE_SHA256_LF = '263b89d2701d1b510df592ebb4546a3c207469f973707b1cd6dd27b8052aa10b'

# Traducciones internas del cálculo observado, no nombres oficiales atribuidos a FIRA.
MEASURES = {
    'precip_total_mm': ('Precipitación acumulada', 'mm', 'sum(precip_mm)',
                        'Suma de la precipitación mensual disponible; no es una media anual.'),
    'precip_mean_mm': ('Precipitación mensual media', 'mm', 'mean(precip_mm)',
                       'Promedio de la precipitación de los meses disponibles, con el mismo peso por mes.'),
    'tmin_mean_c': ('Temperatura mínima media', '°C', 'mean(tmin_c)',
                    'Promedio de los valores mensuales de temperatura mínima; no es la mínima absoluta del periodo.'),
    'tmax_mean_c': ('Temperatura máxima media', '°C', 'mean(tmax_c)',
                    'Promedio de los valores mensuales de temperatura máxima; no es la máxima absoluta del periodo.'),
    'amplitud_termica_mean_c': ('Amplitud térmica media', '°C', 'mean(tmax_c - tmin_c)',
                               'Promedio mensual de la diferencia entre temperatura máxima y mínima.'),
    'amplitud_termica_std_c': ('Variabilidad de amplitud térmica', '°C', 'std(tmax_c - tmin_c, ddof=1)',
                              'Desviación estándar muestral entre meses de la amplitud térmica; no es incertidumbre del modelo.'),
}
WINDOWS = {
    '2022': ('2022', '2022-01-01', '2022-12-31', 'Meses disponibles de 2022.', True),
    '2023': ('2023', '2023-01-01', '2023-12-31', 'Meses disponibles de 2023.', True),
    '2024': ('2024', '2024-01-01', '2024-12-31', 'Meses disponibles de 2024.', True),
    '2025': ('abr–oct 2025', '2025-04-01', '2025-10-31', 'Ciclo abril–octubre de 2025; excluye enero–marzo y noviembre–diciembre.', False),
    '2022_2025': ('histórico + ciclo 2025', '2022-01-01', '2025-10-31',
                  'Meses disponibles de 2022–2024 y abril–octubre de 2025. Excluye enero–marzo de 2025; no es una media de medias anuales.', True),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    source_hash_lf = hashlib.sha256((ROOT / SOURCE).read_text(encoding='utf-8-sig').encode('utf-8')).hexdigest()
    if source_hash_lf != AUDITED_SOURCE_SHA256_LF:
        raise ValueError('Cambió el cálculo P1.9: revisar las traducciones antes de regenerar.')
    schema_path = ROOT / 'ml/models/feature_schema.json'
    schema = json.loads(schema_path.read_text(encoding='utf-8'))
    data_dictionary_source = json.loads((ROOT / 'docs/persona1-data-dictionary-source.json').read_text(encoding='utf-8'))
    features = {}
    for window, (period, start, end, coverage, historical) in WINDOWS.items():
        for base, (name, unit, transformation, definition) in MEASURES.items():
            feature = f'{base}_{window}'
            features[feature] = {
                'friendly_name': f'{name} · {period}', 'definition': definition,
                'variable_unit': unit, 'transformation': transformation,
                'temporal_start': start, 'temporal_end': end, 'temporal_window': coverage,
                'uses_historical_information': historical,
                'historical_context': 'Contexto ambiental; no implica que hubiera cebada en esos años.' if historical else None,
            }
    if set(features) != set(schema['features']):
        raise ValueError('El schema ya no coincide con las 30 variables climáticas auditadas.')
    document = {
        'dictionary_version': 'feature-labels-v1', 'language': 'es-MX',
        'scope': {'model_version': schema['model_version'], 'feature_schema_version': schema['feature_schema_version'],
                  'model_sha256': schema['model_sha256'], 'feature_schema_sha256': digest(schema_path)},
        'source': {'path': SOURCE, 'function': 'calcular_features', 'sha256': digest(ROOT / SOURCE),
                   'sha256_lf': AUDITED_SOURCE_SHA256_LF,
                   'series': 'clima/climate_timeseries.csv'},
        'documentary_source': {'file': data_dictionary_source['source_file'],
                               'sha256': data_dictionary_source['sha256'],
                               'normalized_path': 'docs/persona1-data-dictionary-source.json',
                               'reconciliation': 'docs/data-dictionary-review-2026-10-18.md'},
        'review_status': 'Mapeo técnico verificado contra P1.9 y contrastado con el diccionario entregado por Persona 1; no implica aprobación explícita de estas etiquetas ni carácter oficial de FIRA.',
        'impact_unit_note': 'variable_unit describe la variable de entrada; las contribuciones SHAP de yield-v1 están en t/ha.',
        'features': {feature: features[feature] for feature in schema['features']},
    }
    destination = ROOT / 'api/app/catalogs/feature_labels.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(document, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    lines = ['# Diccionario de variables del modelo — P4.13', '',
             'Versión interna `feature-labels-v1`. Cubre las 30 features de `yield-v1` / `features-v1`.', '',
             'Los nombres se derivan del cálculo P1.9 auditado y se contrastaron con `DICCIONARIO_DE_DATOS.docx` entregado por Persona 1. Las 30 variables coinciden en significado, unidad y periodo. La entrega del documento no implica aprobación explícita de estas etiquetas ni nomenclatura oficial de FIRA. Véase [la comparación y complementos](data-dictionary-review-2026-10-18.md).', '',
             'El catálogo ejecutable está en `api/app/catalogs/feature_labels.json`. Incluye definiciones, unidades, fórmulas, ventanas y hashes del cálculo/modelo/schema. Se regenera con `python scripts/build_feature_dictionary.py`; si cambia el cálculo o el conjunto de features, se detiene para revisión.', '',
             'En 2025 se usa abril–octubre. La ventana conjunta incluye 2022–2024 y abril–octubre de 2025, sin enero–marzo de 2025. Los históricos representan contexto ambiental, no historial de cebada. La media conjunta pondera por observación mensual disponible, no por año.', '',
             '**Las unidades de entrada (mm o °C) no son las unidades del impacto SHAP:** las contribuciones de este predictor siguen expresadas en t/ha. No se cambian identificadores, impactos, orden, versiones ni la identidad de reconstrucción.', '',
             '| Feature técnica | Nombre para la interfaz | Unidad de entrada |', '|---|---|---|']
    lines += [f'| `{f}` | {item["friendly_name"]} | {item["variable_unit"]} |' for f, item in document['features'].items()]
    lines += ['', 'La API aplica los nombres únicamente al modelo y schema cuyos hashes figuran en el catálogo. Ante otro modelo, feature desconocida o diccionario no disponible, conserva el nombre técnico; no adivina una traducción. No añade campos al contrato público: utiliza `FeatureImpact.friendly_name`. El frontend conserva el código técnico en el título de cada etiqueta y en un detalle desplegable de la gráfica completa.', '']
    (ROOT / 'docs/model-feature-dictionary.md').write_text('\n'.join(lines), encoding='utf-8')
    return document


if __name__ == '__main__':
    print(f'Diccionario generado: {len(build()["features"])} variables; feature-labels-v1.')
