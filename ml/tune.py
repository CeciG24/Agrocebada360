"""P2.5 — Tuning de los 2–3 mejores modelos con CV anidada.

Entrada : CEBADA_DATA; modelos finalistas (por defecto los 3 mejores de E5_fusion según results/leaderboard_p25_seleccion.csv)
Salida  : results/tuning/<exp>__<modelo>.json  (best_params, RMSE/MAE/R² anidados vs defaults, top candidatos)
          results/tuning_summary.csv           (tabla comparativa defaults vs afinado)
Versión : tune-v1 (contrato 0.1.0)

Protocolo (sin fuga):
  1. Búsqueda aleatoria sobre un espacio pequeño; candidato 0 = hiperparámetros por defecto.
  2. CV ANIDADA: por cada fold externo se busca SOLO con su train (CV interna 3-fold) y se predice el fold externo.
     El RMSE externo es la estimación honesta de "afinar + entrenar".  Se compara con los defaults en los mismos folds.
  3. Hiperparámetros finales: búsqueda con CV repetida sobre las 138 parcelas (su RMSE es optimista; no se reporta como desempeño).
  La partición de 59 parcelas NO se usa (no tiene target).

Uso:
  CEBADA_DATA=... python tune.py                         # 3 finalistas, E5_fusion
  CEBADA_DATA=... python tune.py --models extratrees --n-iter 8 --outer-repeats 1
"""
import argparse, json, time
import numpy as np, pandas as pd
from sklearn.model_selection import KFold
from src import config as C
from src.cv import metrics
from src.data import load, families, columns_for
from src.tuning import build, search, cv_rmse, SPACES

ap = argparse.ArgumentParser()
ap.add_argument("--exp", default="E5_fusion")
ap.add_argument("--models", nargs="*", default=None)
ap.add_argument("--n-iter", type=int, default=15)
ap.add_argument("--outer-repeats", type=int, default=2)
ap.add_argument("--final-repeats", type=int, default=3)
a = ap.parse_args()

tr, _ = load(); fam = families(tr)
cols = columns_for(a.exp, fam); X = tr[cols].to_numpy(float); y = tr[C.TARGET].to_numpy(float)

models = a.models
if not models:
    lb = pd.read_csv(C.RESULTS / "leaderboard.csv")
    models = lb[lb.exp == a.exp].sort_values("rmse").model.head(3).tolist()
print(f"Finalistas ({a.exp}, {len(cols)} features): {models}", flush=True)

try:
    cutoff_ok = bool(json.loads((C.RESULTS / "data_audit.json").read_text())["cutoff_ok"])
except FileNotFoundError:
    cutoff_ok = None
(C.RESULTS / "tuning").mkdir(parents=True, exist_ok=True)
rows = []
for name in models:
    t0 = time.time(); oof_t = [np.zeros(len(y)) for _ in range(a.outer_repeats)]; oof_d = [np.zeros(len(y)) for _ in range(a.outer_repeats)]
    chosen = []
    for r in range(a.outer_repeats):
        for k, (itr, iva) in enumerate(KFold(C.N_SPLITS, shuffle=True, random_state=C.SEED + 100 + r).split(X)):
            best_p = search(name, X[itr], y[itr], a.n_iter, seed=C.SEED + k)[0][1]       # solo con el train externo
            m = build(name, best_p); m.fit(X[itr], y[itr]); oof_t[r][iva] = m.predict(X[iva])
            d = build(name); d.fit(X[itr], y[itr]); oof_d[r][iva] = d.predict(X[iva])
            chosen.append(best_p)
        print(f"  {name}: repetición externa {r+1}/{a.outer_repeats} ({time.time()-t0:.0f}s)", flush=True)
    mt = pd.DataFrame([metrics(y, o) for o in oof_t]).mean(); md = pd.DataFrame([metrics(y, o) for o in oof_d]).mean()
    sd = lambda oo: float(np.std([metrics(y, o)["rmse"] for o in oo], ddof=1)) if len(oo) > 1 else float("nan")

    ranked = search(name, X, y, a.n_iter, n_splits=C.N_SPLITS, repeats=a.final_repeats)     # hiperparámetros finales
    best_rmse, best_params = ranked[0]
    res = {"exp": a.exp, "model": name, "n_features": len(cols), "best_params": best_params,
           "search_cv_rmse_optimistic": best_rmse, "default_search_cv_rmse": next(s for s, p in ranked if p == {}),
           "nested": {"tuned": mt.to_dict(), "default": md.to_dict(), "rmse_sd_tuned": sd(oof_t), "rmse_sd_default": sd(oof_d),
                      "outer_repeats": a.outer_repeats, "n_iter": a.n_iter},
           "top5_candidates": [{"rmse": s, "params": p} for s, p in ranked[:5]],
           "folds_chose_default": int(sum(1 for p in chosen if p == {})), "folds_total": len(chosen),
           "data_cutoff_verified": cutoff_ok, "provisional": cutoff_ok is not True,
           "note": "PROVISIONAL: features_master no respeta el corte 2025-10-31; reejecutar con el dataset corregido." if cutoff_ok is not True else ""}
    (C.RESULTS / "tuning" / f"{a.exp}__{name}.json").write_text(json.dumps(res, indent=2, ensure_ascii=False, default=str))
    rows.append(dict(exp=a.exp, model=name, rmse_default=md.rmse, rmse_tuned_nested=mt.rmse, delta=mt.rmse - md.rmse,
                     mae_tuned=mt.mae, r2_tuned=mt.r2, folds_chose_default=f"{res['folds_chose_default']}/{res['folds_total']}",
                     best_params=json.dumps(best_params), secs=round(time.time() - t0)))
    print(f"{name:11s} default {md.rmse:.3f} → afinado (anidado) {mt.rmse:.3f}  Δ={mt.rmse-md.rmse:+.3f}  best={best_params}", flush=True)
# resumen = todos los JSON existentes (así corridas separadas por modelo se acumulan)
allrows = []
for f in sorted((C.RESULTS / "tuning").glob("*.json")):
    j = json.loads(f.read_text()); n = j["nested"]
    allrows.append(dict(exp=j["exp"], model=j["model"], rmse_default=n["default"]["rmse"], rmse_tuned_nested=n["tuned"]["rmse"],
                        delta=n["tuned"]["rmse"] - n["default"]["rmse"], mae_tuned=n["tuned"]["mae"], r2_tuned=n["tuned"]["r2"],
                        folds_chose_default=f"{j['folds_chose_default']}/{j['folds_total']}", best_params=json.dumps(j["best_params"]),
                        provisional=j["provisional"]))
pd.DataFrame(allrows).sort_values("rmse_tuned_nested").to_csv(C.RESULTS / "tuning_summary.csv", index=False)
print("\n", pd.DataFrame(rows).drop(columns="best_params").round(3).to_string(index=False))
