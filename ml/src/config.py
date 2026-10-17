"""Configuración central del protocolo (P2.2). Cambiar aquí, no en los notebooks.

Alineado con system-contract.md v0.3.0 (§2 política temporal, §7 artefactos de modelo, §12 versiones, §14 submission)
y con audit-2026-10-14.md / backlog-review-2026-10-14.md.
"""
import os
from pathlib import Path

ML_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ML_DIR.parent

_DATASET = "DATASET_RETO_AGRO_2026_LIMPIO"


def _find_data_root():
    """CEBADA_DATA > <repo>/data/ > <repo>/ml/data/ (el layout depende de cómo se clone el proyecto).

    Si el ZIP de Data trae otro layout, NO se parchea aquí: usar `python prepare_data.py` (adaptador reproducible).
    """
    env = os.environ.get("CEBADA_DATA")
    if env:
        return Path(env)
    for base in (PROJECT_ROOT / "data", ML_DIR / "data"):
        for cand in (base / _DATASET, base / _DATASET / _DATASET):   # el zip suele venir anidado
            if (cand / "features" / "features_master.csv").exists():
                return cand
    return PROJECT_ROOT / "data" / _DATASET   # no existe: load() fallará con mensaje explícito


DATA_ROOT = _find_data_root()
RESULTS = ML_DIR / "results"
MODELS = ML_DIR / "models"            # contrato §7: models/yield_model_<v>.joblib + models/feature_schema.json
SPLIT_DIR = ML_DIR / "split"          # listas oficiales de IDs versionadas (contrato §2.6, §14)
OFFICIAL_IDS_FILE = SPLIT_DIR / "official_ids_v1.json"

SEED = 42
N_SPLITS = 5          # folds
N_REPEATS = 10        # repeticiones de CV (usar 3 para pruebas rápidas)
N_SPATIAL_GROUPS = 6  # clusters KMeans sobre centroides (CV espacial de diagnóstico; no reproduce el muestreo oficial, §7.1)

# --- Nombres internos (alias). Los nombres OFICIALES siguen PENDIENTES (contrato §20) ---
TARGET = "rendimiento_t_ha"            # alias interno; mapeo observado en el dataset limpio: RENDIMIENTO_T_HA -> rendimiento_t_ha
UNIT = "t/ha"                          # CONFIRMADO (2.ª sesión FIRA, 9-oct-2026; contrato §1.1)
ID = "parcel_id"                       # alias interno; mapeo observado: ID_POLIGONO -> parcel_id (nombre oficial PENDIENTE)
PRED_COL = "rendimiento_pred_t_ha"     # nombre INTERNO de la columna de predicción; columnas/orden del submission: PENDIENTE (§20)
SUBMISSION_DECIMALS = 4                # CONFIRMADO (§1.1, §14): valor puntual en t/ha con cuatro decimales

# --- Política temporal (contrato §2) ---
TARGET_CYCLE = "2025-04/2025-10"       # aclaración oficial, 2.ª sesión (9-oct-2026). NO está literalmente en las Bases (§2.1)
# Convención técnica de cierre del ciclo (§2.3). FIRA confirma el MES (oct-2025), no el día 31.
DATA_CUTOFF = "2025-10-31"
# Exportar artefactos/predicciones exige una auditoría válida PARA ESE dataset (hash). Por defecto es obligatorio;
# desactivar solo para experimentos exploratorios: CEBADA_STRICT_CUTOFF=0 o --allow-unverified en los scripts.
STRICT_CUTOFF = os.environ.get("CEBADA_STRICT_CUTOFF", "1") != "0"

# --- Versiones (contrato §12) ---
CONTRACT_VERSION = "0.3.0"
MODEL_VERSION = "yield-v1"             # modelo final (P2.9). El baseline se publica como "yield-v0"
BASELINE_MODEL_VERSION = "yield-v0"
FEATURE_SCHEMA_VERSION = "features-v1"  # formato de schema alineado con contrato 0.3.0 §7.2

# Experimentos oficiales internos (los X* usan ubicación/municipio y son SOLO diagnóstico, backlog-review P2.4)
OFFICIAL_EXPERIMENTS = ("E1_topo", "E2_basico", "E3_planet", "E4_clima", "E5_fusion")

# Métrica principal para elegir modelo: DECISIÓN TÉCNICA INTERNA; FIRA solo menciona RMSE, MAE, R² "u otras" (Bases)
PRIMARY_METRIC = "rmse"
