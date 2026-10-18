
"""P3.9 - Clasificacion de riesgo del modelo yield-v1."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

ML_DIR = Path(__file__).resolve().parents[1]
RESULTS = ML_DIR / "results"

PRED_PATH = RESULTS / "predictions_raw.csv"
OOD_PATH = RESULTS / "rol3/ood_yield_v1/predicciones_ood_yield_v1.csv"
INTERVAL_PATH = (
    RESULTS / "rol3/intervalos_yield_v1/"
    "predicciones_intervalos_yield_v1.csv"
)

OUTPUT_DIR = RESULTS / "rol3/riesgo_yield_v1"
OUTPUT_CSV = OUTPUT_DIR / "predicciones_riesgo_yield_v1.csv"
OUTPUT_META = OUTPUT_DIR / "metadata_riesgo_yield_v1.json"

pred = pd.read_csv(PRED_PATH)
ood = pd.read_csv(OOD_PATH)
intervals = pd.read_csv(INTERVAL_PATH)

sources = {
    "predicciones": pred,
    "ood": ood,
    "intervalos": intervals,
}

for name, df in sources.items():
    if len(df) != 59:
        raise ValueError(f"{name}: se esperaban 59 parcelas")
    if df["parcel_id"].isna().any():
        raise ValueError(f"{name}: hay IDs faltantes")
    if df["parcel_id"].duplicated().any():
        raise ValueError(f"{name}: hay IDs duplicados")
    if df.isna().any().any():
        raise ValueError(f"{name}: hay valores faltantes")
    if not df["model_version"].eq("yield-v1").all():
        raise ValueError(f"{name}: version de modelo incorrecta")

    if set(df["parcel_id"]) != set(pred["parcel_id"]):
        raise ValueError(f"{name}: las parcelas no coinciden")

# Verificar que las predicciones coincidan entre archivos.
reference = pred.set_index("parcel_id")["rendimiento_pred_t_ha"]

for name, df in [("ood", ood), ("intervalos", intervals)]:
    values = df.set_index("parcel_id")["rendimiento_pred_t_ha"]
    difference = (reference - values.reindex(reference.index)).abs()

    if not np.isfinite(difference.to_numpy()).all():
        raise ValueError(f"{name}: diferencias no finitas")

    if difference.max() > 1e-8:
        raise ValueError(f"{name}: las predicciones no coinciden")

# Integrar sin duplicar columnas de prediccion.
ood_columns = [
    "parcel_id",
    "score_ood",
    "alerta_ood",
    "umbral_ood",
    "interpretacion",
]

interval_columns = [
    "parcel_id",
    "margen_exploratorio_t_ha",
    "limite_inferior_t_ha",
    "limite_superior_t_ha",
    "nivel_nominal",
    "metodo",
]

df = pred.merge(
    ood[ood_columns],
    on="parcel_id",
    how="left",
    validate="one_to_one",
)

df = df.merge(
    intervals[interval_columns],
    on="parcel_id",
    how="left",
    validate="one_to_one",
)

if len(df) != 59 or df.isna().any().any():
    raise ValueError("La integracion contiene errores")

# Normalizar las alertas OOD.
if df["alerta_ood"].dtype != bool:
    values = df["alerta_ood"].astype(str).str.lower()

    if not values.isin(["true", "false"]).all():
        raise ValueError("Valores OOD invalidos")

    df["alerta_ood"] = values.eq("true")

if int(df["alerta_ood"].sum()) != 4:
    raise ValueError("Se esperaban 4 alertas OOD")

if not np.allclose(
    df["limite_superior_t_ha"] - df["rendimiento_pred_t_ha"],
    df["margen_exploratorio_t_ha"],
    atol=1e-8,
):
    raise ValueError("Los intervalos no son consistentes")

if not np.allclose(
    df["rendimiento_pred_t_ha"] - df["limite_inferior_t_ha"],
    df["margen_exploratorio_t_ha"],
    atol=1e-8,
):
    raise ValueError("Los intervalos no son consistentes")

# Clasificacion por terciles de rendimiento.
q1 = float(df["rendimiento_pred_t_ha"].quantile(1 / 3))
q2 = float(df["rendimiento_pred_t_ha"].quantile(2 / 3))

def clasificar_rendimiento(value):
    if value <= q1:
        return "Bajo relativo"
    if value <= q2:
        return "Intermedio relativo"
    return "Alto relativo"

df["nivel_relativo"] = df["rendimiento_pred_t_ha"].apply(
    clasificar_rendimiento
)

# Prioridades operativas de revision.
def asignar_prioridad(row):
    low = row["nivel_relativo"] == "Bajo relativo"
    outlier = row["alerta_ood"]

    if low and outlier:
        return "Prioridad alta de revision"
    if low:
        return "Revisar rendimiento estimado"
    if outlier:
        return "Revisar caracteristicas inusuales"
    return "Sin alerta combinada"

df["prioridad_revision"] = df.apply(asignar_prioridad, axis=1)

# Ordenar columnas.
columns = [
    "parcel_id",
    "rendimiento_pred_t_ha",
    "model_version",
    "nivel_relativo",
    "prioridad_revision",
    "score_ood",
    "alerta_ood",
    "interpretacion",
    "umbral_ood",
    "margen_exploratorio_t_ha",
    "limite_inferior_t_ha",
    "limite_superior_t_ha",
    "nivel_nominal",
    "metodo",
]

df = df[columns]

levels = df["nivel_relativo"].value_counts().to_dict()
priorities = df["prioridad_revision"].value_counts().to_dict()

metadata = {
    "model_version": "yield-v1",
    "n_parcels": len(df),
    "n_columns": len(df.columns),
    "n_ood_alerts": int(df["alerta_ood"].sum()),
    "tercile_1": q1,
    "tercile_2": q2,
    "relative_levels": levels,
    "review_priorities": priorities,
    "classification_method": "Terciles de predicciones de evaluacion",
    "priority_method": "Rendimiento bajo relativo y alerta OOD",
    "limitations": [
        "Los terciles son relativos, no umbrales agronomicos.",
        "Las prioridades no representan probabilidades de perdida.",
        "Los intervalos exploratorios no garantizan cobertura.",
        "Una alerta OOD no confirma un error predictivo.",
    ],
}

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

if OUTPUT_CSV.exists() or OUTPUT_META.exists():
    raise FileExistsError(
        "Los resultados ya existen; no se sobrescribiran"
    )

df.to_csv(OUTPUT_CSV, index=False)

OUTPUT_META.write_text(
    json.dumps(metadata, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("MODELO: yield-v1")
print("PARCELAS:", len(df))
print("COLUMNAS:", len(df.columns))
print("TERCIL 1:", round(q1, 6))
print("TERCIL 2:", round(q2, 6))

print("\nNIVELES RELATIVOS:")
print(df["nivel_relativo"].value_counts().to_string())

print("\nPRIORIDADES:")
print(df["prioridad_revision"].value_counts().to_string())

print("\nALERTAS OOD:", int(df["alerta_ood"].sum()))

print("\nPARCELAS CON PRIORIDAD ALTA:")
print(
    df.loc[
        df["prioridad_revision"] == "Prioridad alta de revision",
        ["parcel_id", "rendimiento_pred_t_ha", "score_ood"],
    ].to_string(index=False)
)

print("\nRESULTADOS:", OUTPUT_DIR)
print("No se modificaron los archivos originales.")
