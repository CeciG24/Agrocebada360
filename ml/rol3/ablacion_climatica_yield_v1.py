from pathlib import Path
import json
import numpy as np
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config as C
from src.data import load
from src.cv import repeated_cv, spatial_cv
from src.models import zoo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "rol3" / "ablacion_yield_v1"
OUT.mkdir(parents=True, exist_ok=True)

config = json.loads(
    (ROOT / "results" / "final_model_config.json")
    .read_text(encoding="utf-8-sig")
)

assert config["model_version"] == "yield-v1"
assert config["experiment"] == "E4_clima"

features = config["features"]
assert len(features) == 30

train, _ = load()

assert len(train) == 138
assert all(c in train.columns for c in features)

y = train[C.TARGET].to_numpy(dtype=float)
groups = train["grupo_espacial"].to_numpy()

variantes = {
    "Completo_30": features,
    "Sin_precipitacion": [
        c for c in features if not c.startswith("precip_")
    ],
    "Sin_temperaturas": [
        c for c in features
        if not c.startswith(("tmin_", "tmax_"))
    ],
    "Sin_amplitud_termica": [
        c for c in features
        if not c.startswith("amplitud_")
    ],
    "Sin_2025": [
        c for c in features
        if not c.endswith("_2025")
    ],
    "Sin_multianual_2022_2025": [
        c for c in features
        if not c.endswith("_2022_2025")
    ],
}

crear_modelo = zoo(False)["ridge"]
resultados = []

for nombre, columnas in variantes.items():
    if not columnas:
        raise ValueError("Variante sin variables: " + nombre)

    X = train[columnas].to_numpy(dtype=float)

    rep, oof, _ = repeated_cv(
        crear_modelo, X, y, n_repeats=10
    )

    espacial, _ = spatial_cv(
        crear_modelo, X, y, groups
    )

    resultados.append({
        "variante": nombre,
        "n_variables": len(columnas),
        "rmse": float(rep["rmse"].mean()),
        "rmse_sd": float(rep["rmse"].std(ddof=1)),
        "mae": float(rep["mae"].mean()),
        "r2": float(rep["r2"].mean()),
        "rmse_espacial": float(espacial["rmse"]),
        "r2_espacial": float(espacial["r2"]),
    })

    print(
        f"{nombre:27s} "
        f"variables={len(columnas):2d} "
        f"RMSE={rep['rmse'].mean():.6f} "
        f"RMSE espacial={espacial['rmse']:.6f}",
        flush=True
    )

tabla = pd.DataFrame(resultados)

referencia = tabla.loc[
    tabla["variante"] == "Completo_30"
].iloc[0]

tabla["delta_rmse"] = tabla["rmse"] - referencia["rmse"]
tabla["delta_rmse_espacial"] = (
    tabla["rmse_espacial"] - referencia["rmse_espacial"]
)

salida = OUT / "ablacion_climatica_yield_v1.csv"
tabla.to_csv(salida, index=False)

print()
print("RESULTADOS GUARDADOS:", salida)
print()
print(tabla.round(6).to_string(index=False))
