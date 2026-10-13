"""Configuración central del protocolo (P2.2). Cambiar aquí, no en los notebooks.

Alineado con system-contract.md v0.1.0 (§5 artefactos de modelo, §7.1 unidad, §10 versiones).
"""
import os
from pathlib import Path

ML_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ML_DIR.parent

_DATASET = "DATASET_RETO_AGRO_2026_LIMPIO"


def _find_data_root():
    """CEBADA_DATA > <repo>/data/ > <repo>/../data/ (el layout depende de cómo se clone el proyecto)."""
    env = os.environ.get("CEBADA_DATA")
    if env:
        return Path(env)
    for base in (ML_DIR / "data", PROJECT_ROOT / "data"):
        for cand in (base / _DATASET, base / _DATASET / _DATASET):   # el zip suele venir anidado
            if (cand / "features" / "features_master.csv").exists():
                return cand
    return ML_DIR / "data" / _DATASET   # no existe: load() fallará con mensaje explícito


DATA_ROOT = _find_data_root()
RESULTS = ML_DIR / "results"
MODELS = ML_DIR / "models"            # contrato §5: models/yield_model_<v>.joblib + models/feature_schema.json

SEED = 42
N_SPLITS = 5          # folds
N_REPEATS = 10        # repeticiones de CV (usar 3 para pruebas rápidas)
N_SPATIAL_GROUPS = 6  # clusters KMeans sobre centroides (CV espacial de diagnóstico)

TARGET = "rendimiento_t_ha"
UNIT = "t/ha"                          # contrato §17: unidad a confirmar con el Comité; hoy se asume t/ha
ID = "parcel_id"                       # contrato §17: nombre oficial de la columna ID por confirmar
N_TRAIN, N_EVAL = 138, 59              # partición oficial del reto

# --- Contrato §1.7: no usar datos posteriores a esta fecha para el ciclo abril–octubre 2025 ---
DATA_CUTOFF = "2025-10-31"
# Si CEBADA_STRICT_CUTOFF=1, los scripts que generan artefactos abortan cuando el audit de corte falla.
STRICT_CUTOFF = os.environ.get("CEBADA_STRICT_CUTOFF", "0") == "1"

# --- Versiones (contrato §10) ---
CONTRACT_VERSION = "0.1.0"
MODEL_VERSION = "yield-v0"             # baseline; el modelo ganador será yield-v1
FEATURE_SCHEMA_VERSION = "features-v0"

# Métrica principal para elegir modelo (confirmar con el Comité el 9-oct)
PRIMARY_METRIC = "rmse"
