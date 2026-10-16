"""P2.6 — Modelos de predicción temprana: ¿qué tan pronto se puede anticipar el rendimiento final?

Entrada : CEBADA_DATA/prediccion_temprana/features/features_master_corte_<corte>.csv  (Rol 1, P1.12; también acepta .../matrices/)
Salida  : results/early/early_leaderboard.csv   (una fila por corte x modelo: RMSE±sd, MAE, R², RMSE espacial, mejora vs baselines)
          results/early/early_summary.json      (curva RMSE por corte, corte más temprano "útil", auditoría de ventanas)
          results/early/early_curve.png         (curva RMSE vs corte; si hay matplotlib)
          results/early/oof/<corte>__<modelo>.csv   (parcel_id, y, oof) para Rol 3
Versión : early-v2 (contrato 0.3.0)
Alcance : curva DIAGNÓSTICA de qué tan pronto se puede anticipar. NO produce un modelo por corte ni un endpoint de inferencia temprana.

Corte "útil" (se reportan los tres criterios):
  - supera a la mediana en >= --min-gain-dummy (5 % por defecto)
  - supera al promedio por municipio (el piso real)
  - queda a <= --tol (5 %) del RMSE del corte de octubre (el "techo" del ciclo completo)

Uso:
  CEBADA_DATA=... python run_early.py --repeats 3 --fast                      # prueba
  CEBADA_DATA=... python run_early.py --repeats 10 --models ridge extratrees catboost
  CEBADA_DATA=... python run_early.py --params tuned                          # usa results/tuning/E5_fusion__<modelo>.json
"""
import argparse, json, sys, time
import numpy as np, pandas as pd
from src import config as C
from src import provenance as PV
from src import early as E
from src.cv import repeated_cv, spatial_cv
from src.tuning import build, load_best

ap = argparse.ArgumentParser()
ap.add_argument("--cuts", nargs="*", default=list(E.CUTS))
ap.add_argument("--models", nargs="*", default=["ridge", "extratrees", "catboost"])
ap.add_argument("--repeats", type=int, default=C.N_REPEATS)
ap.add_argument("--fast", action="store_true")
ap.add_argument("--params", choices=["default", "tuned"], default="default")
ap.add_argument("--tol", type=float, default=0.05)
ap.add_argument("--min-gain-dummy", type=float, default=0.05)
ap.add_argument("--tag", default="")
a = ap.parse_args()

out = C.RESULTS / "early"; (out / "oof").mkdir(parents=True, exist_ok=True)
data = E.load_cuts(a.cuts)                                   # valida IDs, split, target y features por corte
issues, notes = E.audit_windows(data)
meta = PV.run_meta(cuts=a.cuts, models=a.models, repeats=a.repeats, params=a.params)
audit_ok = meta["audit_valid_for_dataset"]
provisional = bool(issues) or not audit_ok
if provisional:
    print("⚠️  RESULTADOS PROVISIONALES:" + (f" {len(issues)} incoherencias de ventana entre cortes." if issues else "")
          + ("" if audit_ok else f" {meta['audit_reason']}"), flush=True)
if a.params == "tuned":
    print("ℹ️  --params tuned usa hiperparámetros elegidos con TODAS las parcelas etiquetadas: la curva NO es una evaluación independiente.", flush=True)
    for i in issues[:5]: print("   ", i)
for n in notes: print("ℹ️ ", n)

