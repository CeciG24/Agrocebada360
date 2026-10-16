"""P2.11 — Validación final del modelo y de las predicciones (checklist ejecutable).

Entrada : models/*, results/predictions_*.csv, results/predictions_meta.json, results/final_model_config.json, CEBADA_DATA
Salida  : results/final_validation.json  (cada comprobación: PASS / WARN / FAIL con detalle). Exit code 1 si hay algún FAIL.
Versión : validate-v1 (contrato 0.3.0)

Comprueba: schema 0.3.0 completo · artefacto verificable (sha256, nº y orden de features) · versiones coherentes entre schema, modelo,
predicciones y datos · auditoría válida para el dataset · IDs de entrenamiento/evaluación = lista oficial (hash) · features permitidas ·
predicciones finitas, únicas, cobertura exacta, 4 decimales y consistentes con la precisión completa · el artefacto REPRODUCE las
predicciones · métricas RMSE/MAE/R² presentes y finitas · rango plausible.

Uso:  CEBADA_DATA=... python validate_final.py            (--allow-unverified degrada el chequeo de auditoría a WARN)
"""
import argparse, json, sys
import numpy as np, pandas as pd
from src import config as C
from src import contract as K
from src import provenance as PV
from src.data import load
from src.final import CONFIG_FILE
from src.split import ids_sha256, load_official_ids

ap = argparse.ArgumentParser()
ap.add_argument("--models-dir", default=None)
ap.add_argument("--pred-dir", default=None)
ap.add_argument("--allow-unverified", action="store_true")
a = ap.parse_args()
pdir = C.RESULTS if a.pred_dir is None else __import__("pathlib").Path(a.pred_dir)

checks = []
def check(name, fn, warn_only=False):
    try:
        r = fn(); status, detail = ("PASS", r if isinstance(r, str) else "ok")
    except Exception as e:                                         # noqa: BLE001
        status, detail = ("WARN" if warn_only else "FAIL"), f"{type(e).__name__}: {e}"
    checks.append({"check": name, "status": status, "detail": detail}); print(f"[{status}] {name}: {detail}")

def need(cond, msg):
    if not cond: raise AssertionError(msg)

ctx = {}
def c_artifacts():
    ctx["model"], ctx["schema"] = K.load_artifacts(a.models_dir); return f"{ctx['schema']['model_file']} sha256 {ctx['schema']['model_sha256'][:12]}…"
check("artefacto cargable y verificado (sha256, nº y orden de features)", c_artifacts)
sch = ctx.get("schema")

def c_schema():
    K.validate_schema(sch)
    need(sch["contract_version"] == C.CONTRACT_VERSION, f"contract_version {sch['contract_version']} != {C.CONTRACT_VERSION}")
    need(sch["prediction_unit"] == C.UNIT, "unidad distinta de t/ha")
    need(sch["target_cycle"] == C.TARGET_CYCLE and sch["prediction_information_cutoff"] == C.DATA_CUTOFF, "ciclo/corte distintos")
    return f"{sch['n_features']} features, ciclo {sch['target_cycle']}, corte {sch['prediction_information_cutoff']}"
if sch: check("schema 0.3.0 completo y coherente", c_schema)

tr = ev = off = None
def c_data():
    global tr, ev, off
    tr, ev = load(); off = load_official_ids(); need(off is not None, "falta split/official_ids_v1.json")
    return f"train={len(tr)} eval={len(ev)} (observado) = lista oficial {off['version']}"
check("datos cargados y partición = lista oficial", c_data)

def c_dataversion():
    need(sch["data_version"] == PV.data_version(), f"schema {sch['data_version']} != datos actuales {PV.data_version()}")
    return sch["data_version"]
if sch: check("data_version del schema = dataset actual", c_dataversion)

def c_audit():
    st = PV.audit_state(); need(st["valid"], st["reason"]); return st["reason"]
check("auditoría temporal válida para este dataset", c_audit, warn_only=a.allow_unverified)

def c_train_ids():
    need(sch["train_ids_sha256"] == ids_sha256(off["train_ids"]), "el modelo no se entrenó con exactamente los IDs etiquetados oficiales")
    need(sch.get("verified") is True, "el schema marca verified=false (exportado con --allow-unverified)")
    return f"{sch['n_train']} IDs, hash coincide"
if sch: check("modelo entrenado con todos los IDs etiquetados oficiales (verified)", c_train_ids, warn_only=a.allow_unverified)

def c_notfast():
    need(not sch.get("fast_mode"), "el modelo se entrenó con --fast (menos árboles): reentrena sin --fast para la entrega")
    return "entrenamiento completo (no --fast)"
