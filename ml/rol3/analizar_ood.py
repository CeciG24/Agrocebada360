import sys
from pathlib import Path

import joblib
import numpy as np

# Localizar la carpeta ml del repositorio
BASE_DIR = Path(__file__).resolve().parent
ML_DIR = BASE_DIR.parent

# Permitir importar los módulos del Rol 2
sys.path.insert(0, str(ML_DIR))

from src.data import load

# Cargar modelo y datos
ruta_modelo = ML_DIR / "artifacts" / "baseline_v0.joblib"
artifact = joblib.load(ruta_modelo)
model = artifact["model"]
features = artifact["features"]

train, evaluation = load()

# Aplicar el mismo preprocesamiento del modelo
imputer = model.named_steps["simpleimputer"]
scaler = model.named_steps["standardscaler"]

X_eval = scaler.transform(
    imputer.transform(evaluation[features].to_numpy())
)

# Parcelas identificadas como atípicas
ids = ["AGC_029", "AGC_142", "AGC_154"]

print("CARACTERISTICAS MAS EXTREMAS POR PARCELA")
print("z indica distancia aproximada respecto al entrenamiento.")

for parcel_id in ids:
    matches = np.where(
        evaluation["parcel_id"].astype(str).to_numpy() == parcel_id
    )[0]

    if len(matches) == 0:
        print(f"\nNo se encontro: {parcel_id}")
        continue

    i = matches[0]
    z = X_eval[i]
    indices = np.argsort(np.abs(z))[::-1][:8]

    print(f"\n{parcel_id}")

    for j in indices:
        print(f"{features[j]} | z={z[j]:.3f}")