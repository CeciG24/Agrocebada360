"""P2.7 — Evaluar el ensemble final de los modelos finalistas.

Entrada : CEBADA_DATA; finalistas = --models, o los de results/tuning_summary.csv, o extratrees/rf/catboost
Salida  : results/ensemble/ensemble_config.json   (miembros, pesos, params, decisión keep/discard, métricas)
          results/ensemble/ensemble_compare.csv   (RMSE por repetición: miembros, promedio, ponderado)
          results/ensemble/ensemble_oof.csv       (parcel_id, y, oof del ensemble elegido — insumo de Rol 3)
Versión : ensemble-v1 (contrato 0.1.0)

Protocolo: folds idénticos para todos los modelos; ponderación con CV de nivel 2; comparación contra el MEJOR modelo
individual; se conserva solo si mejora >= --min-gain en promedio, gana en >= --min-win de las repeticiones y no empeora
en CV espacial. P2.9 reentrena con src.ensemble.build_ensemble(...) usando ensemble_config.json.

Uso:
  CEBADA_DATA=... python run_ensemble.py --repeats 3 --fast --models ridge extratrees catboost
  CEBADA_DATA=... python run_ensemble.py --repeats 10 --params tuned
"""
import argparse, json
import numpy as np, pandas as pd
from src import config as C
from src import contract as K
from src.data import load, families, columns_for
from src.ensemble import member_oofs, compare, decide, build_ensemble, simplex_weights
from src.tuning import load_best

ap = argparse.ArgumentParser()
ap.add_argument("--exp", default="E5_fusion")
ap.add_argument("--models", nargs="*", default=None)
ap.add_argument("--repeats", type=int, default=C.N_REPEATS)
ap.add_argument("--fast", action="store_true")
ap.add_argument("--params", choices=["default", "tuned"], default="default")
ap.add_argument("--min-gain", type=float, default=0.005)
ap.add_argument("--min-win", type=float, default=0.8)
ap.add_argument("--spatial-tol", type=float, default=0.01)
a = ap.parse_args()

names = a.models
if not names:
    try: names = pd.read_csv(C.RESULTS / "tuning_summary.csv").model.tolist()
    except FileNotFoundError: names = ["extratrees", "rf", "catboost"]
if len(names) < 2: raise SystemExit("El ensemble necesita al menos 2 modelos")

tr, _ = load(); cols = columns_for(a.exp, families(tr)); K.validate_features(tr, cols)
X = tr[cols].to_numpy(float); y = tr[C.TARGET].to_numpy(float); g = tr["grupo_espacial"].to_numpy()
params = {n: load_best(n, a.exp) for n in names} if a.params == "tuned" else {}
try: audit_ok = bool(json.loads((C.RESULTS / "data_audit.json").read_text())["cutoff_ok"])
except FileNotFoundError: audit_ok = None
print(f"Ensemble sobre {a.exp} ({len(cols)} features), miembros={names}, params={a.params}, repeticiones={a.repeats}", flush=True)

P, Ps = member_oofs(names, params, X, y, g, a.repeats, a.fast)
res = compare(P, Ps, y, names)
dec = decide(res, a.min_gain, a.min_win, a.spatial_tol)
b = res["best_idx"]; w = res["weights_full"] if dec["variant"] == "weighted" else np.full(len(names), 1 / len(names))

out = C.RESULTS / "ensemble"; out.mkdir(parents=True, exist_ok=True)
pd.DataFrame({**{n: res["members"][:, j] for j, n in enumerate(names)}, "mean": res["mean"], "weighted": res["weighted"]}
             ).rename_axis("repeat").to_csv(out / "ensemble_compare.csv")
oof = (P.mean(0) @ w) if dec["keep"] else P.mean(0)[:, b]
pd.DataFrame({C.ID: tr[C.ID], "y": y, "oof": oof}).to_csv(out / "ensemble_oof.csv", index=False)

cfg = {"version": "ensemble-v1", "exp": a.exp, "n_features": len(cols), "params_source": a.params, "member_params": params,
       "members": names, "best_single": names[b], "decision": dec,
       "final_choice": ({"type": "ensemble", "variant": dec["variant"], "weights": dict(zip(names, map(float, w)))}
                        if dec["keep"] else {"type": "single", "model": names[b]}),
       "rmse_cv_mean": {**{n: float(res["members"][:, j].mean()) for j, n in enumerate(names)},
                        "mean": float(res["mean"].mean()), "weighted": float(res["weighted"].mean())},
       "rmse_spatial": {**dict(zip(names, map(float, res["spatial"]["members"]))), "mean": res["spatial"]["mean"],
                        "weighted": res["spatial"]["weighted"]},
       "residual_corr": pd.DataFrame(res["resid_corr"], index=names, columns=names).round(3).to_dict(),
       "data_cutoff_verified": audit_ok, "provisional": audit_ok is not True,
       "note": "PROVISIONAL: reejecutar con el dataset corregido (corte 2025-10-31)." if audit_ok is not True else ""}
(out / "ensemble_config.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False))

ens = build_ensemble(names, w, params, a.fast).fit(X, y)                  # humo: el artefacto se puede construir y predecir
assert np.isfinite(ens.predict(X[:5])).all()
print("\nRMSE CV (media de repeticiones):")
for k_, v in cfg["rmse_cv_mean"].items(): print(f"  {k_:12s} {v:.4f}   | espacial {cfg['rmse_spatial'][k_]:.4f}")
print(f"\nDecisión: {'CONSERVAR' if dec['keep'] else 'DESCARTAR'} ensemble ({dec['variant']}) — mejora media {dec['mean_gain_rmse']:+.4f} t/ha, "
      f"gana en {dec['win_rate']:.0%} de repeticiones, Δ espacial {dec['spatial_delta_rmse']:+.4f}")
print("Elección final:", cfg["final_choice"]); print("Correlación de residuos:\n", pd.DataFrame(cfg["residual_corr"]).to_string())
