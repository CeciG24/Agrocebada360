"""Baseline de integración yield-v0 (Rol 2 -> Rol 4/5). NO es el modelo final: sirve para probar API/app mientras se congela yield-v1.

Entrada : CEBADA_DATA, split/official_ids_v1.json, results/data_audit.json sellada
Salida  : models/baseline_v0/yield_model_v0.joblib + feature_schema.json   (schema 0.3.0, verificable por hash)
          results/baseline_v0/predictions_raw.csv                          (parcel_id, rendimiento_pred_t_ha, model_version) — precisión completa
Versión : yield-v0 / features-v1 / contrato 0.3.0

Cambios frente a la versión 0.1.0 (audit-2026-10-14): schema 0.3.0, precisión completa (antes 3 decimales), exige auditoría válida
para este dataset, valida contra la lista oficial de IDs (no 59), y vive en carpetas propias para no pisar el modelo final (models/, results/).

Uso:  CEBADA_DATA=... python make_baseline_predictions.py   (--allow-unverified solo para pruebas)
"""
import argparse
import pandas as pd
import sklearn
from src import config as C
from src import contract as K
from src.data import load, families, columns_for
from src.models import zoo
from src.split import ids_sha256, load_official_ids

ap = argparse.ArgumentParser(); ap.add_argument("--allow-unverified", action="store_true"); a = ap.parse_args()
tr, ev = load(); fam = families(tr)
off = load_official_ids()
cols = columns_for("E5_fusion", fam)          # sin geo ni mun_*: no se inventan features
K.validate_features(tr, cols)
audit = K.require_valid_audit(allow_unverified=a.allow_unverified)

model = zoo()["ridge"](); model.fit(tr[cols], tr[C.TARGET].to_numpy(float))
schema = K.build_schema(cols, model_version=C.BASELINE_MODEL_VERSION, extra={
    "description": "Baseline Ridge sobre E5_fusion (sin geo). No es el modelo final.",
    "algorithm": "ridge", "experiment": "E5_fusion", "n_train": int(len(tr)),
    "train_ids_sha256": ids_sha256(list(tr[C.ID])), "sklearn_version": sklearn.__version__,
    "verified": bool(audit["valid"]),
})
mdir, rdir = C.MODELS / "baseline_v0", C.RESULTS / "baseline_v0"; rdir.mkdir(parents=True, exist_ok=True)
mp, sp = K.save_artifacts(model, schema, mdir)

model2, schema2 = K.load_artifacts(mdir)       # round-trip: se predice con lo guardado
pred = K.predict_frame(model2, schema2, ev)
out = pd.DataFrame({C.ID: pred.index.astype(str), C.PRED_COL: pred.values, "model_version": schema2["model_version"]})
K.validate_predictions(out, off["eval_ids"] if off else ev[C.ID])
out.to_csv(rdir / "predictions_raw.csv", index=False, float_format="%.17g")
print(f"baseline {schema2['model_version']}: {mp.name} | {len(cols)} features | verified={schema['verified']}")
print(out[C.PRED_COL].describe().round(4).to_string())
