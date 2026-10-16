"""Carga del dataset estandarizado de Rol 1 + definición de familias de features."""
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from .config import DATA_ROOT, TARGET, ID, SEED, N_SPATIAL_GROUPS
from .contract import ContractError, validate_catalog
from .split import load_official_ids, diff_split, TRAIN_LABEL, EVAL_LABEL

TOPO = ["area_ha", "elevation_mean", "slope_mean"]
GEO = ["centroid_lat", "centroid_lon"]  # OJO: proxy de ubicación; decidir si entra al modelo oficial


def load(root=None):
    """Devuelve (train, eval). `eval` NO tiene target: jamás se usa para tuning.

    Contrato §5: parcel_id string (sin conversión a entero), único, no nulo y coincidente entre fuentes.
    §2.6/§14: la partición se valida contra la lista oficial versionada (split/official_ids_v1.json), NO contra 138/59.
    Las columnas `mun_*` y `grupo_espacial` son SOLO de diagnóstico/CV: nunca entran al feature_schema oficial.
    """
    root = Path(root or DATA_ROOT)
    if not (root / "features" / "features_master.csv").exists():
        raise FileNotFoundError(f"No se encontró features_master.csv en {root}. Define CEBADA_DATA o ajusta config.DATA_ROOT")
    validate_catalog(root)                                   # IDs consistentes entre las 4 fuentes
    fm = pd.read_csv(root / "features" / "features_master.csv", dtype={ID: str})
    y = pd.read_csv(root / "targets" / "rendimiento.csv", dtype={ID: str})
    df = fm.merge(y, on=ID, how="left", validate="1:1")
    km = KMeans(N_SPATIAL_GROUPS, random_state=SEED, n_init=10).fit(df[GEO].values)
    muni = pd.get_dummies(df["municipio"], prefix="mun").astype(float)
    df = pd.concat([df, muni, pd.Series(km.labels_, name="grupo_espacial", index=df.index)], axis=1)
    bad_split = set(df.dataset_split.unique()) - {TRAIN_LABEL, EVAL_LABEL}
    if bad_split:
        raise ContractError(f"dataset_split con valores inesperados: {bad_split}")
    official = load_official_ids()
    if official is None:
        warnings.warn("No existe split/official_ids_v1.json: la partición no se pudo validar contra una lista oficial. "
                      "Genera la lista con `python make_official_ids.py`.")
    else:
        d = diff_split(df, official)
        if d:
            raise ContractError(f"dataset_split no coincide con la lista oficial de IDs: {d}")
    tr = df[df.dataset_split == TRAIN_LABEL].reset_index(drop=True)
    ev = df[df.dataset_split == EVAL_LABEL].reset_index(drop=True)
    if len(tr) == 0 or len(ev) == 0:
        raise ContractError("Partición vacía (entrenamiento o evaluación)")
    if not tr[TARGET].notna().all() or not ev[TARGET].isna().all():
        raise ContractError("el target debe existir en TODO el conjunto etiquetado y en NINGUNA parcela de evaluación")
    return tr, ev


def families(df):
    """Familias de features por prefijo/nombre. Excluye columnas de fecha (strings)."""
    num = [c for c in df.select_dtypes("number").columns if c not in (TARGET, "grupo_espacial")]
    is_feno = lambda c: any(k in c for k in ("_peak", "_auc", "_growth_rate", "_decay_rate", "_std_temporal"))
    return {
        "topo": TOPO,
        "geo": GEO,
        "s2": [c for c in num if c.startswith("sentinel2_") and not is_feno(c)],
        "landsat": [c for c in num if c.startswith("landsat_")],
        "planet": [c for c in num if c.startswith("planet_") and not is_feno(c)],
        "feno_s2": [c for c in num if c.startswith("sentinel2_") and is_feno(c)],
        "feno_planet": [c for c in num if c.startswith("planet_") and is_feno(c)],
        "clima": [c for c in num if c.startswith(("precip", "tmin", "tmax", "amplitud"))],
        "muni": [c for c in num if c.startswith("mun_")],
    }


# E0–E5 del backlog (P2.4). Cada experimento = lista de familias.
EXPERIMENTS = {
    "E0_baseline": [],
    "E1_topo": ["topo"],
    "E2_basico": ["s2", "landsat", "feno_s2"],
    "E3_planet": ["planet", "feno_planet"],
    "E4_clima": ["clima"],
    "E5_fusion": ["topo", "s2", "landsat", "feno_s2", "planet", "feno_planet", "clima"],
    # Diagnóstico: ¿cuánto aporta la ubicación? (no es parte oficial hasta decidirlo)
    "X0_municipio": ["muni"],   # PISO REAL: media por municipio. Todo modelo debe superarlo para justificar el satélite.
    "X1_geo": ["geo"],
    "X3_muni_mas_sat": ["muni", "topo", "s2", "landsat", "feno_s2", "planet", "feno_planet"],
    "X2_fusion_mas_geo": ["topo", "geo", "s2", "landsat", "feno_s2", "planet", "feno_planet", "clima"],
}


def columns_for(exp, fam):
    cols = []
    for f in EXPERIMENTS[exp]:
        cols += fam[f]
    return list(dict.fromkeys(cols))
