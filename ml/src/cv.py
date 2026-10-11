"""Protocolo de validación (P2.2). RMSE principal + MAE + R². Siempre devuelve predicciones fuera de fold (OOF)."""
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold, KFold
from .config import N_SPLITS, N_REPEATS, SEED


def metrics(y, p):
    return {"rmse": mean_squared_error(y, p) ** 0.5, "mae": mean_absolute_error(y, p), "r2": r2_score(y, p)}


def repeated_cv(make_model, X, y, n_repeats=N_REPEATS, n_splits=N_SPLITS, seed=SEED):
    """CV aleatoria repetida. Devuelve (métricas por repetición, OOF promedio, OOF por repetición)."""
    X = np.asarray(X, float); y = np.asarray(y, float)
    per_rep, oofs = [], []
    for r in range(n_repeats):
        oof = np.zeros(len(y))
        for tr, va in KFold(n_splits, shuffle=True, random_state=seed + r).split(X):
            m = make_model(); m.fit(X[tr], y[tr]); oof[va] = m.predict(X[va])
        per_rep.append(metrics(y, oof)); oofs.append(oof)
    return pd.DataFrame(per_rep), np.mean(oofs, axis=0), np.array(oofs)


def spatial_cv(make_model, X, y, groups, n_splits=N_SPLITS):
    """CV por grupos espaciales (diagnóstico de generalización a zonas no vistas; suele ser pesimista)."""
    X = np.asarray(X, float); y = np.asarray(y, float)
    oof = np.zeros(len(y))
    for tr, va in GroupKFold(min(n_splits, len(set(groups)))).split(X, y, groups):
        m = make_model(); m.fit(X[tr], y[tr]); oof[va] = m.predict(X[va])
    return metrics(y, oof), oof


def paired_diff(oofs_a, oofs_b, y):
    """Diferencia pareada de RMSE por repetición (a - b). Negativo => a es mejor."""
    ra = np.array([mean_squared_error(y, o) ** 0.5 for o in oofs_a])
    rb = np.array([mean_squared_error(y, o) ** 0.5 for o in oofs_b])
    d = ra - rb
    return d.mean(), (d.std(ddof=1) if len(d) > 1 else float("nan"))
