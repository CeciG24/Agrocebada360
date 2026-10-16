"""P2.9 — Reentrenar el modelo final con TODAS las parcelas etiquetadas oficiales y publicar artefacto + schema.

Entrada : results/final_model_config.json (P2.8), CEBADA_DATA, split/official_ids_v1.json, results/data_audit.json sellada
Salida  : models/yield_model_v1.joblib          (solo el modelo, contrato §7)
          models/feature_schema.json            (schema 0.3.0 con sha256 del joblib, nº y orden de features, versiones, entorno)
          results/final_training_report.json    (qué se entrenó, con qué IDs/datos, verificación de recarga)
Versión : yield-v1 / features-v1 / contrato 0.3.0

Reglas:
  * entrena con todos los IDs ETIQUETADOS de la lista oficial (no con "138": el conteo es una observación);
  * las parcelas de evaluación NO participan (no tienen target);
  * exportar exige auditoría válida PARA ESTE dataset (hash): `audit_data.py` + `stamp_audit.py`. Solo para pruebas exploratorias:
    --allow-unverified (el schema queda con verified=false);
  * se entrena con un DataFrame para que sklearn verifique nombres/orden de features al predecir (23 vs 32 columnas ya no pasa en silencio).

Uso:  CEBADA_DATA=... python train_final_model.py
"""
import argparse, json
import numpy as np
from src import config as C
from src import contract as K
from src import provenance as PV
from src.data import load
from src.final import build_from_spec, describe, load_config
from src.split import ids_sha256, load_official_ids

ap = argparse.ArgumentParser()
ap.add_argument("--config", default=None)
ap.add_argument("--fast", action="store_true", help="solo pruebas: menos árboles (NO usar para la entrega)")
ap.add_argument("--allow-unverified", action="store_true")
ap.add_argument("--models-dir", default=None)
a = ap.parse_args()

cfg = load_config(a.config and __import__("pathlib").Path(a.config))
tr, _ = load()                                   # valida contra la lista oficial; tr = TODAS las parcelas etiquetadas
off = load_official_ids()
if off is None:
    raise SystemExit("Falta split/official_ids_v1.json: corre `python make_official_ids.py`")
if set(tr[C.ID]) != set(off["train_ids"]):
    raise K.ContractError("las parcelas de entrenamiento no coinciden con la lista oficial")
audit = K.require_valid_audit(allow_unverified=a.allow_unverified)
cols = cfg["features"]; K.validate_features(tr, cols)
if cfg.get("provisional"):
    print("⚠️  final_model_config.json es PROVISIONAL:", cfg["provenance"]["audit_reason"])

model = build_from_spec(cfg["spec"], a.fast)
X, y = tr[cols], tr[C.TARGET].to_numpy(float)
model.fit(X, y)
in_sample = np.asarray(model.predict(X), float)

schema = K.build_schema(cols, model_version=C.MODEL_VERSION, extra={
    "description": f"Modelo final {describe(cfg['spec'])} sobre {cfg['experiment']}, entrenado con todas las parcelas etiquetadas oficiales.",
    "algorithm": describe(cfg["spec"]), "spec": cfg["spec"], "experiment": cfg["experiment"],
    "n_train": int(len(tr)), "train_ids_sha256": ids_sha256(list(tr[C.ID])),
    "official_ids_version": off["version"], "official_ids_status": off["status"],
    "cv_metrics": cfg["cv_metrics"], "primary_metric": cfg["primary_metric"],
    "verified": bool(audit["valid"]), "audit_data_version": audit.get("data_version"),
    "fast_mode": bool(a.fast),
})
mp, sp = K.save_artifacts(model, schema, a.models_dir)

# round-trip: lo que usará el backend es lo que se verificó aquí
m2, s2 = K.load_artifacts(a.models_dir)
p2 = K.predict_frame(m2, s2, tr).to_numpy()
max_diff = float(np.max(np.abs(p2 - in_sample)))
if max_diff > 1e-9:
    raise K.ArtifactMismatch(f"el modelo recargado no reproduce las predicciones (dif máx {max_diff:.2e})")
report = {"model_version": C.MODEL_VERSION, "spec_text": describe(cfg["spec"]), "experiment": cfg["experiment"], "n_features": len(cols),
          "n_train": int(len(tr)), "train_ids_sha256": schema["train_ids_sha256"], "model_file": mp.name,
          "model_sha256": s2["model_sha256"], "reload_max_abs_diff": max_diff,
          "in_sample_rmse_informativo": float(np.sqrt(np.mean((y - in_sample) ** 2))),
          "verified": schema["verified"], "provenance": PV.run_meta()}
(C.RESULTS / "final_training_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Modelo {describe(cfg['spec'])}: {mp.name} + {sp.name} | {len(cols)} features | n_train={len(tr)} | verified={schema['verified']}")
print(f"sha256={s2['model_sha256'][:16]}…  recarga OK (dif máx {max_diff:.1e}); RMSE en train (informativo, optimista) {report['in_sample_rmse_informativo']:.4f}")
