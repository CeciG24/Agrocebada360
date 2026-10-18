import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

# Ubicar la carpeta ml del repositorio
BASE_DIR = Path(__file__).resolve().parent
ML_DIR = BASE_DIR.parent

# Permitir importar los modulos del Rol 2
sys.path.insert(0, str(ML_DIR))

from src.data import load

# Cargar modelo y datos
ruta_modelo = ML_DIR / "artifacts" / "baseline_v0.joblib"

artifact = joblib.load(ruta_modelo)
features = artifact["features"]
model = artifact["model"]

train, evaluation = load()

# Preprocesamiento usado por baseline_v0
imputer = model.named_steps["simpleimputer"]
scaler = model.named_steps["standardscaler"]

X_eval = scaler.transform(
    imputer.transform(evaluation[features].to_numpy())
)

parcelas = ["AGC_029", "AGC_142", "AGC_154"]

print("COMPARACION CON LA DISTRIBUCION DE ENTRENAMIENTO")

for parcel_id in parcelas:
    posiciones = np.where(
        evaluation["parcel_id"].astype(str).to_numpy() == parcel_id
    )[0]

    if len(posiciones) == 0:
        print(f"No se encontro {parcel_id}")
        continue

    i = posiciones[0]
    z = X_eval[i]
    indices = np.argsort(np.abs(z))[::-1][:5]

    print(f"\n{'=' * 65}")
    print(f"PARCELA: {parcel_id}")

    for j in indices:
        variable = features[j]
        valores = pd.to_numeric(train[variable], errors="coerce").dropna()
        valor = pd.to_numeric(
            pd.Series([evaluation.iloc[i][variable]]),
            errors="coerce"
        ).iloc[0]

        if valores.empty or pd.isna(valor):
            print(f"{variable}: valor ausente o sin datos de referencia")
            continue

        p05 = valores.quantile(0.05)
        p50 = valores.quantile(0.50)
        p95 = valores.quantile(0.95)

        if valor < valores.min() or valor > valores.max():
            estado = "FUERA DEL RANGO OBSERVADO"
        elif valor < p05 or valor > p95:
            estado = "EXTREMO RESPECTO AL 90% CENTRAL"
        else:
            estado = "DENTRO DEL 90% CENTRAL"

        print(
            f"{variable}\n"
            f"  Parcela={valor:.5g} | "
            f"Min={valores.min():.5g} | "
            f"P05={p05:.5g} | "
            f"Mediana={p50:.5g} | "
            f"P95={p95:.5g} | "
            f"Max={valores.max():.5g}\n"
            f"  Diagnostico: {estado}"
        )