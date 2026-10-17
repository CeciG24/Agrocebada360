"""P2.10 — Generar las predicciones de las parcelas de EVALUACIÓN con el modelo final (recargando el artefacto verificado).

Entrada : models/yield_model_v1.joblib + models/feature_schema.json (P2.9), CEBADA_DATA, split/official_ids_v1.json
Salida  : results/predictions_raw.csv     (parcel_id, rendimiento_pred_t_ha, model_version) a PRECISIÓN COMPLETA — insumo del exportador oficial
          results/predictions_4dp.csv     (mismo contenido redondeado a 4 decimales, t/ha — §1.1/§14)
          results/predictions_meta.json   (hashes de modelo/datos/IDs/archivos, estado de auditoría)
Versión : contrato 0.3.0

Los nombres y el orden de columnas del archivo OFICIAL de FIRA siguen PENDIENTES (§20): `rendimiento_pred_t_ha` es un nombre interno
y el exportador oficial (Rol 4, P4.16) debe aplicarlo con la especificación confirmada.

Uso:  CEBADA_DATA=... python generate_predictions.py
"""
import argparse, json
import pandas as pd
from src import config as C
from src import contract as K
from src import provenance as PV
from src.data import load
from src.split import ids_sha256, load_official_ids

ap = argparse.ArgumentParser()
ap.add_argument("--models-dir", default=None)
ap.add_argument("--out-dir", default=None)
ap.add_argument("--allow-unverified", action="store_true")
a = ap.parse_args()

model, schema = K.load_artifacts(a.models_dir)                       # verifica sha256, versión, nº y orden de features
_, ev = load(); off = load_official_ids()
if off is None:
    raise SystemExit("Falta split/official_ids_v1.json")
audit = K.require_valid_audit(allow_unverified=a.allow_unverified)
dv = PV.data_version()
if schema["data_version"] != dv:
    raise K.ArtifactMismatch(f"el modelo se entrenó con {schema['data_version']} y los datos actuales son {dv}: reentrena (train_final_model.py)")
if set(ev[C.ID]) != set(off["eval_ids"]):
    raise K.ContractError("las parcelas de evaluación no coinciden con la lista oficial")

pred = K.predict_frame(model, schema, ev)
raw = pd.DataFrame({C.ID: pred.index.astype(str), C.PRED_COL: pred.values, "model_version": schema["model_version"]})
K.validate_predictions(raw, off["eval_ids"])
p4 = raw.copy(); p4[C.PRED_COL] = p4[C.PRED_COL].round(C.SUBMISSION_DECIMALS)
K.validate_predictions(p4, off["eval_ids"], decimals=C.SUBMISSION_DECIMALS)

out = C.RESULTS if a.out_dir is None else __import__("pathlib").Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
raw.to_csv(out / "predictions_raw.csv", index=False, float_format="%.17g")
p4.to_csv(out / "predictions_4dp.csv", index=False, float_format=f"%.{C.SUBMISSION_DECIMALS}f")
meta = {"model_version": schema["model_version"], "model_file": schema["model_file"], "model_sha256": schema["model_sha256"],
        "data_version": dv, "contract_version": C.CONTRACT_VERSION, "n_predictions": int(len(raw)),
        "eval_ids_sha256": ids_sha256(list(raw[C.ID])), "official_eval_ids_sha256": off["eval_ids_sha256"],
        "decimals_submission": C.SUBMISSION_DECIMALS, "unit": C.UNIT, "verified": bool(audit["valid"]),
        "files": {n: PV.sha256_file(out / n) for n in ("predictions_raw.csv", "predictions_4dp.csv")},
        "range_t_ha": [float(raw[C.PRED_COL].min()), float(raw[C.PRED_COL].max())],
        "note": "columnas/nombre/orden del CSV oficial: PENDIENTES (contrato §20); este archivo es insumo del exportador.",
        "provenance": PV.run_meta()}
(out / "predictions_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"{len(raw)} predicciones ({schema['model_version']}, {C.UNIT}) -> {out / 'predictions_raw.csv'} y predictions_4dp.csv")
print(raw[C.PRED_COL].describe().round(4).to_string())
