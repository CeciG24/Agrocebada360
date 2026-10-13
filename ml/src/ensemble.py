"""P2.7 — Lógica del ensemble final de modelos (promedio simple y ponderado).

Regla de la propuesta: el ensemble solo se conserva si mejora de forma CONSISTENTE frente al mejor modelo individual.
Para que la comparación sea justa, todos los modelos se evalúan con los MISMOS folds en cada repetición.

Contrato: el artefacto final debe ser UN objeto con .predict() (§5/§6). Se usa `sklearn.VotingRegressor`, que se serializa
con joblib sin depender de este repo (el backend solo necesita sklearn/catboost instalados).
"""
import numpy as np
from scipy.optimize import minimize
from sklearn.ensemble import VotingRegressor
from sklearn.model_selection import GroupKFold, KFold

from . import config as C
from .tuning import build


def rmse(y, p):
    return float(np.sqrt(np.mean((np.asarray(y) - np.asarray(p)) ** 2)))


def member_oofs(names, params_map, X, y, groups, repeats, fast=False, n_splits=C.N_SPLITS, seed=C.SEED):
    """OOF de cada modelo con folds compartidos. Devuelve (P_rand [repeats, n, k], P_spatial [n, k])."""
    X = np.asarray(X, float); y = np.asarray(y, float)
    P = np.zeros((repeats, len(y), len(names)))
    for r in range(repeats):
        for tr, va in KFold(n_splits, shuffle=True, random_state=seed + r).split(X):     # mismos folds para todos
            for j, n in enumerate(names):
                m = build(n, params_map.get(n), fast); m.fit(X[tr], y[tr]); P[r, va, j] = m.predict(X[va])
    Ps = np.zeros((len(y), len(names)))
    for tr, va in GroupKFold(min(n_splits, len(set(groups)))).split(X, y, groups):
        for j, n in enumerate(names):
            m = build(n, params_map.get(n), fast); m.fit(X[tr], y[tr]); Ps[va, j] = m.predict(X[va])
    return P, Ps


def simplex_weights(P, y):
    """Pesos >= 0 que suman 1 y minimizan el error cuadrático sobre las predicciones OOF P [n, k]."""
    k = P.shape[1]
    res = minimize(lambda w: np.mean((y - P @ w) ** 2), np.full(k, 1 / k), method="SLSQP",
                   bounds=[(0, 1)] * k, constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}])
    w = np.clip(res.x, 0, None)
    return w / w.sum() if w.sum() > 0 else np.full(k, 1 / k)


def cv_weighted_predictions(P, y, n_splits=C.N_SPLITS, seed=C.SEED):
    """Predicción ponderada donde los pesos de cada fold se ajustan SIN las filas de ese fold (nivel 2).

    Limitación conocida: las OOF de los modelos base de las filas de entrenamiento del nivel 2 salieron de modelos que
    sí vieron las filas retenidas, por lo que este número puede ser ligeramente optimista (k-1 parámetros: efecto pequeño).
    """
    out = np.zeros(len(y))
    for tr, va in KFold(n_splits, shuffle=True, random_state=seed).split(P):
        out[va] = P[va] @ simplex_weights(P[tr], y[tr])
    return out


def compare(P, Ps, y, names, seed=C.SEED):
    """Métricas por repetición de: cada miembro, promedio simple y ponderado; más la versión espacial."""
    R, n, k = P.shape
    members = np.array([[rmse(y, P[r, :, j]) for j in range(k)] for r in range(R)])          # [R, k]
    mean_ = np.array([rmse(y, P[r].mean(1)) for r in range(R)])
    wtd = np.array([rmse(y, cv_weighted_predictions(P[r], y, seed=seed + r)) for r in range(R)])
    best = int(members.mean(0).argmin())
    w_full = simplex_weights(P.mean(0), y)
    sp = {"members": [rmse(y, Ps[:, j]) for j in range(k)], "mean": rmse(y, Ps.mean(1)), "weighted": rmse(y, Ps @ w_full)}
    resid = np.corrcoef((P.mean(0) - y[:, None]).T) if k > 1 else np.ones((1, 1))
    return {"members": members, "mean": mean_, "weighted": wtd, "best_idx": best, "weights_full": w_full,
            "spatial": sp, "resid_corr": resid}


def decide(res, min_gain=0.005, min_win=0.8, spatial_tol=0.01):
    """¿Se conserva el ensemble? Mejora media >= min_gain, gana en >= min_win de las repeticiones y no empeora en espacial."""
    b = res["best_idx"]; ref = res["members"][:, b]
    variant = "weighted" if res["weighted"].mean() < res["mean"].mean() else "mean"
    delta = res[variant] - ref                               # negativo = el ensemble es mejor
    win = float((delta < 0).mean()); gain = float(-delta.mean())
    sp_delta = res["spatial"][variant] - res["spatial"]["members"][b]
    keep = (gain >= min_gain) and (win >= min_win) and (sp_delta <= spatial_tol) and len(delta) >= 3
    return {"variant": variant, "keep": bool(keep), "mean_gain_rmse": gain, "win_rate": win,
            "spatial_delta_rmse": float(sp_delta), "n_repeats": int(len(delta)),
            "criteria": {"min_gain": min_gain, "min_win": min_win, "spatial_tol": spatial_tol, "min_repeats": 3}}


def build_ensemble(names, weights, params_map=None, fast=False):
    """VotingRegressor listo para .fit(X, y) (P2.9) y para serializarse con contract.save_artifacts."""
    params_map = params_map or {}
    return VotingRegressor([(n, build(n, params_map.get(n), fast)) for n in names], weights=[float(w) for w in weights])
