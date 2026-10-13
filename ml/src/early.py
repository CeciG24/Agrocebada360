"""P2.6 — Utilidades para modelos de predicción temprana (cortes junio → octubre).

Pregunta que responde: ¿qué tan pronto en el ciclo abril–octubre 2025 se puede anticipar el rendimiento final?

Contrato (system-contract.md):
  §1.5/1.6  parcel_id siempre string.            §1.7  ningún corte puede pasar de DATA_CUTOFF (2025-10-31).
  §1.3      no se inventan features: solo columnas de la matriz que entregue Rol 1 (sin geo ni mun_*).
  §3.3      los faltantes los trata el Pipeline (imputación dentro del fold), no este módulo.
Las matrices por corte las produce Rol 1 (P1.11/P1.12). Este módulo NO las modifica; solo las lee y las audita.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from . import config as C
from . import contract as K

# Fecha límite que cada corte DEBERÍA respetar (la usa la auditoría; ajustar si Rol 1 documenta otra).
CUTS = {"junio": "2025-06-30", "julio": "2025-07-31", "agosto": "2025-08-31",
        "septiembre": "2025-09-30", "octubre": "2025-10-31"}
MATRIX_SUBDIR = "prediccion_temprana/matrices"
MATRIX_PATTERN = "features_master_corte_{cut}.csv"      # cambiar aquí si Rol 1 renombra los archivos

# Columnas que NO son features (identificadores, texto, geo de diagnóstico, target).
NON_FEATURES = {C.ID, "dataset_split", "municipio", "estado", C.TARGET, "centroid_lat", "centroid_lon"}

assert all(pd.Timestamp(d) <= pd.Timestamp(C.DATA_CUTOFF) for d in CUTS.values()), "un corte excede DATA_CUTOFF (§1.7)"


def load_cut(cut, root=None, subdir=MATRIX_SUBDIR, pattern=MATRIX_PATTERN):
    """Lee la matriz de un corte, le une el target y devuelve (train, eval, features)."""
    if cut not in CUTS:
        raise ValueError(f"Corte desconocido: {cut}. Opciones: {list(CUTS)}")
    root = Path(root or C.DATA_ROOT)
    path = root / subdir / pattern.format(cut=cut)
    if not path.exists():
        raise FileNotFoundError(f"No existe la matriz del corte '{cut}': {path}")
    m = pd.read_csv(path, dtype={C.ID: str})
    y = pd.read_csv(root / "targets" / "rendimiento.csv", dtype={C.ID: str})
    K.validate_ids(m, f"matriz {cut}")
    if C.TARGET in m.columns:                                  # el target no debe venir en la matriz de features
        raise K.ContractError(f"La matriz '{cut}' trae la columna objetivo {C.TARGET}")
    df = m.merge(y, on=C.ID, how="left", validate="1:1")
    tr = df[df.dataset_split == "ENTRENAMIENTO"].sort_values(C.ID).reset_index(drop=True)
    ev = df[df.dataset_split == "PREDICCION"].sort_values(C.ID).reset_index(drop=True)
    assert tr[C.TARGET].notna().all() and ev[C.TARGET].isna().all(), f"{cut}: el target debe existir solo en train"
    assert (len(tr), len(ev)) == (C.N_TRAIN, C.N_EVAL), f"{cut}: partición inesperada {len(tr)}/{len(ev)}"
    feats = [c for c in m.columns if c not in NON_FEATURES and pd.api.types.is_numeric_dtype(m[c])]
    K.validate_features(df, feats)
    return tr, ev, feats


def load_cuts(cuts=None, root=None, **kw):
    """Carga varios cortes en orden cronológico y comprueba que describan las mismas parcelas."""
    out = {c: dict(zip(("tr", "ev", "feats"), load_cut(c, root, **kw))) for c in (cuts or list(CUTS))}
    ref = None
    for c, d in out.items():
        ids = tuple(d["tr"][C.ID]) + tuple(d["ev"][C.ID])
        if ref is None: ref = ids
        elif ids != ref:
            raise K.ContractError(f"Corte '{c}': las parcelas/partición no coinciden con el primer corte")
    return out


def audit_windows(cuts_data, tol=1e-6, max_bad_frac=0.01):
    """Chequeo de coherencia entre cortes (no sustituye a P1.13, pero detecta ventanas mal construidas).

    Si cada corte acumula observaciones desde el mismo inicio, entonces al avanzar el corte:
      *_max → no baja · *_min → no sube · precipitación acumulada → no baja.
    Devuelve (issues, notes). `issues` vacío = coherente; no prueba que el inicio de ventana sea abril 2025.
    """
    issues, order = [], list(cuts_data)
    for a, b in zip(order[:-1], order[1:]):
        A = cuts_data[a]["tr"].set_index(C.ID); B = cuts_data[b]["tr"].set_index(C.ID)
        for f in sorted(set(cuts_data[a]["feats"]) & set(cuts_data[b]["feats"])):
            if f.endswith("_max") or "precip_accumulated" in f: bad = (B[f] < A[f] - tol)
            elif f.endswith("_min"): bad = (B[f] > A[f] + tol)
            else: continue
            if bad.mean() > max_bad_frac:
                issues.append({"feature": f, "from": a, "to": b, "violating_parcels": int(bad.sum()), "of": len(bad)})
    notes = []
    sets = {c: set(d["feats"]) for c, d in cuts_data.items()}
    if len({frozenset(s) for s in sets.values()}) > 1:
        notes.append("Los cortes no comparten exactamente el mismo conjunto de features: las curvas mezclan información y número de features.")
    return issues, notes


def baseline_matrices(tr):
    """Baselines de referencia por corte: mediana (sin features) y promedio por municipio (dummies SOLO de diagnóstico)."""
    return {"dummy_median": np.zeros((len(tr), 1)),
            "ridge_municipio": pd.get_dummies(tr["municipio"]).astype(float).to_numpy()}


def spatial_groups():
    """grupo_espacial por parcela, tomado de `data.load()` para que coincida con la CV espacial de run_experiments."""
    from .data import load
    t, _ = load()
    return t.set_index(C.ID)["grupo_espacial"]


def earliest_cut(curve, ok):
    """Primer corte (en orden cronológico) donde ok(corte, rmse) es verdadero; None si ninguno."""
    for cut, r in curve.items():
        if ok(cut, r): return cut
    return None
