"""Congela los bytes de entrada de ML tras demostrar equivalencia de una reconstrucción.

No cambia el modelo ni su schema. Rechaza cualquier cambio de IDs, texto o valores
fuera de tolerancia; registra hashes antes/después en data_compatibility.json.
"""
import argparse
import json
from pathlib import Path
import shutil

import pandas as pd

from ml.artifact_contract import sha256
from ml.src.provenance import FINGERPRINT_FILES, dataset_fingerprint


def align(candidate, reference, out):
    candidate, reference, out = Path(candidate), Path(reference), Path(out)
    if out.exists():
        raise FileExistsError('La salida debe ser una carpeta nueva.')
    tables = sorted(p.relative_to(reference) for p in reference.rglob('*.csv'))
    if set(tables) != {p.relative_to(candidate) for p in candidate.rglob('*.csv')}:
        raise ValueError('Las entregas no contienen las mismas tablas CSV.')
    checked = {}
    for rel in tables:
        old = pd.read_csv(reference / rel, dtype={'parcel_id': str, 'ID_POLIGONO': str})
        new = pd.read_csv(candidate / rel, dtype={'parcel_id': str, 'ID_POLIGONO': str})
        pd.testing.assert_frame_equal(old, new, check_dtype=False, check_exact=False, atol=1e-10, rtol=1e-10)
        checked[rel.as_posix()] = {'candidate_sha256': sha256(candidate / rel),
                                  'reference_sha256': sha256(reference / rel), 'shape': list(new.shape)}
    shutil.copytree(candidate, out)
    # Solo estos tres archivos definen data_version en el formato ya publicado por ML.
    for rel in FINGERPRINT_FILES.values():
        shutil.copyfile(reference / rel, out / rel)
    layout_manifest = out / 'data_manifest.json'
    if layout_manifest.exists():
        layout = json.loads(layout_manifest.read_text(encoding='utf-8'))
        for item in layout.get('mapping', []):
            item['sha256'] = sha256(out / item['to'])
            item['bytes'] = (out / item['to']).stat().st_size
        layout['byte_compatibility_report'] = 'data_compatibility.json'
        layout_manifest.write_text(json.dumps(layout, indent=2, ensure_ascii=False), encoding='utf-8')
    report = {
        'profile': 'byte-compatibility-v1', 'atol': 1e-10, 'rtol': 1e-10,
        'candidate_data_version': dataset_fingerprint(candidate)['data_version'],
        'reference_data_version': dataset_fingerprint(reference)['data_version'],
        'output_data_version': dataset_fingerprint(out)['data_version'],
        'preserved_reference_bytes': list(FINGERPRINT_FILES.values()), 'tables_checked': checked,
        'note': 'Equivalencia numérica y texto/IDs exactos; se congelan bytes del input publicado de ML, no se reetiquetan archivos diferentes.',
    }
    (out / 'data_compatibility.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--reference', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    print(json.dumps(align(args.candidate, args.reference, args.out), indent=2, ensure_ascii=False))
