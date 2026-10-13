"""Predicciones base del modelo (Rol 2 → Rol 4/5). NO es el modelo final: sirve para integrar API/app ya.

Entrada : CEBADA_DATA (dataset de Rol 1)
Salida  : models/yield_model_v0.joblib        (solo el modelo, contrato §5)
          models/feature_schema.json          (features en orden contractual, unidad, versión, corte)
          results/predictions_raw.csv         (parcel_id, rendimiento_pred_t_ha, model_version) — 59 filas
Versión : yield-v0 / features-v0 / contrato 0.1.0

Las predicciones se calculan RECARGANDO los artefactos guardados (§6), de modo que lo que ve el backend
es exactamente lo que se escribió en el CSV.
"""
import json
import pandas as pd
import sklearn
from src import config as C
from src.data import load, families, columns_for
from src.models import zoo
from src import contract as K

tr, ev = load(); fam = families(tr)
cols = columns_for("E5_fusion", fam)          # sin geo ni mun_*: no se inventan features
K.validate_features(tr, cols)

# Corte temporal §1.7: el estado se registra en el schema; si CEBADA_STRICT_CUTOFF=1 se aborta.
try:
    audit = json.loads((C.RESULTS / "data_audit.json").read_text())
    cutoff_ok = bool(audit["cutoff_ok"])
except FileNotFoundError:
    cutoff_ok = None
if cutoff_ok is not True:
    msg = ("data_audit.json no existe: corre `python audit_data.py`" if cutoff_ok is None else
           "El dataset NO respeta el corte " + C.DATA_CUTOFF + " (ver results/data_audit.json)")
    print("⚠️  " + msg)
    if C.STRICT_CUTOFF:
        raise SystemExit("CEBADA_STRICT_CUTOFF=1: no se generan artefactos con datos no verificados al corte")

model = zoo()["ridge"](); model.fit(tr[cols].to_numpy(float), tr[C.TARGET].to_numpy(float))
schema = K.build_schema(cols, extra={
    "description": "Baseline Ridge sobre E5_fusion (sin geo). No es el modelo final.",
    "algorithm": "ridge", "experiment": "E5_fusion", "n_train": len(tr),
    "sklearn_version": sklearn.__version__,
    "data_cutoff_verified": cutoff_ok,         # True / False / None (sin auditar)
})
mp, sp = K.save_artifacts(model, schema)

model2, schema2 = K.load_artifacts()           # round-trip: se predice con lo guardado
pred = K.predict_frame(model2, schema2, ev)
out = pd.DataFrame({C.ID: pred.index, "rendimiento_pred_t_ha": pred.values.round(3), "model_version": schema2["model_version"]})
K.validate_predictions(out, ev[C.ID])
C.RESULTS.mkdir(exist_ok=True)
out.to_csv(C.RESULTS / "predictions_raw.csv", index=False)
print(f"modelo: {mp.name} | schema: {sp.name} | {len(cols)} features | data_cutoff_verified={cutoff_ok}")
print(out.rendimiento_pred_t_ha.describe())
