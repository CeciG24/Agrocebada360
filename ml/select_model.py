"""P2.8 — Seleccionar el modelo definitivo y congelar su configuración.

Entrada : results/leaderboard.csv (P2.4), results/tuning/*.json (P2.5, opcional), results/ensemble/ensemble_config.json (P2.7, opcional)
Salida  : results/final_model_config.json  (modelo/params elegidos, RMSE/MAE/R² por CV, espacial, versiones, justificación)
Versión : select-v1 (contrato 0.3.0)

Regla (decisión técnica interna; FIRA solo menciona RMSE/MAE/R² "u otras"):
  1. Candidatos = experimentos OFICIALES (E1–E5). Los X* (municipio/ubicación) son diagnóstico y nunca se eligen solos.
  2. Mejor RMSE (CV repetida). Empate técnico = a menos de max(rmse_sd, 0.005) del mejor.
  3. Entre empatados: menor RMSE espacial; luego menos features.
  4. Hiperparámetros afinados SOLO si el RMSE de la CV ANIDADA (honesta) mejora al de defaults en >= 0.005 t/ha; si no, defaults.
  5. Ensemble SOLO si run_ensemble.py lo conservó con evaluación independiente (--params default) y es del mismo experimento.
  Se reporta la brecha contra el baseline de municipio (diagnóstico): si el modelo con satélite no lo supera, queda escrito.

Uso:
  CEBADA_DATA=... python select_model.py
  CEBADA_DATA=... python select_model.py --exp E5_fusion --model extratrees      # decisión del equipo (override)
"""
import argparse, json
import numpy as np, pandas as pd
from src import config as C
from src import provenance as PV
from src.cv import metrics, repeated_cv, spatial_cv
from src.data import load, families, columns_for
from src.final import CONFIG_FILE, describe
from src.tuning import build

ap = argparse.ArgumentParser()
ap.add_argument("--leaderboard", default="leaderboard.csv")
ap.add_argument("--exp", default=None, help="override: experimento")
ap.add_argument("--model", default=None, help="override: modelo")
ap.add_argument("--min-tuning-gain", type=float, default=0.005)
ap.add_argument("--tie", type=float, default=0.005, help="empate técnico mínimo en RMSE (t/ha)")
ap.add_argument("--repeats", type=int, default=None, help="repeticiones para recalcular métricas con params afinados (por defecto, las del leaderboard)")
a = ap.parse_args()

lb = pd.read_csv(C.RESULTS / a.leaderboard)
if "tipo" not in lb.columns:
    raise SystemExit(f"{a.leaderboard} no tiene columna `tipo`: reejecuta run_experiments.py (versión 0.3.0)")
off = lb[lb.tipo == "oficial"].copy()
if off.empty:
    raise SystemExit("No hay filas de experimentos oficiales en el leaderboard")
off = off.sort_values("rmse")
best = off.iloc[0]
thr = best.rmse + max(float(best.rmse_sd) if np.isfinite(best.rmse_sd) else 0.0, a.tie)
tied = off[off.rmse <= thr].sort_values(["rmse_spatial", "n_feat", "rmse"])
pick = tied.iloc[0]
if a.exp or a.model:
    sel = off[(off.exp == (a.exp or pick.exp)) & (off.model == (a.model or pick.model))]
    if sel.empty:
        raise SystemExit("El override no está en el leaderboard oficial")
    pick, reason = sel.iloc[0], "override explícito del equipo"
else:
    reason = (f"mejor RMSE oficial {best.exp}/{best.model} ({best.rmse:.4f}); empatados a <= {thr:.4f}: "
              f"{', '.join(tied.exp + '/' + tied.model)}; desempate por RMSE espacial y nº de features")
exp, model = pick.exp, pick.model

# --- hiperparámetros: solo si el anidado mejora de forma material ---
tj = C.RESULTS / "tuning" / f"{exp}__{model}.json"
params, params_note, tuning_ref = {}, "hiperparámetros por defecto (zoo)", None
if tj.exists():
    t = PV.read_json_tolerant(tj); n = t["nested"]
    gain = n["default"]["rmse"] - n["tuned"]["rmse"]
    tuning_ref = {"file": tj.name, "nested_rmse_default": n["default"]["rmse"], "nested_rmse_tuned": n["tuned"]["rmse"], "gain": gain}
    if gain >= a.min_tuning_gain and t["best_params"]:
        params, params_note = t["best_params"], f"afinados: la CV anidada mejora {gain:.4f} t/ha (>= {a.min_tuning_gain})"
    else:
        params_note = f"defaults: la mejora anidada del tuning es {gain:+.4f} t/ha (< {a.min_tuning_gain}) o el mejor candidato fue el default"
else:
    params_note += (f" (no hay results/tuning para {exp}/{model}: si quieres evaluar hiperparámetros afinados corre "
                    f"`python tune.py --exp {exp} --models {model}` y vuelve a ejecutar select_model.py)")

spec = {"type": "single", "model": model, "params": params}

# --- métricas del modelo elegido (CV repetida + espacial) ---
tr, _ = load(); cols = columns_for(exp, families(tr))
X = tr[cols].to_numpy(float); y = tr[C.TARGET].to_numpy(float); g = tr["grupo_espacial"].to_numpy()
reps = a.repeats or int(pick.repeats)
if params:
    rep, oof, _ = repeated_cv(lambda: build(model, params), X, y, n_repeats=reps)
    sp, _ = spatial_cv(lambda: build(model, params), X, y, g)
    cv = {"rmse": float(rep.rmse.mean()), "rmse_sd": float(rep.rmse.std(ddof=1)) if reps > 1 else None,
          "mae": float(rep.mae.mean()), "r2": float(rep.r2.mean()), "rmse_spatial": sp["rmse"], "r2_spatial": sp["r2"], "repeats": reps,
          "caveat": "los params se eligieron con todas las parcelas: este RMSE es optimista; la estimación honesta es la CV anidada de tuning"}
