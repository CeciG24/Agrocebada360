"""Contrato para Rol 4/5 (P2.10 preliminar): entrena un baseline v0 con las 138 parcelas y escribe
results/predictions_raw.csv con las 59 de evaluación. NO es el modelo final: sirve para integrar API/app ya.
Columnas: parcel_id, rendimiento_pred_t_ha, model_version"""
import joblib, pandas as pd
from src import config as C
from src.data import load, families, columns_for
from src.models import zoo

tr, ev = load(); fam = families(tr)
cols = columns_for("E5_fusion", fam)          # sin geo: mantiene la historia explicable
model = zoo()["ridge"](); model.fit(tr[cols].values, tr[C.TARGET].values)
C.ARTIFACTS.mkdir(exist_ok=True)
joblib.dump({"model": model, "features": cols, "version": "baseline_v0"}, C.ARTIFACTS / "baseline_v0.joblib")
out = pd.DataFrame({C.ID: ev[C.ID], "rendimiento_pred_t_ha": model.predict(ev[cols].values).round(3), "model_version": "baseline_v0"})
assert len(out) == 59 and out.rendimiento_pred_t_ha.notna().all() and out[C.ID].is_unique
out.to_csv(C.RESULTS / "predictions_raw.csv", index=False)
print(out.describe())
