import math
import numpy as np
import pandas as pd

from pathlib import Path


# =====================================================
# 1. Cargar archivos existentes
# =====================================================

BASE_DIR = Path(__file__).resolve().parent
ML_DIR = BASE_DIR.parent
RESULTADOS_DIR = ML_DIR / "results" / "rol3"

ruta_oof = ML_DIR / "results" / "oof" / "E5_fusion__ridge.csv"
ruta_pred = ML_DIR / "results" / "predictions_raw.csv"

oof = pd.read_csv(ruta_oof)
pred = pd.read_csv(ruta_pred)

print("Filas OOF:", len(oof))
print("Predicciones de evaluacion:", len(pred))


# =====================================================
# 2. Calcular errores de validacion
# =====================================================

residuos = np.abs(oof["y"] - oof["oof"])
n = len(residuos)

if n == 0 or residuos.isna().any():
    raise ValueError("Hay residuos vacios o datos insuficientes.")

mae = np.mean(residuos)
rmse = np.sqrt(np.mean((oof["y"] - oof["oof"]) ** 2))

# Intervalo exploratorio del 90 %
alpha = 0.10

# Cuantil con correccion de muestra finita
indice = math.ceil((n + 1) * (1 - alpha)) - 1
indice = min(indice, n - 1)

margen = np.sort(residuos.to_numpy())[indice]


# =====================================================
# 3. Verificar identificadores y predicciones
# =====================================================

if pred["parcel_id"].duplicated().any():
    raise ValueError("Hay parcel_id duplicados en predictions_raw.csv.")

if oof["parcel_id"].duplicated().any():
    raise ValueError("Hay parcel_id duplicados en el archivo OOF.")

if pred["rendimiento_pred_t_ha"].isna().any():
    raise ValueError("Hay predicciones faltantes.")

if pred["model_version"].nunique() != 1:
    raise ValueError("Se encontraron varias versiones de modelo.")

if pred["model_version"].iloc[0] != "baseline_v0":
    raise ValueError("El archivo no corresponde a baseline_v0.")


# =====================================================
# 4. Crear intervalos para las 59 parcelas
# =====================================================

resultado = pred.copy()

resultado["margen_error_exploratorio_t_ha"] = margen

resultado["limite_inferior_t_ha"] = (
    resultado["rendimiento_pred_t_ha"] - margen
)

resultado["limite_superior_t_ha"] = (
    resultado["rendimiento_pred_t_ha"] + margen
)

resultado["nivel_nominal_intervalo"] = "90% exploratorio"

resultado["metodo_intervalo"] = (
    "Residuo absoluto OOF E5_fusion__ridge; "
    "correccion de muestra finita"
)


# =====================================================
# 5. Guardar archivo nuevo
# =====================================================

salida = RESULTADOS_DIR / "predicciones_intervalos_rol3.csv"

resultado.to_csv(salida, index=False)


# =====================================================
# 6. Mostrar resumen
# =====================================================

print("\nRESULTADOS DE VALIDACION")
print("MAE OOF:", round(mae, 4), "t/ha")
print("RMSE OOF:", round(rmse, 4), "t/ha")
print("Margen exploratorio:", round(margen, 4), "t/ha")

print("\nINTERVALOS GENERADOS")
print("Parcelas:", len(resultado))
print("Valores faltantes:", int(resultado.isna().sum().sum()))

print("\nPrimeras diez parcelas:")
print(
    resultado[
        [
            "parcel_id",
            "rendimiento_pred_t_ha",
            "limite_inferior_t_ha",
            "limite_superior_t_ha"
        ]
    ].head(10).to_string(index=False)
)

print("\nArchivo guardado:", salida)
print("Las predicciones originales no fueron modificadas.")
