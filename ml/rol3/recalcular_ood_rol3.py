import joblib
import numpy as np
import pandas as pd

from pathlib import Path
from sklearn.ensemble import IsolationForest
import sys

BASE_DIR = Path(__file__).resolve().parent
ML_DIR = BASE_DIR.parent

sys.path.insert(0, str(ML_DIR))

from src.data import load

# =====================================================
# 1. Cargar el modelo y los datos originales
# =====================================================

# Directorios del repositorio oficial
RESULTADOS_DIR = ML_DIR / "results" / "rol3"
RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)

ruta_modelo = ML_DIR / "artifacts" / "baseline_v0.joblib"
ruta_predicciones = ML_DIR / "results" / "predictions_raw.csv"

artifact = joblib.load(ruta_modelo)
model = artifact["model"]
features = artifact["features"]

train, evaluation = load()

predicciones = pd.read_csv(ruta_predicciones)

print("Entrenamiento:", len(train))
print("Parcelas de evaluacion:", len(evaluation))
print("Predicciones originales:", len(predicciones))


# =====================================================
# 2. Aplicar el preprocesamiento del modelo
# =====================================================

imputer = model.named_steps["simpleimputer"]
scaler = model.named_steps["standardscaler"]

X_train = scaler.transform(
    imputer.transform(train[features].to_numpy())
)

X_eval = scaler.transform(
    imputer.transform(evaluation[features].to_numpy())
)


# =====================================================
# 3. Ajustar el detector OOD solo con entrenamiento
# =====================================================

detector = IsolationForest(
    n_estimators=300,
    contamination="auto",
    random_state=42
)

detector.fit(X_train)

scores_train = detector.score_samples(X_train)
scores_eval = detector.score_samples(X_eval)

# Umbral del 5 % calculado exclusivamente en entrenamiento
umbral = np.percentile(scores_train, 5)

alertas = scores_eval < umbral


# =====================================================
# 4. Construir tabla de alertas OOD
# =====================================================

ood = pd.DataFrame({
    "parcel_id": evaluation["parcel_id"].astype(str).to_numpy(),
    "score_ood": scores_eval,
    "alerta_ood": alertas
})

ood["interpretacion"] = np.where(
    ood["alerta_ood"],
    "Revisar caracteristicas inusuales",
    "Sin alerta OOD detectada"
)

# Conservar las predicciones existentes
resultado = predicciones.merge(
    ood,
    on="parcel_id",
    how="left",
    validate="one_to_one"
)

if resultado["score_ood"].isna().any():
    raise ValueError(
        "Hay parcelas sin puntaje OOD. Revisa los identificadores."
    )

# Guardar el umbral para documentar el criterio
resultado["umbral_ood"] = umbral

ruta_salida = RESULTADOS_DIR / "predicciones_con_alertas_ood.csv"
if ruta_salida.exists():
    raise FileExistsError(
        f"El archivo ya existe y no se sobrescribira: {ruta_salida}"
    )
resultado.to_csv(ruta_salida, index=False)


# =====================================================
# 5. Actualizar la clasificación relativa
# =====================================================

ruta_clasificacion = RESULTADOS_DIR / "predicciones_clasificadas_rol3.csv"
if ruta_clasificacion.exists():
    clasificacion = pd.read_csv(ruta_clasificacion)

    columnas_actualizadas = [
        "score_ood",
        "alerta_ood",
        "interpretacion",
        "umbral_ood"
    ]

    # Eliminar las versiones anteriores de esas columnas
    clasificacion = clasificacion.drop(
        columns=[
            c for c in columnas_actualizadas
            if c in clasificacion.columns
        ],
        errors="ignore"
    )

    clasificacion = clasificacion.merge(
        ood.assign(umbral_ood=umbral),
        on="parcel_id",
        how="left",
        validate="one_to_one"
    )

    if clasificacion["score_ood"].isna().any():
        raise ValueError(
            "La clasificacion tiene parcelas sin puntaje OOD."
        )

    clasificacion.to_csv(ruta_clasificacion, index=False)

    print("Clasificacion actualizada:", ruta_clasificacion)


# =====================================================
# 6. Mostrar resumen y validar resultados
# =====================================================

print("\nUMBRAL OOD:", round(umbral, 6))
print("Parcelas evaluadas:", len(resultado))
print("Parcelas con alerta OOD:", int(alertas.sum()))
print("Parcelas sin alerta OOD:", int((~alertas).sum()))
print("Puntajes faltantes:", int(resultado["score_ood"].isna().sum()))

print("\nParcelas con alerta:")
print(
    resultado.loc[
        resultado["alerta_ood"],
        ["parcel_id", "rendimiento_pred_t_ha", "score_ood"]
    ].to_string(index=False)
)

print("\nArchivo OOD guardado:", ruta_salida)
print("\nProceso terminado.")