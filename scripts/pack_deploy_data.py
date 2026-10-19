"""Optional archive of the bundled deployment; Render's current blueprint uses Git directly."""
import argparse
import hashlib
import json
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DEPLOY_DIR = ROOT / 'data/deploy'
OUTPUT = ROOT / 'data/cebada-deploy.tar.gz'


def check_deploy():
    from ml.integration import IntegratedArtifacts
    manifest = json.loads((DEPLOY_DIR / 'data/data_manifest.json').read_text(encoding='utf-8'))
    for record in manifest['mapping']:
        path = (DEPLOY_DIR / 'data' / record['to']).resolve()
        if not path.is_relative_to((DEPLOY_DIR / 'data').resolve()):
            raise ValueError('Data manifest path outside the deployment.')
        if hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
            raise ValueError(f'Data checksum mismatch: {record["to"]}')
    for name in ['parcels.geojson', 'geometry_metadata.json']:
        if not (DEPLOY_DIR / 'data/geometria' / name).is_file():
            raise ValueError('Deployment requires verified geometry and its CRS metadata.')
    artifacts = IntegratedArtifacts(DEPLOY_DIR / 'data', DEPLOY_DIR / 'delivery')
    geometries = sum(row['geometry'] is not None for row in artifacts.catalog.values())
    if not geometries or geometries != len(artifacts.catalog):
        raise ValueError('Deployment map requires complete geometry coverage.')
    if not artifacts.risks or not artifacts.regions:
        raise ValueError('Deployment requires verified risk and regional modules.')
    return {'status': 'passed', 'n_parcels': len(artifacts.catalog), 'n_geometries': geometries,
            'n_risks': len(artifacts.risks), 'n_regions': len(artifacts.regions)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true', help='Validate without creating an archive.')
    args = parser.parse_args()
    report = check_deploy()
    if not args.check_only:
        if OUTPUT.exists():
            raise FileExistsError(f'Archive already exists: {OUTPUT}; choose explicitly whether to replace it.')
        with tarfile.open(OUTPUT, 'w:gz', compresslevel=6) as archive:
            archive.add(DEPLOY_DIR, arcname='deploy')
        report.update(output=str(OUTPUT), output_sha256=hashlib.sha256(OUTPUT.read_bytes()).hexdigest())
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
