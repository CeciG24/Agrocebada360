"""Auditoría del dataset de Rol 1 contra system-contract.md (§1.7 corte temporal, §3 IDs/faltantes).

Entrada : CEBADA_DATA (carpeta DATASET_RETO_AGRO_2026_LIMPIO)
Salida  : results/data_audit.json  (+ resumen en consola). Exit code 1 si falla el corte temporal.
Versión : audit-v1 (contrato 0.1.0)

Qué verifica:
  1. Estructura: IDs str/únicos/consistentes, 138/59, sin NaN/inf, sin target en eval.
  2. Corte: filas de series crudas posteriores a DATA_CUTOFF y si features_master las usa
     (recalcula agregados con distintas ventanas y ve cuál reproduce lo entregado).
"""
import json, sys
import numpy as np, pandas as pd
from src import config as C
from src.contract import validate_catalog

root = C.DATA_ROOT
cut = pd.Timestamp(C.DATA_CUTOFF)
rep = {"cutoff": C.DATA_CUTOFF, "data_root": str(root)}

# 1) estructura
cat = validate_catalog(root)
fm = pd.read_csv(root / "features/features_master.csv", dtype={C.ID: str})
num = fm.select_dtypes("number")
rep["structure"] = {"n_parcels": len(fm), "split": fm.dataset_split.value_counts().to_dict(),
                    "n_features_numeric": num.shape[1], "nan_cells": int(fm.isna().sum().sum()),
                    "inf_cells": int(np.isinf(num.to_numpy(float)).sum())}

# 2) filas crudas posteriores al corte
def load_ts(path, idcol):
    d = pd.read_csv(root / path); d["f"] = pd.to_datetime(d["fecha_captura"]); return d.rename(columns={idcol: C.ID})
S = {"sentinel2": load_ts("sensores/sentinel2_timeseries.csv", "ID_POLIGONO"),
     "landsat": load_ts("sensores/landsat_timeseries.csv", "ID_POLIGONO"),
     "planet": load_ts("sensores/planet_timeseries.csv", "ID_POLIGONO"),
     "clima": load_ts("clima/climate_timeseries.csv", C.ID)}
rep["raw_rows_after_cutoff"] = {k: {"after": int((d.f > cut).sum()), "total": len(d), "max_date": str(d.f.max().date())} for k, d in S.items()}

# 3) ¿features_master usa esas filas? (se prueba con 40 parcelas)
ids = fm[C.ID].head(40).tolist()
def match(sensor, col, feat, valcol):
    d = S[sensor]; res = {"todo el histórico": 0, "hasta corte": 0, "abr–oct 2025": 0}
    for i in ids:
        x = d[d[C.ID] == i]; v = fm.loc[fm[C.ID] == i, feat].iloc[0]
        win = {"todo el histórico": x, "hasta corte": x[x.f <= cut], "abr–oct 2025": x[(x.f >= "2025-04-01") & (x.f <= cut)]}
        for k, w in win.items():
            res[k] += int(np.isclose(w[valcol].mean(), v, atol=1e-6))
    return res
rep["feature_window_match_40_parcels"] = {
    "sentinel2_ndvi_mean": match("sentinel2", "ndvi", "sentinel2_ndvi_mean", "ndvi_promedio"),
    "planet_ndvi_mean": match("planet", "ndvi", "planet_ndvi_mean", "ndvi_promedio"),
}
cl = S["clima"]; ok = {"año 2025 completo": 0, "ene–oct 2025": 0, "abr–oct 2025": 0}
for i in ids:
    x = cl[(cl[C.ID] == i) & (cl.f.dt.year == 2025)]; v = fm.loc[fm[C.ID] == i, "precip_total_mm_2025"].iloc[0]
    ok["año 2025 completo"] += int(np.isclose(x.precip_mm.sum(), v, atol=1e-6))
    ok["ene–oct 2025"] += int(np.isclose(x[x.f <= cut].precip_mm.sum(), v, atol=1e-6))
    ok["abr–oct 2025"] += int(np.isclose(x[(x.f >= "2025-04-01") & (x.f <= cut)].precip_mm.sum(), v, atol=1e-6))
rep["feature_window_match_40_parcels"]["precip_total_mm_2025"] = ok
for c in ("sentinel2_ndvi_peak_date", "planet_ndvi_peak_date"):
    rep.setdefault("peak_dates", {})[c] = {"min": str(pd.read_csv(root / "features/fenologia_features.csv")[c].min()),
                                           "max": str(pd.read_csv(root / "features/fenologia_features.csv")[c].max())}

m = rep["feature_window_match_40_parcels"]
ndvi_s2_ok = (m["sentinel2_ndvi_mean"]["abr–oct 2025"] == 40 or m["sentinel2_ndvi_mean"]["hasta corte"] == 40)
ndvi_pl_ok = (m["planet_ndvi_mean"]["abr–oct 2025"] == 40 or m["planet_ndvi_mean"]["hasta corte"] == 40)
precip_ok = (m["precip_total_mm_2025"]["abr–oct 2025"] == 40 or m["precip_total_mm_2025"]["ene–oct 2025"] == 40)
peaks_ok = all(pd.to_datetime(rep["peak_dates"][c]["max"]) <= cut for c in ("sentinel2_ndvi_peak_date", "planet_ndvi_peak_date"))

rep["cutoff_ok"] = bool(ndvi_s2_ok and ndvi_pl_ok and precip_ok and peaks_ok)
C.RESULTS.mkdir(parents=True, exist_ok=True)
(C.RESULTS / "data_audit.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False, default=str))
print(json.dumps(rep, indent=2, ensure_ascii=False, default=str))
print("\nCORTE TEMPORAL:", "OK" if rep["cutoff_ok"] else "VIOLADO (ver feature_window_match: los agregados usan datos posteriores al corte / otros ciclos)")
sys.exit(0 if rep["cutoff_ok"] else 1)
