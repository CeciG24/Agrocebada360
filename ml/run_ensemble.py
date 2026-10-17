"""P2.7 — Evaluar el ensemble final de los modelos finalistas.

Entrada : CEBADA_DATA; finalistas = --models, o los de results/tuning_summary.csv, o extratrees/rf/catboost
Salida  : results/ensemble/ensemble_config.json   (miembros, pesos, params, decisión keep/discard, métricas, procedencia)
          results/ensemble/ensemble_compare.csv   (RMSE por repetición: miembros, promedio, ponderado anidado)
          results/ensemble/ensemble_oof.csv       (parcel_id, y, oof del resultado elegido — insumo de Rol 3)
Versión : ensemble-v2 (contrato 0.3.0)

Protocolo:
  * folds idénticos para todos los modelos (member_oofs);
  * ponderación con STACKING ANIDADO: los pesos de cada fold externo se ajustan solo con su train (sin fuga entre niveles);
  * comparación contra el MEJOR modelo individual; se conserva solo si mejora >= --min-gain en promedio, gana en >= --min-win
    de las repeticiones y no empeora en CV espacial. Descartar el ensemble es un resultado válido.
  * `--params tuned` usa hiperparámetros elegidos con TODAS las parcelas etiquetadas: la comparación deja de ser independiente
    (queda marcada `evaluation_independent=false`). Para una decisión imparcial usa `--params default` (valor por defecto).

P2.9 reentrena con src.ensemble.build_ensemble(...) usando ensemble_config.json.

Uso:
  CEBADA_DATA=... python run_ensemble.py --repeats 3 --fast --models ridge extratrees catboost
  CEBADA_DATA=... python run_ensemble.py --repeats 10                      # decisión imparcial (parámetros por defecto)
  CEBADA_DATA=... python run_ensemble.py --repeats 10 --params tuned       # NO independiente (se marca en el JSON)
"""
import argparse, json
import numpy as np, pandas as pd
from src import config as C
from src import contract as K
from src import provenance as PV
from src.data import load, families, columns_for
from src.ensemble import member_oofs, weighted_oofs, compare, decide, build_ensemble
from src.tuning import load_best
from src.final import best_official_exp

ap = argparse.ArgumentParser()
ap.add_argument("--exp", default=None, help="por defecto: el mejor experimento OFICIAL del leaderboard")
ap.add_argument("--models", nargs="*", default=None)
ap.add_argument("--repeats", type=int, default=C.N_REPEATS)
ap.add_argument("--fast", action="store_true")
ap.add_argument("--params", choices=["default", "tuned"], default="default")
ap.add_argument("--skip-weighted", action="store_true", help="no evalúa la ponderación anidada (más rápido; solo promedio simple)")
ap.add_argument("--min-gain", type=float, default=0.005)
ap.add_argument("--min-win", type=float, default=0.8)
ap.add_argument("--spatial-tol", type=float, default=0.01)
a = ap.parse_args()

if a.exp is None:
    a.exp = best_official_exp(); print(f'Experimento por defecto = mejor oficial del leaderboard: {a.exp}', flush=True)
if a.exp not in C.OFFICIAL_EXPERIMENTS:
    raise SystemExit(f"{a.exp} no es un experimento oficial {C.OFFICIAL_EXPERIMENTS}")
names = a.models
if not names:
    try: names = pd.read_csv(C.RESULTS / "tuning_summary.csv").model.tolist()
    except FileNotFoundError: names = ["extratrees", "rf", "catboost"]
names = list(dict.fromkeys(names))
if len(names) < 2: raise SystemExit("El ensemble necesita al menos 2 modelos")

tr, _ = load(); cols = columns_for(a.exp, families(tr)); K.validate_features(tr, cols)
X = tr[cols].to_numpy(float); y = tr[C.TARGET].to_numpy(float); g = tr["grupo_espacial"].to_numpy()
params = {n: load_best(n, a.exp) for n in names} if a.params == "tuned" else {}
independent = a.params != "tuned"
meta = PV.run_meta(exp=a.exp, models=names, repeats=a.repeats, fast=a.fast, params=a.params)
print(f"Ensemble sobre {a.exp} ({len(cols)} features), miembros={names}, params={a.params}, repeticiones={a.repeats}", flush=True)
if not independent:
    print("⚠️  --params tuned: los hiperparámetros se eligieron con todas las parcelas; la comparación NO es independiente.", flush=True)
