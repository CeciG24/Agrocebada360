from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
MODELS = ROOT / "models"
OUT = RESULTS / "rol3" / "validacion_final_yield_v1"

errores = []
verificaciones = {}

def comprobar(nombre, condicion, detalle=""):
    correcto = bool(condicion)
    verificaciones[nombre] = {
        "correcto": correcto,
        "detalle": detalle
    }
    print(("OK" if correcto else "ERROR"), "-", nombre, detalle)
    if not correcto:
        errores.append(nombre)

def cargar(ruta):
    return pd.read_csv(RESULTS / ruta)

def alinear(nombre, df, oficial):
    comprobar(
        nombre + ": 59 filas",
        len(df) == 59
    )
    comprobar(
        nombre + ": IDs unicos",
        df["parcel_id"].is_unique
    )
    comprobar(
        nombre + ": mismas parcelas",
        set(df["parcel_id"]) == set(oficial["parcel_id"])
    )
    return oficial[["parcel_id"]].merge(
        df, on="parcel_id", how="left", validate="one_to_one"
    )

def iguales(a, b, tolerancia=1e-8):
    return np.allclose(
        np.asarray(a, dtype=float),
        np.asarray(b, dtype=float),
        atol=tolerancia,
        rtol=0
    )

config = json.loads(
    (RESULTS / "final_model_config.json").read_text(
        encoding="utf-8-sig"
    )
)

features = config["features"]

comprobar(
    "Version oficial",
    config["model_version"] == "yield-v1"
)
comprobar(
    "Experimento oficial",
    config["experiment"] == "E4_clima"
)
comprobar(
    "30 variables climaticas",
    len(features) == 30 and len(set(features)) == 30
)

modelo = MODELS / "yield_model_v1.joblib"

comprobar(
    "Modelo congelado existente",
    modelo.is_file()
)

if modelo.is_file():
    sha = hashlib.sha256(modelo.read_bytes()).hexdigest()
    comprobar(
        "SHA256 del modelo congelado",
        sha == "f624c2324e418b642a41c98bed53977fa4eb9fa3e210c0341d239592b4bc33d6",
        sha
    )

oficial = cargar("predictions_raw.csv")

comprobar("59 predicciones oficiales", len(oficial) == 59)
comprobar("IDs oficiales unicos", oficial["parcel_id"].is_unique)
comprobar(
    "Version en predicciones",
    oficial["model_version"].eq("yield-v1").all()
)

intervalos = alinear(
    "Intervalos",
    cargar("rol3/intervalos_yield_v1/predicciones_intervalos_yield_v1.csv"),
    oficial
)

ood = alinear(
    "OOD",
    cargar("rol3/ood_yield_v1/predicciones_ood_yield_v1.csv"),
    oficial
)

riesgo = alinear(
    "Riesgo",
    cargar("rol3/riesgo_yield_v1/predicciones_riesgo_yield_v1.csv"),
    oficial
)

for nombre, df in [
    ("Intervalos", intervalos),
    ("OOD", ood),
    ("Riesgo", riesgo)
]:
    comprobar(
        nombre + ": version yield-v1",
        df["model_version"].eq("yield-v1").all()
    )
    comprobar(
        nombre + ": predicciones oficiales",
        iguales(
            df["rendimiento_pred_t_ha"],
            oficial["rendimiento_pred_t_ha"]
        )
    )

comprobar(
    "Intervalos: limites inferiores",
    iguales(
        intervalos["limite_inferior_t_ha"],
        intervalos["rendimiento_pred_t_ha"]
        - intervalos["margen_exploratorio_t_ha"]
    )
)

comprobar(
    "Intervalos: limites superiores",
    iguales(
        intervalos["limite_superior_t_ha"],
        intervalos["rendimiento_pred_t_ha"]
        + intervalos["margen_exploratorio_t_ha"]
    )
)

comprobar(
    "Intervalos: nivel nominal",
    intervalos["nivel_nominal"].eq("90% exploratorio").all()
)

comprobar(
    "Riesgo: alertas OOD consistentes",
    riesgo["alerta_ood"].astype(str).tolist()
    == ood["alerta_ood"].astype(str).tolist()
)

for columna in [
    "score_ood", "umbral_ood",
    "limite_inferior_t_ha",
    "limite_superior_t_ha",
    "margen_exploratorio_t_ha"
]:
    fuente = ood if columna in ["score_ood", "umbral_ood"] else intervalos
    comprobar(
        "Riesgo: " + columna,
        iguales(riesgo[columna], fuente[columna])
    )

shap = alinear(
    "SHAP",
    cargar("rol3/shap_yield_v1/shap_valores_yield_v1.csv"),
    oficial
)

comprobar(
    "SHAP: 30 contribuciones",
    all(f in shap.columns for f in features)
)

if all(f in shap.columns for f in features):
    reconstruccion = (
        shap["valor_base_shap_t_ha"].to_numpy()
        + shap[features].sum(axis=1).to_numpy()
    )

    comprobar(
        "SHAP: aditividad",
        iguales(
            reconstruccion,
            shap["prediccion_reconstruida_t_ha"]
        )
    )

comprobar(
    "SHAP: reconstruccion de predicciones oficiales",
    iguales(
        shap["prediccion_reconstruida_t_ha"],
        oficial["rendimiento_pred_t_ha"]
    )
)

importancia = cargar(
    "rol3/shap_yield_v1/shap_importancia_yield_v1.csv"
)

comprobar(
    "SHAP: 30 variables de importancia",
    len(importancia) == 30
    and set(importancia["variable"]) == set(features)
)

graficas = [
    "01_predicho_vs_real.png",
    "02_residuos.png",
    "03_importancia_shap.png",
    "04_rmse_temporal_early_v2.png"
]

for nombre in graficas:
    ruta = RESULTS / "rol3/graficas_yield_v1" / nombre
    comprobar(
        "Grafica: " + nombre,
        ruta.is_file() and ruta.stat().st_size > 1000
    )

OUT.mkdir(parents=True, exist_ok=True)

reporte = {
    "modelo": "yield-v1",
    "experimento": "E4_clima",
    "parcelas_prediccion": len(oficial),
    "variables": len(features),
    "verificaciones": verificaciones,
    "errores": errores,
    "resultado": "APROBADO" if not errores else "RECHAZADO"
}

ruta_reporte = OUT / "reporte_validacion_P3_12.json"

ruta_reporte.write_text(
    json.dumps(reporte, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print()
print("RESULTADO FINAL:", reporte["resultado"])
print("VERIFICACIONES:", len(verificaciones))
print("ERRORES:", len(errores))
print("REPORTE:", ruta_reporte)

if errores:
    raise SystemExit(1)
