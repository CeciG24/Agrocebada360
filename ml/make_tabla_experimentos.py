"""Entregable P2.4: tabla de experimentos (una fila por experimento, con su mejor modelo).
Lee results/leaderboard<tag>.csv y escribe results/tabla_experimentos<tag>.csv
Uso: python make_tabla_experimentos.py [--tag _oficial_v1]"""
import argparse
import pandas as pd
from src import config as C

ap = argparse.ArgumentParser(); ap.add_argument("--tag", default="")
a = ap.parse_args()
lb = pd.read_csv(C.RESULTS / f"leaderboard{a.tag}.csv")

DESC = {
    "E0_baseline": "Ninguna (mediana del train)", "E1_topo": "Topografía + área",
    "E2_basico": "Sentinel-2 + Landsat (+ fenología)", "E3_planet": "Planet (+ fenología)",
    "E4_clima": "Clima (precip., temperaturas)", "E5_fusion": "Todo: topo + básico + Planet + clima",
    "X0_municipio": "[diagnóstico] solo municipio", "X1_geo": "[diagnóstico] solo lat/lon",
    "X2_fusion_mas_geo": "[diagnóstico] E5 + lat/lon", "X3_muni_mas_sat": "[diagnóstico] municipio + topo + satélite",
}
best = lb.loc[lb.groupby("exp").rmse.idxmin()].copy()
best["descripcion"] = best.exp.map(DESC)
best["tipo"] = best.exp.map(lambda e: "baseline" if e == "E0_baseline" else ("oficial" if e in C.OFFICIAL_EXPERIMENTS else "diagnostico"))
# mejor modelo "defendible": mejor de cada experimento y también el promedio de todos los modelos (robustez)
best["rmse_prom_modelos"] = best.exp.map(lb.groupby("exp").rmse.mean())
cols = ["exp", "tipo", "descripcion", "n_feat", "model", "rmse", "rmse_sd", "mae", "r2", "rmse_spatial", "rmse_prom_modelos", "repeats"]
order = list(DESC)
out = best[cols].set_index("exp").loc[[e for e in order if e in set(best.exp)]].reset_index().round(3)
out.to_csv(C.RESULTS / f"tabla_experimentos{a.tag}.csv", index=False)
print(out.to_string(index=False))
print("\nNota: los experimentos 'diagnostico' usan municipio/ubicación y NO son candidatos al modelo oficial; "
      "el 'oficial' debe compararse contra ellos para saber cuánto aporta el satélite.")
