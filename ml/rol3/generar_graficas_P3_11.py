from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
OUT = RESULTS / "rol3" / "graficas_yield_v1"

OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 140,
    "savefig.dpi": 200,
    "font.size": 10,
    "axes.grid": True,
    "grid.alpha": 0.25,
})

def guardar(nombre):
    plt.tight_layout()
    plt.savefig(OUT / nombre, bbox_inches="tight")
    plt.close()
    print("Generada:", nombre)


# 1. Predicho vs real: OOF exploratorio E4_clima Ridge

oof = pd.read_csv(RESULTS / "oof/E4_clima__ridge.csv")

required = {"parcel_id", "y", "oof"}
assert required.issubset(oof.columns)
assert len(oof) == 138
assert oof["parcel_id"].is_unique
assert oof[["y", "oof"]].notna().all().all()

y = oof["y"].to_numpy(dtype=float)
pred = oof["oof"].to_numpy(dtype=float)

lim_min = min(y.min(), pred.min())
lim_max = max(y.max(), pred.max())

plt.figure(figsize=(6.5, 5.5))
plt.scatter(y, pred, alpha=0.7, s=30)
plt.plot(
    [lim_min, lim_max],
    [lim_min, lim_max],
    "--",
    linewidth=1.5,
    label="Prediccion perfecta"
)
plt.xlabel("Rendimiento real (t/ha)")
plt.ylabel("Prediccion OOF (t/ha)")
plt.title("Predicho vs real - E4_clima Ridge (OOF)")
plt.legend()
guardar("01_predicho_vs_real.png")


# 2. Residuos: real menos predicho

residuos = y - pred

fig, ax = plt.subplots(figsize=(6.5, 5.5))
ax.scatter(pred, residuos, alpha=0.7, s=30)
ax.axhline(0, linestyle="--", linewidth=1.5)
ax.set_xlabel("Prediccion OOF (t/ha)")
ax.set_ylabel("Residuo: real - predicho (t/ha)")
ax.set_title("Residuos - E4_clima Ridge (OOF)")
guardar("02_residuos.png")


# 3. Importancia SHAP del modelo definitivo yield-v1

shap = pd.read_csv(
    RESULTS / "rol3/shap_yield_v1/shap_importancia_yield_v1.csv"
)

print("Columnas SHAP:", list(shap.columns))

candidatas_variable = [
    "feature", "variable", "feature_name"
]
candidatas_importancia = [
    "mean_abs_shap", "mean_abs_shap_value",
    "importancia_media_absoluta", "importance",
    "importancia_shap_media_t_ha"
]

col_variable = next(
    (c for c in candidatas_variable if c in shap.columns), None
)
col_importancia = next(
    (c for c in candidatas_importancia if c in shap.columns), None
)

if col_variable is None or col_importancia is None:
    raise ValueError(
        "Columnas SHAP no reconocidas: " + str(list(shap.columns))
    )

top = (
    shap.nlargest(12, col_importancia)
    .sort_values(col_importancia)
)

plt.figure(figsize=(9, 6))
plt.barh(
    top[col_variable].astype(str),
    top[col_importancia].astype(float)
)
plt.xlabel("Media de |SHAP| (t/ha)")
plt.title("Importancia global SHAP - yield-v1")
guardar("03_importancia_shap.png")


# 4. RMSE temporal: early-v2, NO yield-v1

early = pd.read_csv(
    RESULTS / "early/early_leaderboard.csv"
)

meses = ["junio", "julio", "agosto", "septiembre", "octubre"]
modelos = ["ridge", "extratrees", "catboost"]

plt.figure(figsize=(8, 5.5))

for modelo in modelos:
    serie = (
        early.loc[early["model"] == modelo]
        .set_index("cut")
        .reindex(meses)
    )
    assert serie["rmse"].notna().all(), modelo

    plt.plot(
        [m.capitalize() for m in meses],
        serie["rmse"],
        marker="o",
        linewidth=2,
        label=modelo
    )

plt.xlabel("Corte temporal de 2025")
plt.ylabel("RMSE convencional (t/ha)")
plt.title("Prediccion temprana - early-v2 (27 variables)")
plt.legend()
guardar("04_rmse_temporal_early_v2.png")


print()
print("Resumen:")
print("Parcelas OOF:", len(oof))
print("RMSE OOF agregado:", np.sqrt(np.mean(residuos ** 2)))
print("MAE OOF agregado:", np.mean(np.abs(residuos)))
print("Graficas guardadas en:", OUT)