if sch: check("modelo entrenado con configuración completa (no --fast)", c_notfast, warn_only=a.allow_unverified)

def c_features():
    K.validate_features(ev, sch["features"]); K.validate_features(tr, sch["features"]); return "sin mun_*, sin §5.6, numéricas, finitas"
if sch and tr is not None: check("features permitidas (§5.6) y presentes", c_features)

raw = p4 = meta = None
def c_files():
    global raw, p4, meta
    raw = pd.read_csv(pdir / "predictions_raw.csv", dtype={C.ID: str}); p4 = pd.read_csv(pdir / "predictions_4dp.csv", dtype={C.ID: str})
    meta = PV.read_json_tolerant(pdir / "predictions_meta.json")
    for n, h in meta["files"].items(): need(PV.sha256_file(pdir / n) == h, f"{n}: el hash no coincide con predictions_meta.json (archivo alterado)")
    return "hashes de archivos coinciden"
check("archivos de predicciones presentes e íntegros", c_files)

def c_cover():
    K.validate_predictions(raw, off["eval_ids"]); K.validate_predictions(p4, off["eval_ids"], decimals=C.SUBMISSION_DECIMALS)
    return f"{len(raw)} IDs = lista oficial de evaluación, únicos, finitos"
if raw is not None and off is not None: check("cobertura exacta de IDs oficiales, finitud y 4 decimales", c_cover)

def c_consistent():
    m = raw.merge(p4, on=C.ID, suffixes=("_raw", "_4dp"), validate="1:1")
    d = np.abs(m[f"{C.PRED_COL}_raw"].round(C.SUBMISSION_DECIMALS) - m[f"{C.PRED_COL}_4dp"]).max()
    need(d < 1e-9, f"4dp no es el redondeo de la precisión completa (dif {d})"); need((raw.model_version == sch["model_version"]).all(), "model_version de las predicciones != schema")
    need(meta["model_sha256"] == sch["model_sha256"] and meta["data_version"] == sch["data_version"], "predictions_meta no corresponde a este modelo/datos")
    return "4dp = redondeo del raw; versiones y hashes coinciden"
if raw is not None and sch: check("predicciones consistentes con el schema (versión/hash/redondeo)", c_consistent)

def c_reproduce():
    p = K.predict_frame(ctx["model"], sch, ev).reindex(raw[C.ID]).to_numpy()
    d = float(np.max(np.abs(p - raw[C.PRED_COL].to_numpy()))); need(d < 1e-9, f"el artefacto no reproduce las predicciones (dif máx {d:.2e})")
    return f"reproducción exacta (dif máx {d:.1e})"
if raw is not None and sch and ev is not None: check("el artefacto reproduce las predicciones del CSV", c_reproduce)

def c_metrics():
    cfg = PV.read_json_tolerant(CONFIG_FILE); m = cfg["cv_metrics"]
    for k in ("rmse", "mae", "r2"): need(np.isfinite(m[k]), f"métrica {k} no finita")
    need(cfg["experiment"] == sch["experiment"] and cfg["spec"] == sch["spec"], "final_model_config.json no coincide con el modelo del schema")
    return f"CV RMSE {m['rmse']:.4f} MAE {m['mae']:.4f} R2 {m['r2']:.4f} (espacial {m['rmse_spatial']:.4f})"
if sch: check("métricas RMSE/MAE/R² registradas y configuración = modelo", c_metrics)

def c_range():
    y = tr[C.TARGET]; lo, hi = y.min() - 0.5 * y.std(), y.max() + 0.5 * y.std(); v = raw[C.PRED_COL]
    need(v.between(lo, hi).all(), f"predicciones fuera de [{lo:.2f}, {hi:.2f}] t/ha: {int((~v.between(lo, hi)).sum())}")
    return f"[{v.min():.3f}, {v.max():.3f}] dentro de [{lo:.2f}, {hi:.2f}] t/ha"
if raw is not None and tr is not None: check("rango plausible respecto al entrenamiento", c_range, warn_only=True)

fails = [c for c in checks if c["status"] == "FAIL"]; warns = [c for c in checks if c["status"] == "WARN"]
rep = {"validate_version": "validate-v1", "overall": "FAIL" if fails else ("PASS_WITH_WARNINGS" if warns else "PASS"),
       "n_pass": sum(c["status"] == "PASS" for c in checks), "n_warn": len(warns), "n_fail": len(fails), "checks": checks, "provenance": PV.run_meta()}
(C.RESULTS / "final_validation.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nRESULTADO: {rep['overall']} ({rep['n_pass']} PASS, {len(warns)} WARN, {len(fails)} FAIL)")
sys.exit(1 if fails else 0)
