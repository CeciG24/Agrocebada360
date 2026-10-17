
"""P3.6 - Intervalos exploratorios del modelo definitivo yield-v1."""

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ML_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = ML_DIR / "results"
OUTPUT_DIR = RESULTS_DIR / "rol3" / "intervalos_yield_v1"

OOF_PATH = RESULTS_DIR / "oof" / "E4_clima__ridge.csv"
PRED_PATH = RESULTS_DIR / "predictions_raw.csv"
CONFIG_PATH = RESULTS_DIR / "final_model_config.json"

ALPHA = 0.10

config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
assert config["model_version"] == "yield-v1"
assert config["experiment"] == "E4_clima"
assert config["spec"]["model"] == "ridge"
assert config["n_features"] == 30

oof = pd.read_csv(OOF_PATH)
pred = pd.read_csv(PRED_PATH)

required_oof = {"parcel_id", "y", "oof"}
required_pred = {
    "parcel_id", "rendimiento_pred_t_ha", "model_version"
}

assert required_oof.issubset(oof.columns)
assert required_pred.issubset(pred.columns)
assert len(oof) == 138
assert len(pred) == 59

for name, df in [("OOF", oof), ("predicciones", pred)]:
    if df["parcel_id"].isna().any() or df["parcel_id"].duplicated().any():
        raise ValueError(f"Identificadores invalidos en {name}")

if not (pred["model_version"] == "yield-v1").all():
    raise ValueError("Las predicciones no corresponden a yield-v1")

if not np.isfinite(oof[["y", "oof"]].to_numpy(dtype=float)).all():
    raise ValueError("Valores OOF invalidos")

if not np.isfinite(pred["rendimiento_pred_t_ha"].to_numpy(dtype=float)).all():
    raise ValueError("Predicciones invalidas")

# Residuos de las predicciones OOF promediadas entre repeticiones.
errors = np.abs(
    oof["y"].to_numpy(dtype=float)
    - oof["oof"].to_numpy(dtype=float)
)

n = len(errors)
k = min(math.ceil((n + 1) * (1 - ALPHA)), n)
margin = float(np.sort(errors)[k - 1])

mae = float(np.mean(errors))
rmse = float(np.sqrt(np.mean(errors**2)))
covered = int(np.sum(errors <= margin))
coverage = float(covered / n)

# No se modifica el archivo oficial.
result = pred.copy()
result["margen_exploratorio_t_ha"] = margin
result["limite_inferior_t_ha"] = (
    result["rendimiento_pred_t_ha"] - margin
)
result["limite_superior_t_ha"] = (
    result["rendimiento_pred_t_ha"] + margin
)
result["nivel_nominal"] = "90% exploratorio"
result["metodo"] = "Cuantil de residuos OOF promediados E4_clima/ridge"

if result.isna().any().any():
    raise ValueError("Hay valores faltantes en los intervalos")

if not (
    (result["limite_inferior_t_ha"] <= result["rendimiento_pred_t_ha"])
    & (result["rendimiento_pred_t_ha"] <= result["limite_superior_t_ha"])
).all():
    raise ValueError("Los intervalos no contienen sus predicciones")

metadata = {
    "model_version": "yield-v1",
    "experiment": "E4_clima",
    "algorithm": "ridge",
    "data_version": config["provenance"]["data_version"],
    "oof_source": str(OOF_PATH.relative_to(ML_DIR)),
    "oof_method": "Promedio OOF de CV aleatoria repetida",
    "n_calibration_residuals": n,
    "n_evaluation": len(pred),
    "nominal_level": 0.90,
    "alpha": ALPHA,
    "quantile_rank": k,
    "mae_oof_t_ha": mae,
    "rmse_oof_t_ha": rmse,
    "margin_t_ha": margin,
    "interval_width_t_ha": 2 * margin,
    "descriptive_oof_coverage": coverage,
    "descriptive_oof_covered": covered,
    "limitations": [
        "No existe conjunto independiente de calibracion.",
        "La cobertura OOF es descriptiva, no una garantia conformal.",
        "No se ha validado la cobertura espacial de yield-v1.",
        "La seguridad temporal de todas las variables no esta certificada."
    ]
}

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

result.to_csv(
    OUTPUT_DIR / "predicciones_intervalos_yield_v1.csv",
    index=False
)

(OUTPUT_DIR / "metadata_intervalos_yield_v1.json").write_text(
    json.dumps(metadata, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("MODELO:", config["model_version"])
print("PARCELAS OOF:", n)
print("PARCELAS DE EVALUACION:", len(pred))
print("MAE OOF:", round(mae, 6))
print("RMSE OOF:", round(rmse, 6))
print("MARGEN 90%:", round(margin, 6))
print("ANCHO:", round(2 * margin, 6))
print("COBERTURA OOF:", round(coverage * 100, 2), "%")
print("PARCELAS CUBIERTAS:", covered, "de", n)

print("\nPRIMERAS CINCO PARCELAS:")
print(
    result[
        [
            "parcel_id",
            "rendimiento_pred_t_ha",
            "limite_inferior_t_ha",
            "limite_superior_t_ha"
        ]
    ].head().round(6).to_string(index=False)
)

print("\nARCHIVOS GENERADOS EN:", OUTPUT_DIR)
print("Las predicciones oficiales no fueron modificadas.")
