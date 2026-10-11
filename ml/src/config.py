"""Configuración central del protocolo (P2.2). Cambiar aquí, no en los notebooks."""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2] 
ML_DIR = Path(__file__).resolve().parents[1]

# Carpeta DATASET_RETO_AGRO_2026_LIMPIO (override con variable de entorno CEBADA_DATA)
DATA_ROOT = Path(os.environ.get("CEBADA_DATA", PROJECT_ROOT / "data/DATASET_RETO_AGRO_2026_LIMPIO"))
RESULTS = ML_DIR / "results"
ARTIFACTS = ML_DIR / "artifacts"

SEED = 42
N_SPLITS = 5          # folds
N_REPEATS = 10        # repeticiones de CV (usar 3 para pruebas rápidas)
N_SPATIAL_GROUPS = 6  # clusters KMeans sobre centroides (CV espacial de diagnóstico)

TARGET = "rendimiento_t_ha"
ID = "parcel_id"
# Métrica principal para elegir modelo (confirmar con el Comité el 9-oct)
PRIMARY_METRIC = "rmse"