else:
    cv = {"rmse": float(pick.rmse), "rmse_sd": float(pick.rmse_sd) if np.isfinite(pick.rmse_sd) else None, "mae": float(pick.mae),
          "r2": float(pick.r2), "rmse_spatial": float(pick.rmse_spatial), "r2_spatial": float(pick.r2_spatial), "repeats": int(pick.repeats)}

# --- ensemble ---
ens_note, ens_ref = "no hay results/ensemble/ensemble_config.json", None
ef = C.RESULTS / "ensemble" / "ensemble_config.json"
if ef.exists():
    e = PV.read_json_tolerant(ef); d = e["decision"]
    ens_ref = {"exp": e["exp"], "members": e["members"], "keep": d["keep"], "variant": d["variant"], "gain": d["mean_gain_rmse"],
               "win_rate": d["win_rate"], "evaluation_independent": e.get("evaluation_independent"), "params_source": e.get("params_source")}
    if d["keep"] and e.get("evaluation_independent") and e["exp"] == exp:
        spec = {"type": "ensemble", "variant": d["variant"], "members": e["members"],
                "weights": e["final_choice"]["weights"], "member_params": e.get("member_params", {})}
        oo = pd.read_csv(C.RESULTS / "ensemble" / "ensemble_oof.csv")
        m = metrics(oo.y.to_numpy(), oo.oof.to_numpy())
        cv = {"rmse": float(e["rmse_cv_mean"][d["variant"] if d["variant"] == "mean" else "weighted_nested"]), "mae": m["mae"], "r2": m["r2"],
              "rmse_spatial": float(e["rmse_spatial"][d["variant"] if d["variant"] == "mean" else "weighted_nested"]),
              "repeats": int(d["n_repeats"]), "source": "run_ensemble.py (ponderación anidada, sin fuga)"}
        ens_note = "ensemble CONSERVADO por run_ensemble.py (mejora consistente e independiente)"
    elif d["keep"] and not e.get("evaluation_independent"):
        ens_note = "el ensemble se conservó pero con params afinados (no independiente): NO se usa; reejecutar con --params default"
    elif d["keep"]:
        ens_note = f"el ensemble es de {e['exp']} y el modelo elegido es de {exp}: NO se usa"
    else:
        ens_note = f"ensemble DESCARTADO (mejora {d['mean_gain_rmse']:+.4f} t/ha, gana en {d['win_rate']:.0%} de repeticiones): un modelo individual es válido"

# --- brecha contra el baseline de municipio (diagnóstico) ---
muni = lb[lb.exp == "X0_municipio"]
gap = None
if not muni.empty:
    mb = muni.sort_values("rmse").iloc[0]
    gap = {"muni_model": mb.model, "muni_rmse": float(mb.rmse), "selected_rmse": cv["rmse"], "delta": cv["rmse"] - float(mb.rmse),
           "muni_rmse_spatial": float(mb.rmse_spatial), "selected_rmse_spatial": cv["rmse_spatial"],
           "reading": ("el modelo con satélite/clima NO supera al promedio por municipio en CV aleatoria; documentar y decidir como equipo si "
                       "el municipio puede entrar al modelo oficial (el contrato no lo prohíbe pero el schema actual rechaza mun_*)")
           if cv["rmse"] > float(mb.rmse) else "el modelo oficial supera al baseline por municipio"}

meta = PV.run_meta(selected_from=a.leaderboard)
cfg = {"version": "select-v1", "model_version": C.MODEL_VERSION, "contract_version": C.CONTRACT_VERSION,
       "experiment": exp, "features": cols, "n_features": len(cols), "spec": spec, "spec_text": describe(spec),
       "selection_reason": reason, "hyperparameters": params_note, "tuning": tuning_ref, "ensemble": ens_note, "ensemble_ref": ens_ref,
       "cv_metrics": cv, "municipality_baseline_gap": gap,
       "top_candidates": off.head(8)[["exp", "model", "n_feat", "rmse", "rmse_sd", "mae", "r2", "rmse_spatial"]].round(4).to_dict("records"),
       "n_labeled": int(len(tr)), "primary_metric": C.PRIMARY_METRIC,
       "caveats": ["La métrica principal (RMSE) es decisión técnica interna.",
                   "Los candidatos se compararon sobre las mismas parcelas con las que se elige: hay optimismo de selección.",
                   "CV espacial = diagnóstico (KMeans sobre centroides), no reproduce el muestreo oficial."],
       "provenance": meta, "provisional": meta["provisional"]}
CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Modelo seleccionado: {describe(spec)} sobre {exp} ({len(cols)} features)")
print(" razón      :", reason); print(" parámetros :", params_note); print(" ensemble   :", ens_note)
print(f" CV  RMSE {cv['rmse']:.4f}  MAE {cv['mae']:.4f}  R2 {cv['r2']:.4f} | espacial RMSE {cv['rmse_spatial']:.4f}")
if gap: print(f" vs municipio ({gap['muni_model']}): {gap['muni_rmse']:.4f}  Δ={gap['delta']:+.4f} -> {gap['reading']}")
print("Escrito", CONFIG_FILE)
