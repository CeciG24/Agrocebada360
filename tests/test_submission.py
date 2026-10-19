import csv
import json
from pathlib import Path

import pytest
from scripts.generate_submission import generate, validate_submission


def sources(tmp_path, ids=None, rows=None):
    ids = ids or ['001', 'AGC_003']
    split = tmp_path / 'ids.json'
    split.write_text(json.dumps({'eval_ids': ids}))
    raw = tmp_path / 'raw.csv'
    with raw.open('w', newline='') as out:
        writer = csv.writer(out)
        writer.writerow(['parcel_id', 'rendimiento_pred_t_ha'])
        writer.writerows(rows or [('AGC_003', '4.123456'), ('001', '2.654321')])
    return raw, split, tmp_path / 'submission.csv'


def test_round_trip_preserves_opaque_ids_and_split_order(tmp_path):
    raw, split, out = sources(tmp_path)
    assert generate(raw, split, out)['n_rows'] == 2
    assert out.read_text().splitlines() == ['parcel_id,rendimiento_t_ha', '001,2.6543', 'AGC_003,4.1235']
    assert validate_submission(out, split, raw)['status'] == 'ok'


@pytest.mark.parametrize('rows', [
    [('001', 2), ('001', 3), ('AGC_003', 4)],
    [('001', 2)], [('001', 2), ('AGC_003', 4), ('extra', 5)],
    [('001', 'NaN'), ('AGC_003', 4)], [('001', 'Inf'), ('AGC_003', 4)],
])
def test_rejects_invalid_source_before_writing(tmp_path, rows):
    raw, split, out = sources(tmp_path, rows=rows)
    with pytest.raises(ValueError):
        generate(raw, split, out)
    assert not out.exists()


@pytest.mark.parametrize('content', [
    'parcel_id,rendimiento_t_ha\n001,2.654\nAGC_003,4.1235\n',
    'parcel_id,rendimiento_t_ha\n001,9.6543\nAGC_003,4.1235\n',
    'parcel_id,rendimiento_t_ha,extra\n001,2.6543,x\nAGC_003,4.1235,x\n',
])
def test_rejects_invalid_submission(tmp_path, content):
    raw, split, out = sources(tmp_path)
    out.write_text(content)
    with pytest.raises(ValueError):
        validate_submission(out, split, raw)


def test_repository_submission_matches_frozen_predictions():
    root = Path(__file__).resolve().parents[1]
    assert validate_submission(root / 'submissions/la_amariza_prediccion.csv')['n_rows'] == 59
