"""Extrae el ZIP oficial y sus cuatro paquetes internos sin adivinar rutas."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
from zipfile import ZipFile


def extract(archive, destination):
    destination = Path(destination).resolve()
    with ZipFile(archive) as z:
        names = z.namelist()
        for name in names:
            rel = PurePosixPath(name)
            if ('\\' in name or ':' in name or rel.is_absolute() or '..' in rel.parts
                    or not (destination / name).resolve().is_relative_to(destination)):
                raise ValueError(f'Ruta insegura en ZIP: {name}')
        for name in names:
            if '__MACOSX' not in PurePosixPath(name).parts and not PurePosixPath(name).name.startswith('.'):
                z.extract(name, destination)


def unpack(archive, workdir):
    workdir = Path(workdir)
    if workdir.exists():
        raise FileExistsError('Usa una carpeta de trabajo nueva; no se sobrescriben datos.')
    workdir.mkdir(parents=True)
    extract(archive, workdir)
    raw = workdir / 'DATASET_RETO_AGRO_2026'
    packages = {
        'Parcelas_Reto_AGC_CONJUNTO_70_30.zip': raw / 'Parcelas_Reto_AGC_CONJUNTO_70_30',
        'Reto_AgroCebada_CHIRPS_Precipitacion_2022_2025.zip': raw,
        'Reto_AgroCebada_Temperatura_2022_2025_RECORTADA_CHIRPS.zip': raw,
        'Reto_AgroCebada_Topografia_INEGI_CEM4.zip': raw,
    }
    for name, dest in packages.items():
        extract(raw / name, dest)
    manifest = {'source_zip_sha256': hashlib.sha256(Path(archive).read_bytes()).hexdigest(),
                'files': {p.relative_to(raw).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sorted(raw.rglob('*')) if p.is_file()}}
    (workdir / 'raw_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return raw


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zip', required=True)
    parser.add_argument('--workdir', required=True)
    args = parser.parse_args()
    print(unpack(args.zip, args.workdir))
