"""Corre experimentos E0–E5 (+ diagnósticos) x modelos y escribe results/leaderboard.csv y results/oof/*.csv.

Uso:
  CEBADA_DATA=/ruta/DATASET_RETO_AGRO_2026_LIMPIO python run_experiments.py --repeats 3 --fast      # prueba rápida
  CEBADA_DATA=... python run_experiments.py --repeats 10                                            # oficial
  --exps E5_fusion E4_clima   --models ridge extratrees catboost   (para acotar)
"""
import argparse, time
import numpy as np, pandas as pd
from src import config as C
from src.data import load, families, columns_for, EXPERIMENTS
from src.models import zoo
from src.cv import repeated_cv, spatial_cv

ap = argparse.ArgumentParser()
ap.add_argument("--repeats", type=int, default=C.N_REPEATS)
ap.add_argument("--fast", action="store_true")
ap.add_argument("--exps", nargs="*", default=list(EXPERIMENTS))
ap.add_argument("--models", nargs="*", default=None)
ap.add_argument("--tag", default="")
a = ap.parse_args()

tr, ev = load()
fam = families(tr); y = tr[C.TARGET].values; g = tr["grupo_espacial"].values
models = zoo(a.fast)
if a.models: models = {k: v for k, v in models.items() if k in a.models}
(C.RESULTS / "oof").mkdir(parents=True, exist_ok=True)
rows = []
for e in a.exps:
    cols = columns_for(e, fam)
    for name, mk in models.items():
        if e == "E0_baseline" and name != "dummy_median":   # E0 solo el baseline ingenuo
            continue
        if e != "E0_baseline" and name == "dummy_median":
            continue
        X = tr[cols].values if cols else np.zeros((len(tr), 1))
        t0 = time.time()
        rep, oof, _ = repeated_cv(mk, X, y, n_repeats=a.repeats)
        sp, _ = spatial_cv(mk, X, y, g)
        rows.append(dict(exp=e, model=name, n_feat=len(cols), rmse=rep.rmse.mean(), rmse_sd=rep.rmse.std(ddof=1),
                         mae=rep.mae.mean(), r2=rep.r2.mean(), rmse_spatial=sp["rmse"], r2_spatial=sp["r2"],
                         repeats=a.repeats, secs=round(time.time() - t0, 1)))
        pd.DataFrame({C.ID: tr[C.ID], "y": y, "oof": oof}).to_csv(C.RESULTS / "oof" / f"{e}__{name}.csv", index=False)
        print(f"{e:18s} {name:13s} feats={len(cols):3d} RMSE {rows[-1]['rmse']:.3f}±{rows[-1]['rmse_sd']:.3f} "
              f"MAE {rows[-1]['mae']:.3f} R2 {rows[-1]['r2']:.3f} | espacial RMSE {sp['rmse']:.3f}  ({rows[-1]['secs']}s)", flush=True)
lb = pd.DataFrame(rows).sort_values("rmse")
lb.to_csv(C.RESULTS / f"leaderboard{a.tag}.csv", index=False)
print("\nTOP 10\n", lb.head(10).round(3).to_string(index=False))
