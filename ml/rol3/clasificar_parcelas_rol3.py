
from pathlib import Path
import numpy as np
import pandas as pd

# =====================================================
# 1. Cargar las predicciones y las alertas OOD
# =====================================================

# Ubicar la carpeta de resultados del Rol 3
BASE_DIR = Path(__file__).resolve().parent
RESULTADOS_DIR = BASE_DIR.parent / "results" / "rol3"

ruta_ood = RESULTADOS_DIR / "predicciones_con_alertas_ood.csv"
ruta_salida = RESULTADOS_DIR / "predicciones_clasificadas_rol3.csv"

df = pd.read_csv(ruta_ood)

columnas_requeridas = [
    "parcel_id",
    "rendimiento_pred_t_ha",
    "model_version",
    "score_ood",
    "alerta_ood",
    "interpretacion",
    "umbral_ood",
]

faltantes = [c for c in columnas_requeridas if c not in df.columns]

if faltantes:
    raise ValueError(f"Faltan columnas requeridas: {faltantes}")

if df["parcel_id"].duplicated().any():
    raise ValueError("Hay identificadores de parcela duplicados.")

if df["rendimiento_pred_t_ha"].isna().any():
    raise ValueError("Hay rendimientos predichos faltantes.")

# Normalizar los valores booleanos por seguridad.
if df["alerta_ood"].dtype != bool:
    valores = df["alerta_ood"].astype(str).str.lower()
    if not valores.isin(["true", "false"]).all():
        raise ValueError("La columna alerta_ood tiene valores inválidos.")
    df["alerta_ood"] = valores.eq("true")

# =====================================================
# 2. Clasificar el rendimiento relativo
# =====================================================
# Se utilizan terciles de las predicciones de evaluación.
# Son categorías relativas, NO umbrales agronómicos.

q1 = df["rendimiento_pred_t_ha"].quantile(1 / 3)
q2 = df["rendimiento_pred_t_ha"].quantile(2 / 3)

def clasificar_rendimiento(valor):
    if valor <= q1:
        return "Bajo relativo"
    elif valor <= q2:
        return "Intermedio relativo"
    return "Alto relativo"

df["nivel_relativo"] = df["rendimiento_pred_t_ha"].apply(
    clasificar_rendimiento
)

# =====================================================
# 3. Asignar prioridades de revisión
# =====================================================

def asignar_prioridad(fila):
    bajo = fila["nivel_relativo"] == "Bajo relativo"
    ood = fila["alerta_ood"]

    if bajo and ood:
        return "Prioridad alta de revision"
    elif bajo:
        return "Revisar rendimiento estimado"
    elif ood:
        return "Revisar caracteristicas inusuales"
    return "Sin alerta combinada"

df["prioridad_revision"] = df.apply(
    asignar_prioridad,
    axis=1
)

# =====================================================
# 4. Ordenar columnas y guardar
# =====================================================

columnas = [
    "parcel_id",
    "rendimiento_pred_t_ha",
    "model_version",
    "nivel_relativo",
    "prioridad_revision",
    "score_ood",
    "alerta_ood",
    "interpretacion",
    "umbral_ood",
]

df[columnas].to_csv(ruta_salida, index=False)

# =====================================================
# 5. Mostrar resumen
# =====================================================

print("Parcelas clasificadas:", len(df))
print("\nNiveles relativos:")
print(df["nivel_relativo"].value_counts().to_string())

print("\nPrioridades:")
print(df["prioridad_revision"].value_counts().to_string())

print("\nAlertas OOD:", int(df["alerta_ood"].sum()))
print("Archivo guardado:", ruta_salida)