"""P2.7 — Lógica del ensemble final de modelos (promedio simple y ponderado).

Regla de la propuesta: el ensemble solo se conserva si mejora de forma CONSISTENTE frente al mejor modelo individual.
Para que la comparación sea justa, todos los modelos se evalúan con los MISMOS folds en cada repetición.

Corrección frente a la versión anterior (audit-2026-10-14 / backlog-review P2.7):
  * La ponderación YA NO tiene fuga entre niveles. Los pesos de cada fold externo se ajustan con predicciones OOF
    *internas* calculadas solo con el train de ese fold (stacking anidado). Es la misma receta que se aplica al modelo final
    (pesos aprendidos de OOF), por lo que la estimación corresponde al procedimiento que realmente se entrega.
  * El promedio simple no tiene parámetros que aprender: nunca tuvo esa fuga.
  * Si los hiperparámetros de los miembros provienen del tuning global con las 138 parcelas, la comparación NO es independiente
    (lo marca run_ensemble.py); no presentarla como evaluación final imparcial.

Contrato: el artefacto final debe ser UN objeto con .predict() (§7/§8). Se usa `sklearn.VotingRegressor`, que se serializa
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


def _fit_predict(name, params_map, fast, Xtr, ytr, Xva):
    m = build(name, params_map.get(name), fast); m.fit(Xtr, ytr)
    return m.predict(Xva)


def member_oofs(names, params_map, X, y, groups, repeats, fast=False, n_splits=C.N_SPLITS, seed=C.SEED):
    """OOF de cada modelo con folds compartidos. Devuelve (P_rand [repeats, n, k], P_spatial [n, k])."""
    X = np.asarray(X, float); y = np.asarray(y, float)
    P = np.zeros((repeats, len(y), len(names)))
    for r in range(repeats):
        for tr, va in KFold(n_splits, shuffle=True, random_state=seed + r).split(X):     # mismos folds para todos
            for j, n in enumerate(names):
                P[r, va, j] = _fit_predict(n, params_map, fast, X[tr], y[tr], X[va])
    Ps = np.zeros((len(y), len(names)))
    for tr, va in GroupKFold(min(n_splits, len(set(groups)))).split(X, y, groups):
        for j, n in enumerate(names):
            Ps[va, j] = _fit_predict(n, params_map, fast, X[tr], y[tr], X[va])
    return P, Ps


def simplex_weights(P, y):
    """Pesos >= 0 que suman 1 y minimizan el error cuadrático sobre las predicciones OOF P [n, k]."""
    k = P.shape[1]
    res = minimize(lambda w: np.mean((y - P @ w) ** 2), np.full(k, 1 / k), method="SLSQP",
                   bounds=[(0, 1)] * k, constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}])
    w = np.clip(res.x, 0, None)
    return w / w.sum() if w.sum() > 0 else np.full(k, 1 / k)


def nested_weighted_oof(names, params_map, X, y, outer_splits, fast=False, inner_splits=3, seed=C.SEED):
    """Predicción ponderada SIN fuga entre niveles (stacking anidado).

    Por cada split externo (tr, va):
      1. OOF interno de cada miembro usando SOLO `tr` (KFold interno) -> pesos simplex ajustados con esas predicciones
      2. miembros reentrenados con todo `tr`; se predice `va` y se combina con los pesos del paso 1
    `va` no participa ni en los miembros ni en los pesos. Devuelve (pred [n], pesos [n_splits, k]).
    """
    X = np.asarray(X, float); y = np.asarray(y, float)
    pred = np.zeros(len(y)); W = []
    for tr, va in outer_splits:
        Pin = np.zeros((len(tr), len(names)))
        for itr, iva in KFold(inner_splits, shuffle=True, random_state=seed).split(tr):
            for j, n in enumerate(names):
                Pin[iva, j] = _fit_predict(n, params_map, fast, X[tr][itr], y[tr][itr], X[tr][iva])
        w = simplex_weights(Pin, y[tr]); W.append(w)
        Pva = np.column_stack([_fit_predict(n, params_map, fast, X[tr], y[tr], X[va]) for n in names])
        pred[va] = Pva @ w
    return pred, np.array(W)


def weighted_oofs(names, params_map, X, y, groups, repeats, fast=False, n_splits=C.N_SPLITS, inner_splits=3, seed=C.SEED):
    """Ponderado anidado con los MISMOS folds externos que member_oofs. Devuelve (Pw [repeats, n], Pws [n], W_mean [k])."""
    X = np.asarray(X, float)
    Pw, Ws = [], []
    for r in range(repeats):
        pr, W = nested_weighted_oof(names, params_map, X, y, list(KFold(n_splits, shuffle=True, random_state=seed + r).split(X)),
                                    fast, inner_splits, seed + r)
        Pw.append(pr); Ws.append(W)
    sp = list(GroupKFold(min(n_splits, len(set(groups)))).split(X, y, groups))
    Pws, Wsp = nested_weighted_oof(names, params_map, X, y, sp, fast, inner_splits, seed)
    return np.array(Pw), Pws, np.concatenate(Ws + [Wsp]).mean(0)


def compare(P, Ps, y, names, Pw=None, Pws=None):
    """Métricas por repetición de: cada miembro, promedio simple y ponderado (anidado); más la versión espacial.

    Si no se pasa Pw (ponderado anidado), la variante ponderada no se evalúa (NaN) y no podrá elegirse.
    """
    R, n, k = P.shape
    members = np.array([[rmse(y, P[r, :, j]) for j in range(k)] for r in range(R)])          # [R, k]
    mean_ = np.array([rmse(y, P[r].mean(1)) for r in range(R)])
    wtd = np.array([rmse(y, Pw[r]) for r in range(R)]) if Pw is not None else np.full(R, np.nan)
    best = int(members.mean(0).argmin())
    w_full = simplex_weights(P.mean(0), y)       # pesos que usaría el modelo final (aprendidos del OOF completo)
    sp = {"members": [rmse(y, Ps[:, j]) for j in range(k)], "mean": rmse(y, Ps.mean(1)),
          "weighted": rmse(y, Pws) if Pws is not None else float("nan")}
    resid = np.corrcoef((P.mean(0) - y[:, None]).T) if k > 1 else np.ones((1, 1))
    return {"members": members, "mean": mean_, "weighted": wtd, "best_idx": best, "weights_full": w_full,
            "spatial": sp, "resid_corr": resid}


def decide(res, min_gain=0.005, min_win=0.8, spatial_tol=0.01):
    """¿Se conserva el ensemble? Mejora media >= min_gain, gana en >= min_win de las repeticiones y no empeora en espacial."""
    b = res["best_idx"]; ref = res["members"][:, b]
    w_ok = np.isfinite(res["weighted"]).all() and res["weighted"].mean() < res["mean"].mean()
    variant = "weighted" if w_ok else "mean"
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
