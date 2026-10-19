"""Generate or validate a submission without training or sending it."""
import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREDICTIONS_DEFAULT = ROOT / 'ml/results/predictions_raw.csv'
IDS_DEFAULT = ROOT / 'ml/split/official_ids_v1.json'
DECIMALS = 4


def evaluation_ids(path):
    ids = json.loads(Path(path).read_text(encoding='utf-8'))['eval_ids']
    if (not ids or any(not isinstance(i, str) or not i or i.strip() != i for i in ids)
            or len(set(ids)) != len(ids)):
        raise ValueError('eval_ids must be nonempty, unique, opaque strings.')
    return ids


def rows_by_id(path, ids, value_column, *, submission=False):
    with Path(path).open(encoding='utf-8-sig', newline='') as source:
        reader = csv.DictReader(source)
        fields = reader.fieldnames or []
        required = ['parcel_id', value_column]
        if (len(fields) != len(set(fields)) or not set(required).issubset(fields)
                or (submission and fields != required)):
            raise ValueError(f'Invalid CSV headers: expected {required}.')
        values = {}
        for row in reader:
            parcel_id, token = row['parcel_id'], row[value_column]
            if None in row or any(v is None for v in row.values()):
                raise ValueError('Malformed CSV row.')
            if parcel_id in values:
                raise ValueError(f'Duplicate parcel_id: {parcel_id}.')
            if submission and not re.fullmatch(r'-?\d+\.\d{4}', token):
                raise ValueError('Submission values must have exactly four decimals.')
            try:
                value = float(token)
            except (TypeError, ValueError) as exc:
                raise ValueError(f'Invalid prediction for {parcel_id}.') from exc
            if not math.isfinite(value):
                raise ValueError(f'Nonfinite prediction for {parcel_id}.')
            values[parcel_id] = value
    if set(values) != set(ids):
        raise ValueError('CSV IDs must match eval_ids exactly: no missing or extra IDs.')
    return values


def validate_submission(path, ids_path=IDS_DEFAULT, predictions_path=PREDICTIONS_DEFAULT):
    path = Path(path)
    ids = evaluation_ids(ids_path)
    values = rows_by_id(path, ids, 'rendimiento_t_ha', submission=True)
    predictions = rows_by_id(predictions_path, ids, 'rendimiento_pred_t_ha')
    if any(f'{values[i]:.4f}' != f'{predictions[i]:.4f}' for i in ids):
        raise ValueError('Submission differs from the rounded frozen predictions.')
    return {'status': 'ok', 'output': str(path), 'n_rows': len(ids), 'decimals': DECIMALS,
            'unit': 't/ha', 'ids_source': str(ids_path), 'predictions_source': str(predictions_path),
            'output_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'rendimiento_min': min(values.values()), 'rendimiento_max': max(values.values())}


def generate(predictions_path, ids_path, output_path):
    ids = evaluation_ids(ids_path)
    predictions = rows_by_id(predictions_path, ids, 'rendimiento_pred_t_ha')
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', encoding='utf-8', newline='') as output:
        writer = csv.writer(output)
        writer.writerow(['parcel_id', 'rendimiento_t_ha'])
        writer.writerows((i, f'{predictions[i]:.4f}') for i in ids)
    return validate_submission(output_path, ids_path, predictions_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--team', help='Team name used for the output filename.')
    parser.add_argument('--predictions', type=Path, default=PREDICTIONS_DEFAULT)
    parser.add_argument('--ids', type=Path, default=IDS_DEFAULT)
    parser.add_argument('--out-dir', type=Path, default=Path('.'))
    parser.add_argument('--validate-only', type=Path, metavar='CSV', help='Validate an existing CSV without writing.')
    args = parser.parse_args()
    try:
        if args.validate_only:
            summary = validate_submission(args.validate_only, args.ids, args.predictions)
        else:
            slug = (args.team or '').strip().replace(' ', '_').lower()
            if not re.fullmatch(r'[a-z0-9][a-z0-9_-]*', slug):
                parser.error('--team is required for generation; use letters, digits, underscores or hyphens.')
            summary = generate(args.predictions, args.ids, args.out_dir / f'{slug}_prediccion.csv')
    except (ValueError, KeyError, OSError, csv.Error) as exc:
        parser.exit(1, f'Error: {exc}\n')
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
