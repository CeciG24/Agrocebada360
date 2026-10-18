import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import sys

ML_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ML_DIR))

from src.data import load
from src.provenance import data_version

MODEL_PATH = ML_DIR / "models" / "yield_model_v1.joblib"
SCHEMA_PATH = ML_DIR / "models" / "feature_schema.json"
RESULTS = ML_DIR / "results" / "rol3" / "shap_yield_v1"

model = joblib.load(MODEL_PATH)
schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

features = list(schema["features"])

assert schema["model_version"] == "yield-v1"
assert schema["data_version"] == data_version()
assert len(features) == 30
assert features == list(model.feature_names_in_)

train, evaluation = load()

X_train = train[features]
X_eval = evaluation[features]

imputer = model.named_steps["simpleimputer"]
scaler = model.named_steps["standardscaler"]
regressor = model.named_steps["ridgecv"]

X_train_scaled = scaler.transform(imputer.transform(X_train))
X_eval_scaled = scaler.transform(imputer.transform(X_eval))

print("Calculando SHAP del modelo yield-v1...")

masker = shap.maskers.Independent(
    X_train_scaled,
    max_samples=len(X_train_scaled)
)

explainer = shap.LinearExplainer(regressor, masker)
explanation = explainer(X_eval_scaled)

values = np.asarray(explanation.values)
base_values = np.broadcast_to(
    np.asarray(explanation.base_values),
    (len(evaluation),)
)

predictions = model.predict(X_eval)
reconstructed = base_values + values.sum(axis=1)
max_error = float(np.max(np.abs(predictions - reconstructed)))

print("Parcelas:", len(evaluation))
print("Variables:", len(features))
print("Error maximo de aditividad:", max_error)

if len(evaluation) != 59:
    raise ValueError("Se esperaban 59 parcelas de evaluacion")

if max_error > 1e-8:
    raise ValueError("SHAP no reconstruye las predicciones")

importance = pd.DataFrame({
    "variable": features,
    "importancia_shap_media_t_ha": np.abs(values).mean(axis=0),
    "efecto_shap_medio_t_ha": values.mean(axis=0)
}).sort_values("importancia_shap_media_t_ha", ascending=False)

individual = pd.DataFrame(values, columns=features)
individual.insert(0, "parcel_id", evaluation["parcel_id"].to_numpy())
individual.insert(1, "prediccion_t_ha", predictions)
individual.insert(2, "valor_base_shap_t_ha", base_values)
individual.insert(3, "prediccion_reconstruida_t_ha", reconstructed)

metadata = {
    "model_version": "yield-v1",
    "data_version": schema["data_version"],
    "model_sha256": schema["model_sha256"],
    "method": "shap.LinearExplainer",
    "background": "138 parcelas de entrenamiento, variables imputadas y escaladas",
    "n_train": len(train),
    "n_evaluation": len(evaluation),
    "n_features": len(features),
    "max_additivity_error_t_ha": max_error,
    "unit": "t/ha",
    "interpretation": "Asociaciones predictivas, no efectos causales"
}

RESULTS.mkdir(parents=True, exist_ok=True)

importance.to_csv(
    RESULTS / "shap_importancia_yield_v1.csv",
    index=False
)

individual.to_csv(
    RESULTS / "shap_valores_yield_v1.csv",
    index=False
)

(RESULTS / "shap_metadata_yield_v1.json").write_text(
    json.dumps(metadata, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

plot_data = shap.Explanation(
    values=values,
    base_values=base_values,
    data=X_eval_scaled,
    feature_names=features
)

shap.plots.beeswarm(plot_data, max_display=20, show=False)
plt.tight_layout()
plt.savefig(
    RESULTS / "shap_resumen_yield_v1.png",
    dpi=180,
    bbox_inches="tight"
)
plt.close()

print("\nTOP 15 VARIABLES:")
print(importance.head(15).round(5).to_string(index=False))
print("\nArchivos generados en:", RESULTS)
