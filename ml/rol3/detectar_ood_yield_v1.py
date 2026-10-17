
"""P3.8 - Deteccion OOD para el modelo definitivo yield-v1."""

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

ML_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ML_DIR))

from src.data import load
from src.provenance import data_version

MODEL_PATH = ML_DIR / "models" / "yield_model_v1.joblib"
SCHEMA_PATH = ML_DIR / "models" / "feature_schema.json"
PRED_PATH = ML_DIR / "results" / "predictions_raw.csv"
OUTPUT_DIR = ML_DIR / "results" / "rol3" / "ood_yield_v1"

model = joblib.load(MODEL_PATH)
schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

features = list(schema["features"])

assert schema["model_version"] == "yield-v1"
assert schema["data_version"] == data_version()
assert len(features) == 30
assert features == list(model.feature_names_in_)

train, evaluation = load()
pred = pd.read_csv(PRED_PATH)

assert len(train) == 138
assert len(evaluation) == 59
assert len(pred) == 59
assert (pred["model_version"] == "yield-v1").all()

for name, df in [
    ("entrenamiento", train),
    ("evaluacion", evaluation),
    ("predicciones", pred)
]:
    if df["parcel_id"].isna().any():
        raise ValueError(f"IDs faltantes en {name}")
    if df["parcel_id"].duplicated().any():
        raise ValueError(f"IDs duplicados en {name}")

if set(pred["parcel_id"]) != set(evaluation["parcel_id"]):
    raise ValueError("Las parcelas de evaluacion no coinciden")

# Aplicar exactamente el preprocesamiento del modelo definitivo.
imputer = model.named_steps["simpleimputer"]
scaler = model.named_steps["standardscaler"]

X_train = scaler.transform(imputer.transform(train[features]))
X_eval = scaler.transform(imputer.transform(evaluation[features]))

if not np.isfinite(X_train).all() or not np.isfinite(X_eval).all():
    raise ValueError("Hay valores no finitos en las variables")

# Entrenar exclusivamente con las 138 parcelas de entrenamiento.
detector = IsolationForest(
    n_estimators=300,
    contamination="auto",
    random_state=42
)

detector.fit(X_train)

scores_train = detector.score_samples(X_train)
scores_eval = detector.score_samples(X_eval)

# El umbral se calcula exclusivamente con entrenamiento.
threshold = float(np.percentile(scores_train, 5))
alerts = scores_eval < threshold

ood = pd.DataFrame({
    "parcel_id": evaluation["parcel_id"].astype(str).to_numpy(),
    "score_ood": scores_eval,
    "alerta_ood": alerts
})

ood["umbral_ood"] = threshold
ood["interpretacion"] = np.where(
    ood["alerta_ood"],
    "Revisar caracteristicas climaticas inusuales",
    "Sin alerta OOD detectada"
)

result = pred.merge(
    ood,
    on="parcel_id",
    how="left",
    validate="one_to_one"
)

if len(result) != 59 or result["score_ood"].isna().any():
    raise ValueError("Error al combinar alertas y predicciones")

if not np.array_equal(
    result["alerta_ood"].to_numpy(),
    result["score_ood"].to_numpy() < threshold
):
    raise ValueError("Las alertas no coinciden con el umbral")

metadata = {
    "model_version": "yield-v1",
    "data_version": schema["data_version"],
    "model_sha256": schema["model_sha256"],
    "method": "IsolationForest",
    "n_estimators": 300,
    "contamination": "auto",
    "random_state": 42,
    "n_features": len(features),
    "n_train": len(train),
    "n_evaluation": len(evaluation),
    "threshold_method": "Percentil 5 de score_samples en entrenamiento",
    "threshold": threshold,
    "n_alerts": int(alerts.sum()),
    "n_without_alert": int((~alerts).sum()),
    "limitations": [
        "El umbral es operativo y no garantiza 5% de alertas futuras.",
        "Las alertas no demuestran que una prediccion sea incorrecta.",
        "El detector utiliza exclusivamente las 30 variables climaticas.",
        "La seguridad temporal de las variables requiere verificacion."
    ]
}

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

result.to_csv(
    OUTPUT_DIR / "predicciones_ood_yield_v1.csv",
    index=False
)

(OUTPUT_DIR / "metadata_ood_yield_v1.json").write_text(
    json.dumps(metadata, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("MODELO:", schema["model_version"])
print("VARIABLES:", len(features))
print("ENTRENAMIENTO:", len(train))
print("EVALUACION:", len(evaluation))
print("UMBRAL OOD:", round(threshold, 8))
print("ALERTAS OOD:", int(alerts.sum()))
print("SIN ALERTA:", int((~alerts).sum()))

print("\nPARCELAS CON ALERTA:")
print(
    result.loc[
        result["alerta_ood"],
        ["parcel_id", "rendimiento_pred_t_ha", "score_ood"]
    ].to_string(index=False)
)

print("\nARCHIVOS GENERADOS EN:", OUTPUT_DIR)
print("No se modificaron las predicciones ni la clasificacion anterior.")