groups_by_id = E.spatial_groups()
rows = []
for cut, d in data.items():
    tr, feats = d["tr"], d["feats"]
    y = tr[C.TARGET].to_numpy(float); g = groups_by_id.loc[tr[C.ID]].to_numpy()
    X = tr[feats].to_numpy(float)
    runs = {m: (lambda m=m: build(m, load_best(m) if a.params == "tuned" else None, fast=a.fast), X) for m in a.models}
    for b, Xb in E.baseline_matrices(tr).items():            # baselines por corte
        runs[b] = ((lambda b=b: build("dummy_median") if b == "dummy_median" else build("ridge")), Xb)
    for name, (mk, Xm) in runs.items():
        t0 = time.time()
        rep, oof, _ = repeated_cv(mk, Xm, y, n_repeats=a.repeats)
        sp, _ = spatial_cv(mk, Xm, y, g)
        rows.append(dict(cut=cut, cutoff=E.CUTS[cut], model=name, n_feat=Xm.shape[1], rmse=rep.rmse.mean(),
                         rmse_sd=rep.rmse.std(ddof=1) if a.repeats > 1 else np.nan, mae=rep.mae.mean(), r2=rep.r2.mean(),
                         rmse_spatial=sp["rmse"], r2_spatial=sp["r2"], repeats=a.repeats, secs=round(time.time() - t0, 1)))
        pd.DataFrame({C.ID: tr[C.ID], "y": y, "oof": oof}).to_csv(out / "oof" / f"{cut}__{name}.csv", index=False)
        print(f"{cut:11s} {name:16s} feats={Xm.shape[1]:3d} RMSE {rows[-1]['rmse']:.3f}  MAE {rows[-1]['mae']:.3f}  "
              f"R2 {rows[-1]['r2']:.3f} | espacial {sp['rmse']:.3f}", flush=True)

lb = pd.DataFrame(rows)
piv = lb.pivot(index="cut", columns="model", values="rmse").reindex(a.cuts)
lb["gain_vs_dummy"] = 1 - lb.rmse / lb.cut.map(piv["dummy_median"])
lb["gain_vs_municipio"] = 1 - lb.rmse / lb.cut.map(piv["ridge_municipio"])
last = a.cuts[-1]
lb["loss_vs_ceiling"] = lb.rmse / lb.apply(lambda r: piv.loc[last, r.model], axis=1) - 1   # >0: peor que con el ciclo completo
lb["cut"] = pd.Categorical(lb.cut, a.cuts, ordered=True)
lb = lb.sort_values(["model", "cut"]); lb.to_csv(out / f"early_leaderboard{a.tag}.csv", index=False)

summary = {"version": "early-v2", "provisional": provisional, "audit_valid_for_dataset": audit_ok, "params": a.params,
           "evaluation_independent": a.params != "tuned", "scope": "curva diagnóstica; no es un modelo por corte ni un endpoint",
           "provenance": meta,
           "window_issues": issues, "notes": notes, "ceiling_cut": last, "models": {}}
for m in a.models:
    curve = piv[m].to_dict()
    ceil = curve[last]
    summary["models"][m] = {
        "rmse_by_cut": curve,
        "earliest_beats_dummy": E.earliest_cut(curve, lambda c, r: r <= piv.loc[c, "dummy_median"] * (1 - a.min_gain_dummy)),
        "earliest_beats_municipio": E.earliest_cut(curve, lambda c, r: r < piv.loc[c, "ridge_municipio"]),
        "earliest_within_tol_of_ceiling": E.earliest_cut(curve, lambda c, r: r <= ceil * (1 + a.tol)),
    }
(out / f"early_summary{a.tag}.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

try:
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 4))
    for m in list(a.models) + ["dummy_median", "ridge_municipio"]:
        ax.plot(a.cuts, piv[m].values, marker="o", ls="--" if m in ("dummy_median", "ridge_municipio") else "-", label=m)
    ax.set_xlabel("Corte de información"); ax.set_ylabel("RMSE (t/ha, CV)"); ax.legend(); ax.grid(alpha=.3)
    ax.set_title("Predicción temprana" + (" (PROVISIONAL)" if provisional else ""))
    fig.tight_layout(); fig.savefig(out / f"early_curve{a.tag}.png", dpi=140)
except Exception as e:                                         # noqa: BLE001
    print("sin gráfica:", e)
print("\nRMSE por corte\n", piv.round(3).to_string())
print("\nResumen:", json.dumps({m: {k: v for k, v in s.items() if k != "rmse_by_cut"} for m, s in summary["models"].items()}, indent=1, ensure_ascii=False))
