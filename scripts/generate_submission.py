"""Genera el CSV de entrega oficial para FIRA a partir de predictions_raw.csv.

Uso típico:
    python scripts/generate_submission.py --team agrocebada360

El script valida que las 59 predicciones sean finitas, correspondan exactamente
a los IDs del conjunto de evaluación y produce el archivo listo para enviar.

Ver docs/fira-submission-instructions.md para el proceso completo de entrega.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd

PREDICTIONS_DEFAULT = ROOT / 'ml' / 'results' / 'predictions_raw.csv'
IDS_DEFAULT = ROOT / 'ml' / 'split' / 'official_ids_v1.json'
DECIMALS = 4
EXPECTED_N = 59


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate(predictions_path: Path, ids_path: Path, output_path: Path) -> dict:
    # --- cargar fuentes ---
    ids_doc = json.loads(ids_path.read_text(encoding='utf-8'))
    eval_ids: list[str] = ids_doc['eval_ids']
    if len(eval_ids) != EXPECTED_N:
        raise ValueError(
            f'official_ids_v1.json tiene {len(eval_ids)} eval_ids; se esperan {EXPECTED_N}.'
        )

    raw = pd.read_csv(predictions_path)
    if 'parcel_id' not in raw.columns or 'rendimiento_pred_t_ha' not in raw.columns:
        raise ValueError(
            f'predictions_raw.csv debe tener columnas parcel_id y rendimiento_pred_t_ha. '
            f'Columnas encontradas: {list(raw.columns)}'
        )

    raw = raw.set_index('parcel_id')

    # --- validar cobertura de IDs ---
    missing = [i for i in eval_ids if i not in raw.index]
    if missing:
        raise ValueError(
            f'{len(missing)} IDs de evaluación no están en predictions_raw.csv: {missing[:5]}…'
        )

    extra = [i for i in raw.index if i not in eval_ids]
    if extra:
        # Solo advertencia: el archivo de origen puede incluir más parcelas
        print(f'Aviso: {len(extra)} parcelas en predictions_raw.csv no son del conjunto de '
              f'evaluación y serán excluidas del CSV de entrega.')

    # --- filtrar, renombrar y redondear ---
    sub = raw.loc[eval_ids, ['rendimiento_pred_t_ha']].copy()
    sub.index.name = 'parcel_id'
    sub = sub.rename(columns={'rendimiento_pred_t_ha': 'rendimiento_t_ha'})
    sub['rendimiento_t_ha'] = sub['rendimiento_t_ha'].round(DECIMALS)

    # --- validaciones finales ---
    errors = []

    nan_ids = sub.index[sub['rendimiento_t_ha'].isna()].tolist()
    if nan_ids:
        errors.append(f'NaN en {len(nan_ids)} predicciones: {nan_ids[:5]}')

    inf_ids = [i for i in sub.index if not math.isfinite(sub.loc[i, 'rendimiento_t_ha'])]
    if inf_ids:
        errors.append(f'Inf en {len(inf_ids)} predicciones: {inf_ids[:5]}')

    if sub.index.duplicated().any():
        errors.append('Hay IDs duplicados en el resultado.')

    if len(sub) != EXPECTED_N:
        errors.append(f'El CSV tiene {len(sub)} filas; se esperan {EXPECTED_N}.')

    if errors:
        raise ValueError('Validación fallida:\n' + '\n'.join(f'  - {e}' for e in errors))

    # --- escribir ---
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sub.to_csv(output_path, float_format=f'%.{DECIMALS}f')

    sha = _sha256(output_path)
    summary = {
        'status': 'ok',
        'output': str(output_path),
        'n_rows': len(sub),
        'decimals': DECIMALS,
        'unit': 't/ha',
        'rendimiento_min': float(sub['rendimiento_t_ha'].min()),
        'rendimiento_max': float(sub['rendimiento_t_ha'].max()),
        'rendimiento_mean': round(float(sub['rendimiento_t_ha'].mean()), DECIMALS),
        'ids_source': ids_doc.get('version', str(ids_path)),
        'predictions_source': str(predictions_path),
        'output_sha256': sha,
    }
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        '--team', required=True,
        help='Nombre del equipo (se usa en el nombre del archivo). '
             'Ejemplo: agrocebada360 → agrocebada360_prediccion.csv',
    )
    parser.add_argument(
        '--predictions', default=str(PREDICTIONS_DEFAULT),
        help=f'Ruta a predictions_raw.csv (default: {PREDICTIONS_DEFAULT})',
    )
    parser.add_argument(
        '--ids', default=str(IDS_DEFAULT),
        help=f'Ruta a official_ids_v1.json (default: {IDS_DEFAULT})',
    )
    parser.add_argument(
        '--out-dir', default='.',
        help='Directorio de salida (default: directorio actual)',
    )
    args = parser.parse_args()

    team_slug = args.team.strip().replace(' ', '_').lower()
    output_path = Path(args.out_dir) / f'{team_slug}_prediccion.csv'

    try:
        summary = generate(
            predictions_path=Path(args.predictions),
            ids_path=Path(args.ids),
            output_path=output_path,
        )
    except (ValueError, KeyError, FileNotFoundError) as exc:
        parser.exit(1, f'Error: {exc}\n')

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f'\nArchivo listo: {output_path}')
