
import joblib
import numpy as np
import pandas as pd
import shap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import sys
from pathlib import Path

# Directorios del repositorio
BASE_DIR = Path(__file__).resolve().parent
ML_DIR = BASE_DIR.parent

# Permitir importar los modulos del Rol 2
sys.path.insert(0, str(ML_DIR))

from src.data import load

# Rutas de entrada y salida
ARTIFACT = ML_DIR / "artifacts" / "baseline_v0.joblib"
RESULTS = ML_DIR / "results" / "rol3"
RESULTS.mkdir(parents=True, exist_ok=True)

print("Cargando modelo y datos...")
artifact = joblib.load(ARTIFACT)
model = artifact["model"]
features = artifact["features"]

train, evaluation = load()

# Preparar los datos con las mismas transformaciones del modelo
X_train = train[features].to_numpy()
X_eval = evaluation[features].to_numpy()

imputer = model.named_steps["simpleimputer"]
scaler = model.named_steps["standardscaler"]
regressor = model.steps[-1][1]

X_train_imputed = imputer.transform(X_train)
X_eval_imputed = imputer.transform(X_eval)

X_train_scaled = scaler.transform(X_train_imputed)
X_eval_scaled = scaler.transform(X_eval_imputed)

print("Calculando valores SHAP...")
explainer = shap.LinearExplainer(regressor, X_train_scaled)
explanation = explainer(X_eval_scaled)

# Importancia global: promedio del valor absoluto SHAP
importance = pd.DataFrame({
    "variable": features,
    "importancia_shap_media": np.abs(explanation.values).mean(axis=0),
    "efecto_shap_medio": explanation.values.mean(axis=0)
})

importance = importance.sort_values(
    "importancia_shap_media", ascending=False
)

importance.to_csv(
    RESULTS / "shap_importancia_baseline_v0.csv",
    index=False
)

# Explicaciones individuales para cada parcela evaluada
individual = pd.DataFrame(explanation.values, columns=features)
individual.insert(0, "parcel_id", evaluation["parcel_id"].to_numpy())
individual.insert(1, "prediccion_modelo",
                  model.predict(X_eval).round(4))
individual.insert(2, "valor_base_shap",
                  float(np.asarray(explanation.base_values).mean()))

individual.to_csv(
    RESULTS / "shap_valores_baseline_v0.csv",
    index=False
)

# Gráfica global de importancia SHAP
plot_data = shap.Explanation(
    values=explanation.values,
    base_values=explanation.base_values,
    data=X_eval_imputed,
    feature_names=features
)

shap.plots.beeswarm(plot_data, max_display=20, show=False)
plt.tight_layout()
plt.savefig(
    RESULTS / "shap_resumen_baseline_v0.png",
    dpi=180,
    bbox_inches="tight"
)
plt.close()

print("\nAnalisis SHAP terminado.")
print("Modelo:", artifact.get("version", "sin version"))
print("Parcelas explicadas:", len(evaluation))
print("Variables analizadas:", len(features))
print("\nTop 15 variables por importancia SHAP:")
print(importance.head(15).round(5).to_string(index=False))
print("\nArchivos guardados:")
print(RESULTS / "shap_importancia_baseline_v0.csv")
print(RESULTS / "shap_valores_baseline_v0.csv")
print(RESULTS / "shap_resumen_baseline_v0.png")