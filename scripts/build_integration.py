"""Construye y verifica una entrega integrada desde ambos ZIP, en una carpeta nueva."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml.align_data import align
from ml.integration import prepare_delivery
from scripts.verify_integrated_delivery import verify
from scripts_limpieza.unpack_dataset import unpack


def build(raw_zip, clean_reference, out):
    out = Path(out).resolve()
    if out.exists():
        raise FileExistsError('Usa una carpeta de salida nueva; no se borra ni sobrescribe una entrega.')
    out.mkdir(parents=True)
    env = {**os.environ, 'PYTHONIOENCODING': 'utf-8', 'CEBADA_PREP_WORKDIR': str(out / 'raw')}

    def run(name, *args):
        with (out / (name + '.log')).open('w', encoding='utf-8') as log:
            subprocess.run([sys.executable, *map(str, args)], cwd=ROOT, env=env,
                           stdout=log, stderr=subprocess.STDOUT, check=True)

    unpack(raw_zip, out / 'raw')
    run('data-rebuild', ROOT / 'scripts_limpieza/p1_15.py')
    run('reference-layout', ROOT / 'ml/prepare_data.py', '--src', Path(clean_reference).resolve(), '--out', out / 'reference')
    run('rebuilt-layout', ROOT / 'ml/prepare_data.py', '--src', out / 'raw/DATASET_RETO_AGRO_2026_LIMPIO', '--out', out / 'candidate')
    compatibility = align(out / 'candidate', out / 'reference', out / 'data')
    env.update({'CEBADA_DATA': str(out / 'data'), 'CEBADA_RESULTS': str(out / 'audit')})
    run('strict-audit', ROOT / 'ml/audit_data.py')
    run('stamp-audit', ROOT / 'ml/stamp_audit.py')
    manifest = prepare_delivery(out / 'data', out / 'delivery')
    acceptance = verify(out / 'data', out / 'delivery')
    report = {'status': 'passed', 'data_version': manifest['data_version'],
              'candidate_data_version': compatibility['candidate_data_version'],
              'equivalent_csv_tables': len(compatibility['tables_checked']), **acceptance}
    (out / 'acceptance.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-zip', required=True)
    parser.add_argument('--clean-reference', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.raw_zip, args.clean_reference, args.out), indent=2))
    except (OSError, ValueError, AssertionError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'Integración detenida: {exc}. Revisa los logs de la salida.\n')