if meta["provisional"]:
    print("⚠️  PROVISIONAL:", meta["audit_reason"], flush=True)

P, Ps = member_oofs(names, params, X, y, g, a.repeats, a.fast)
Pw = Pws = None
w_nested = None
if not a.skip_weighted:
    Pw, Pws, w_nested = weighted_oofs(names, params, X, y, g, a.repeats, a.fast)
res = compare(P, Ps, y, names, Pw, Pws)
dec = decide(res, a.min_gain, a.min_win, a.spatial_tol)
b = res["best_idx"]
w = res["weights_full"] if dec["variant"] == "weighted" else np.full(len(names), 1 / len(names))

out = C.RESULTS / "ensemble"; out.mkdir(parents=True, exist_ok=True)
pd.DataFrame({**{n: res["members"][:, j] for j, n in enumerate(names)}, "mean": res["mean"], "weighted_nested": res["weighted"]}
             ).rename_axis("repeat").to_csv(out / "ensemble_compare.csv")
if dec["keep"]:
    oof = Pw.mean(0) if dec["variant"] == "weighted" else P.mean(0).mean(1)        # el weighted ya es OOF anidado (sin fuga)
else:
    oof = P.mean(0)[:, b]
pd.DataFrame({C.ID: tr[C.ID], "y": y, "oof": oof}).to_csv(out / "ensemble_oof.csv", index=False)

cfg = {"version": "ensemble-v2", "exp": a.exp, "n_features": len(cols), "params_source": a.params,
       "evaluation_independent": independent, "member_params": params,
       "members": names, "best_single": names[b], "decision": dec,
       "final_choice": ({"type": "ensemble", "variant": dec["variant"], "weights": dict(zip(names, map(float, w)))}
                        if dec["keep"] else {"type": "single", "model": names[b]}),
       "rmse_cv_mean": {**{n: float(res["members"][:, j].mean()) for j, n in enumerate(names)},
                        "mean": float(res["mean"].mean()), "weighted_nested": float(np.nanmean(res["weighted"]))},
       "rmse_spatial": {**dict(zip(names, map(float, res["spatial"]["members"]))), "mean": res["spatial"]["mean"],
                        "weighted_nested": res["spatial"]["weighted"]},
       "weights_nested_mean": (dict(zip(names, map(float, w_nested))) if w_nested is not None else None),
       "residual_corr": pd.DataFrame(res["resid_corr"], index=names, columns=names).round(3).to_dict(),
       "provenance": meta, "provisional": meta["provisional"],
       "note": ("Pesos finales = simplex sobre el OOF completo (receta que reproduce train_final_model.py); la estimación de "
                "'weighted_nested' ajusta los pesos dentro de cada fold externo, sin fuga.")}
(out / "ensemble_config.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")

ens = build_ensemble(names, w, params, a.fast).fit(tr[cols], y)           # humo: el artefacto se puede construir y predecir
assert np.isfinite(ens.predict(tr[cols].head(5))).all()
print("\nRMSE CV (media de repeticiones):")
for k_, v in cfg["rmse_cv_mean"].items():
    sp = cfg["rmse_spatial"].get(k_)
    print(f"  {k_:16s} {v:.4f}   | espacial {sp:.4f}")
print(f"\nDecisión: {'CONSERVAR' if dec['keep'] else 'DESCARTAR'} ensemble ({dec['variant']}) — mejora media {dec['mean_gain_rmse']:+.4f} t/ha, "
      f"gana en {dec['win_rate']:.0%} de repeticiones, Δ espacial {dec['spatial_delta_rmse']:+.4f}")
print("Elección final:", cfg["final_choice"]); print("Correlación de residuos:\n", pd.DataFrame(cfg["residual_corr"]).to_string())
