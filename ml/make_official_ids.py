"""Genera split/official_ids_v1.json (listas versionadas de IDs de entrenamiento y evaluación).

Entrada : CEBADA_DATA (dataset de Data, columna dataset_split)
Salida  : split/official_ids_v1.json
Versión : official-ids-v1 (contrato 0.3.0 §2.6, §14)

NO sustituye la lista oficial de FIRA (contrato §20, PENDIENTE): documenta la asignación del dataset entregado, con
hash, para que el código valide contra una lista y no contra constantes 138/59. No sobrescribe sin --force.
"""
import argparse, json, sys
import pandas as pd
from src import config as C
from src.provenance import dataset_fingerprint
from src.split import build_official_ids, load_official_ids, diff_split

ap = argparse.ArgumentParser(); ap.add_argument("--force", action="store_true"); a = ap.parse_args()
fm = pd.read_csv(C.DATA_ROOT / "features" / "features_master.csv", dtype={C.ID: str})
fp = dataset_fingerprint()
new = build_official_ids(fm, source="features_master.csv: dataset_split (contrastada con el maestro original en audit-2026-10-14)",
                         data_version=fp["data_version"])
if C.OFFICIAL_IDS_FILE.exists() and not a.force:
    cur = load_official_ids()
    d = diff_split(fm, cur)
    print("Ya existe", C.OFFICIAL_IDS_FILE, "->", "coincide con el dataset actual." if not d else f"DIFIERE del dataset actual: {d}")
    sys.exit(0 if not d else 1)
C.SPLIT_DIR.mkdir(parents=True, exist_ok=True)
C.OFFICIAL_IDS_FILE.write_text(json.dumps(new, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Escrito {C.OFFICIAL_IDS_FILE}: train={new['observed_counts']['train']} eval={new['observed_counts']['eval']} (observados)")
