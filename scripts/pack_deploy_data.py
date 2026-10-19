"""Empaqueta data/deploy/ en un tar.gz listo para subir al disco de Render.

Uso:
    python scripts/pack_deploy_data.py

Produce:
    data/cebada-deploy.tar.gz  (~50-70 MB comprimido)

Pasos siguientes:
    1. Sube data/cebada-deploy.tar.gz a GitHub Releases como asset de v1.0-agrocebada
       (o a cualquier servicio que dé una URL de descarga directa).
    2. Copia la URL de descarga directa del asset.
    3. En el shell de Render (dashboard → servicio → Shell), ejecuta:
           bash scripts/setup_render_disk.sh <URL>
"""
import hashlib
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEPLOY_DIR = ROOT / "data" / "deploy"
OUTPUT = ROOT / "data" / "cebada-deploy.tar.gz"
REQUIRED = ["data/features/features_master.csv", "data/targets/rendimiento.csv",
            "data/parcel_master.csv", "data/topografia/topography_master.csv",
            "data/clima/climate_timeseries.csv", "delivery/integration_manifest.json",
            "delivery/catalog.json", "delivery/explanations.json", "delivery/model"]


def main():
    if not DEPLOY_DIR.exists():
        sys.exit("No se encontró data/deploy/. Ejecuta primero prepare_data.py y prepare_delivery().")

    missing = [r for r in REQUIRED if not (DEPLOY_DIR / r).exists()]
    if missing:
        sys.exit(f"Faltan archivos en data/deploy/:\n  " + "\n  ".join(missing))

    if OUTPUT.exists():
        OUTPUT.unlink()
        print(f"Reemplazando {OUTPUT.name} existente.")

    print(f"Empaquetando data/deploy/ -> {OUTPUT} ...")
    with tarfile.open(OUTPUT, "w:gz", compresslevel=6) as tar:
        tar.add(DEPLOY_DIR, arcname="deploy")

    size_mb = OUTPUT.stat().st_size / 1_048_576
    sha = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()

    print(f"\nArchivo creado: {OUTPUT}")
    print(f"  Tamano  : {size_mb:.1f} MB")
    print(f"  SHA-256 : {sha}")
    print("\nSiguientes pasos")
    print("1. Sube data/cebada-deploy.tar.gz como asset en GitHub Releases:")
    print("     gh release upload v1.0-agrocebada data/cebada-deploy.tar.gz")
    print("   O subelo a Google Drive / Dropbox y obtén un link de descarga directa.")
    print("2. En el shell de Render (dashboard -> tu servicio -> pestana Shell):")
    print("     bash scripts/setup_render_disk.sh <URL-DE-DESCARGA>")
    print("3. Reinicia el servicio en Render para que cargue los datos.")


if __name__ == "__main__":
    main()
