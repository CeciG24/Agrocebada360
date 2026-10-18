
import joblib
import numpy as np
import pandas as pd
import shap
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ML_DIR = BASE_DIR.parent

# Permitir importar los modulos del Rol 2
sys.path.insert(0, str(ML_DIR))

from src.data import load, families, columns_for
from src.models import zoo

# Rutas independientes del directorio de ejecucion
RESULTS = ML_DIR / "results" / "rol3"
ARTIFACTS = ML_DIR / "artifacts" / "rol3"

RESULTS.mkdir(parents=True, exist_ok=True)
ARTIFACTS.mkdir(parents=True, exist_ok=True)

print("Cargando datos...")
train, evaluation = load()

# Recuperar exactamente las variables de X0_municipio
fam = families(train)
features = columns_for("X0_municipio", fam)

print("Variables utilizadas:", len(features))
print(features)

# Entrenar Ridge con la configuracion oficial del proyecto
X_train = train[features].to_numpy()
y_train = train["rendimiento_t_ha"].to_numpy()
X_eval = evaluation[features].to_numpy()

model = zoo()["ridge"]()
model.fit(X_train, y_train)

# Guardar un artefacto independiente
joblib.dump(
    {
        "model": model,
        "features": features,
        "version": "X0_municipio_ridge_rol3"
    },
    ARTIFACTS / "x0_municipio_ridge_rol3.joblib"
)

# Aplicar las transformaciones aprendidas por el modelo
imputer = model.named_steps["simpleimputer"]
scaler = model.named_steps["standardscaler"]
regressor = model.steps[-1][1]

X_train_scaled = scaler.transform(imputer.transform(X_train))
X_eval_scaled = scaler.transform(imputer.transform(X_eval))

# Usar las 138 parcelas como referencia SHAP
masker = shap.maskers.Independent(
    X_train_scaled,
    max_samples=len(X_train_scaled)
)
explainer = shap.LinearExplainer(regressor, masker)
explanation = explainer(X_eval_scaled)

# Predicciones del modelo entrenado con todos los datos de entrenamiento
predictions = model.predict(X_eval)

# Importancia global de las variables
importance = pd.DataFrame({
    "variable": features,
    "importancia_shap_media": np.abs(explanation.values).mean(axis=0),
    "efecto_shap_medio": explanation.values.mean(axis=0)
}).sort_values("importancia_shap_media", ascending=False)

importance.to_csv(
    RESULTS / "shap_importancia_x0_municipio_ridge.csv",
    index=False
)

# Explicaciones individuales por parcela
individual = pd.DataFrame(
    explanation.values,
    columns=features
)
individual.insert(0, "parcel_id", evaluation["parcel_id"].to_numpy())
individual.insert(1, "prediccion_modelo", predictions)

base_values = np.asarray(explanation.base_values)
if base_values.ndim == 0:
    base_values = np.repeat(float(base_values), len(evaluation))

individual.insert(2, "valor_base_shap", base_values)

individual.to_csv(
    RESULTS / "shap_valores_x0_municipio_ridge.csv",
    index=False
)

# Gráfica global
shap.plots.beeswarm(
    explanation,
    max_display=min(20, len(features)),
    show=False
)
plt.tight_layout()
plt.savefig(
    RESULTS / "shap_resumen_x0_municipio_ridge.png",
    dpi=180,
    bbox_inches="tight"
)
plt.close()

# Comprobación de coherencia entre SHAP y predicción
suma_shap = (
    base_values + explanation.values.sum(axis=1)
)
max_difference = float(np.max(np.abs(suma_shap - predictions)))

print("\nAnalisis SHAP terminado.")
print("Parcelas de entrenamiento:", len(train))
print("Parcelas explicadas:", len(evaluation))
print("Variables explicadas:", len(features))
print("RMSE OOF previo de referencia: aproximadamente 0.507 t/ha")
print("Diferencia maxima entre prediccion y suma SHAP:",
      round(max_difference, 8))

print("\nImportancia SHAP:")
print(importance.round(5).to_string(index=False))

print("\nArchivos generados:")
print(RESULTS / "shap_importancia_x0_municipio_ridge.csv")
print(RESULTS / "shap_valores_x0_municipio_ridge.csv")
print(RESULTS / "shap_resumen_x0_municipio_ridge.png")
print(ARTIFACTS / "x0_municipio_ridge_rol3.joblib")