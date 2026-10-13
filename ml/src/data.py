"""Carga del dataset estandarizado de Rol 1 + definición de familias de features."""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from pathlib import Path
from .config import DATA_ROOT, TARGET, ID, SEED, N_SPATIAL_GROUPS, N_TRAIN, N_EVAL
from .contract import validate_catalog

TOPO = ["area_ha", "elevation_mean", "slope_mean"]
GEO = ["centroid_lat", "centroid_lon"]  # OJO: proxy de ubicación; decidir si entra al modelo oficial


def load(root=None):
    """Devuelve (train, eval). `eval` NO tiene target: jamás se usa para tuning.

    Contrato §3: parcel_id string (sin conversión a entero), único, no nulo y coincidente entre fuentes.
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
    tr = df[df.dataset_split == "ENTRENAMIENTO"].reset_index(drop=True)
    ev = df[df.dataset_split == "PREDICCION"].reset_index(drop=True)
    assert tr[TARGET].notna().all() and ev[TARGET].isna().all(), "el target debe existir solo en train"
    assert (len(tr), len(ev)) == (N_TRAIN, N_EVAL), f"partición inesperada: {len(tr)}/{len(ev)}"
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
