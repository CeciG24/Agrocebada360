"""Adaptador reproducible del dataset de Data al layout canónico que espera ML.

Entrada : --src  ZIP o carpeta entregada por Rol 1 (p. ej. DATASET_RETO_AGRO_2026_LIMPIO_2.zip)
Salida  : --out  carpeta con layout canónico (por defecto <repo>/data/DATASET_RETO_AGRO_2026_LIMPIO) + data_manifest.json
Versión : layout-v1 (contrato 0.3.0 §3 principios 1-2, §17 reproducibilidad)

Por qué (audit-2026-10-14, "Incompatibilidad de rutas"): el ZIP no se podía conectar a ML solo con CEBADA_DATA. El contrato
permite formatos equivalentes acordados, pero exige un acuerdo y un adaptador REPRODUCIBLE. Este script:
  * busca cada archivo por nombre (ignora __MACOSX/.DS_Store), lo copia a su ruta canónica y registra el mapeo aplicado
  * no modifica el contenido de ningún CSV (copia byte a byte) y guarda sha256 de cada archivo
  * falla si falta un archivo requerido o si un nombre aparece duplicado en rutas distintas (no adivina)
Layout canónico (el que usan src/data.py, src/contract.py y audit_data.py):
  parcel_master.csv · features/features_master.csv · features/fenologia_features.csv · targets/rendimiento.csv
  topografia/topography_master.csv · clima/climate_timeseries.csv · sensores/{sentinel2,landsat,planet}_timeseries.csv
  prediccion_temprana/features/features_master_corte_<mes>.csv   (v1 usaba prediccion_temprana/matrices/)

Uso:  python prepare_data.py --src ../DATASET_RETO_AGRO_2026_LIMPIO_2.zip
      CEBADA_DATA=<out> python audit_data.py && python stamp_audit.py
"""
import argparse, json, shutil, sys, tempfile, zipfile
from datetime import datetime, timezone
from pathlib import Path

from src import config as C
from src.provenance import sha256_file

CANON = {   # nombre de archivo -> ruta canónica relativa
    "parcels.geojson": "geometria/parcels.geojson",
    "geometry_metadata.json": "geometria/geometry_metadata.json",
    "parcel_master.csv": "parcel_master.csv",
    "features_master.csv": "features/features_master.csv",
    "fenologia_features.csv": "features/fenologia_features.csv",
    "satellite_features.csv": "features/satellite_features.csv",
    "rendimiento.csv": "targets/rendimiento.csv",
    "topography_master.csv": "topografia/topography_master.csv",
    "climate_timeseries.csv": "clima/climate_timeseries.csv",
    "climate_features.csv": "clima/climate_features.csv",
    "climate_aggregates.csv": "clima/climate_aggregates.csv",
    "sentinel2_timeseries.csv": "sensores/sentinel2_timeseries.csv",
    "landsat_timeseries.csv": "sensores/landsat_timeseries.csv",
    "planet_timeseries.csv": "sensores/planet_timeseries.csv",
    "basico_temporal_normalizado.csv": "normalizado/basico_temporal_normalizado.csv",
    "pro_temporal_normalizado.csv": "normalizado/pro_temporal_normalizado.csv",
}
REQUIRED = ["parcel_master.csv", "features_master.csv", "fenologia_features.csv", "rendimiento.csv", "topography_master.csv",
            "climate_timeseries.csv", "sentinel2_timeseries.csv", "landsat_timeseries.csv", "planet_timeseries.csv"]
CUT_MONTHS = ("junio", "julio", "agosto", "septiembre", "octubre")


def canonical(path: Path, name: str):
    if name in CANON:
        return CANON[name]
    if name.startswith("features_master_corte_"):                  # matrices por corte (v1: matrices/, v2: features/)
        return f"prediccion_temprana/features/{name}"
    if "corte" in name:                                            # series filtradas por corte
        return f"prediccion_temprana/{name}"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True); ap.add_argument("--out", default=str(C.PROJECT_ROOT / "data" / "DATASET_RETO_AGRO_2026_LIMPIO"))
    ap.add_argument("--force", action="store_true", help="sobrescribir --out si existe")
    a = ap.parse_args()
    src, out = Path(a.src), Path(a.out)
    tmp = None
    manifest = {"layout_version": "layout-v1", "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "source": str(src), "mapping": [], "ignored": [], "id_target_alias_note":
                "mapeo observado (audit-2026-10-14): ID_POLIGONO -> parcel_id; RENDIMIENTO_T_HA -> rendimiento_t_ha. Nombres oficiales PENDIENTES (§20)."}
    if src.is_file() and src.suffix == ".zip":
        manifest["source_sha256"] = sha256_file(src); manifest["source_bytes"] = src.stat().st_size
        tmp = Path(tempfile.mkdtemp(prefix="cebada_zip_")); zipfile.ZipFile(src).extractall(tmp); base = tmp
    elif src.is_dir():
        base = src
    else:
        sys.exit(f"--src debe ser un .zip o una carpeta: {src}")
    found, dup = {}, {}
    for p in sorted(base.rglob("*")):
        if not p.is_file() or (p.suffix != ".csv" and p.name not in ("parcels.geojson", "geometry_metadata.json")):
            continue
        rel = p.relative_to(base)
        if any(part in ("__MACOSX", ".git") for part in rel.parts) or p.name.startswith("._"):
            manifest["ignored"].append(str(rel)); continue
        dst = canonical(rel, p.name)
        if dst is None:
            manifest["ignored"].append(str(rel)); continue
        if dst in found:
            dup.setdefault(dst, [str(found[dst].relative_to(base))]).append(str(rel))
        found[dst] = p
    if dup:
        sys.exit(f"Archivos duplicados con el mismo nombre en rutas distintas (no se adivina cuál usar): {dup}")
    missing = [n for n in REQUIRED if CANON[n] not in found]
    if missing:
        sys.exit(f"Faltan archivos requeridos en la entrega: {missing}")
    if out.exists():
        if not a.force:
            sys.exit(f"{out} ya existe: usa --force para regenerarlo")
        shutil.rmtree(out)
    for dst, p in sorted(found.items()):
        (out / dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, out / dst)
        manifest["mapping"].append({"from": str(p.relative_to(base)), "to": dst, "sha256": sha256_file(out / dst), "bytes": (out / dst).stat().st_size})
    cuts = [m for m in CUT_MONTHS if f"prediccion_temprana/features/features_master_corte_{m}.csv" not in found]
    manifest["early_cut_matrices_missing"] = cuts
    (out / "data_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"Layout canónico escrito en {out} ({len(found)} archivos). Matrices de corte faltantes: {cuts or 'ninguna'}")
    print(f"Siguiente: CEBADA_DATA={out} python audit_data.py && python stamp_audit.py")


if __name__ == "__main__":
    main()
