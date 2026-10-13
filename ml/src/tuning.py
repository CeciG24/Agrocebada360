"""Espacios de búsqueda y utilidades de tuning (P2.5).

Los hiperparámetros se eligen SOLO con CV sobre las 138 parcelas de train (la partición de 59 no tiene target).
El tuning se evalúa con CV ANIDADA: el score externo nunca vio los datos usados para elegir hiperparámetros.
"""
import json
from pathlib import Path

import numpy as np
from sklearn.base import clone
from sklearn.model_selection import KFold, ParameterSampler

from . import config as C
from .models import zoo

# Rejillas pequeñas y conservadoras: con 138 filas, espacios grandes solo generan sobreajuste al CV.
SPACES = {
    "extratrees": {"n_estimators": [300, 500], "min_samples_leaf": [1, 2, 3, 5, 8],
                   "max_features": [0.1, 0.2, 0.33, 0.5, 0.8, 1.0], "max_depth": [None, 8, 12]},
    "rf": {"n_estimators": [300, 500], "min_samples_leaf": [1, 2, 3, 5, 8],
           "max_features": [0.1, 0.2, 0.33, 0.5, 0.8], "max_depth": [None, 8, 12], "max_samples": [None, 0.7, 0.9]},
    "catboost": {"iterations": [300, 500], "depth": [3, 4, 5, 6], "learning_rate": [0.02, 0.04, 0.07],
                 "l2_leaf_reg": [1, 3, 5, 10, 20], "rsm": [0.2, 0.5, 1.0]},
    "gbr": {"n_estimators": [150, 250, 400], "learning_rate": [0.02, 0.03, 0.06], "max_depth": [2, 3, 4],
            "subsample": [0.5, 0.7, 0.9], "min_samples_leaf": [1, 3, 6], "max_features": [0.3, 0.6, 1.0]},
    "xgboost": {"n_estimators": [200, 400], "max_depth": [2, 3, 4], "learning_rate": [0.02, 0.04, 0.07],
                "subsample": [0.5, 0.7, 0.9], "colsample_bytree": [0.3, 0.5, 0.8], "reg_lambda": [1, 5, 15],
                "min_child_weight": [1, 3, 6]},
    "lightgbm": {"n_estimators": [200, 400], "num_leaves": [4, 7, 15], "learning_rate": [0.02, 0.04, 0.07],
                 "min_child_samples": [4, 8, 15], "colsample_bytree": [0.3, 0.5, 0.8], "reg_lambda": [1, 5, 15]},
    "elasticnet": {"l1_ratio": [0.1, 0.3, 0.5, 0.7, 0.9]},
}


def prefixed(model, params):
    """Los Pipelines de sklearn necesitan `<paso>__<param>`; CatBoost no."""
    if hasattr(model, "steps"):
        step = model.steps[-1][0]
        return {f"{step}__{k}": v for k, v in params.items()}
    return dict(params)


def build(name, params=None, fast=False):
    m = zoo(fast)[name]()
    if params:
        m = clone(m).set_params(**prefixed(m, params))
    return m


def candidates(name, n_iter, seed=C.SEED):
    """Candidato 0 = configuración por defecto del zoo ({}), para que 'tuned' nunca sea peor en la búsqueda."""
    return [{}] + list(ParameterSampler(SPACES[name], n_iter=n_iter, random_state=seed))


def cv_rmse(name, params, X, y, n_splits, repeats, seed):
    """RMSE medio sobre repeticiones de KFold (RMSE calculado sobre los OOF de cada repetición)."""
    out = []
    for r in range(repeats):
        oof = np.zeros(len(y))
        for tr, va in KFold(n_splits, shuffle=True, random_state=seed + r).split(X):
            m = build(name, params); m.fit(X[tr], y[tr]); oof[va] = m.predict(X[va])
        out.append(float(np.sqrt(np.mean((y - oof) ** 2))))
    return float(np.mean(out))


def search(name, X, y, n_iter, n_splits=3, repeats=1, seed=C.SEED):
    scored = [(cv_rmse(name, p, X, y, n_splits, repeats, seed), p) for p in candidates(name, n_iter, seed)]
    scored.sort(key=lambda t: t[0])
    return scored   # [(rmse, params)] ordenado


def load_best(name, exp="E5_fusion", path=None):
    """Hiperparámetros afinados guardados por tune.py (para P2.7/P2.8/P2.9)."""
    p = Path(path or C.RESULTS / "tuning" / f"{exp}__{name}.json")
    return json.loads(p.read_text())["best_params"]
