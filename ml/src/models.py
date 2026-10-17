"""Zoo de modelos (P2.1/P2.3). Imputacion/escalado van dentro del Pipeline: se ajustan POR FOLD.

Contexto: 138 parcelas de entrenamiento, regresion tabular con features de alta dimension (satelite).
Cada modelo usa configuracion conservadora para N pequeno; el tuning (tune.py) ajustara los finalistas
con CV anidada sobre el mismo conjunto de 138 muestras.
"""
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import RidgeCV, ElasticNetCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from .config import SEED


def zoo(fast=False):
    nt = 150 if fast else 300
    m = {
        "dummy_median": lambda: DummyRegressor(strategy="median"),

        # Ridge: grid amplio — con 138 muestras suele necesitar alphas altos (100-10000).
        # Se añade 10000 para cubrir casos de features muy correlacionadas (satelital).
        "ridge": lambda: make_pipeline(
            SimpleImputer(strategy="median"),
            StandardScaler(),
            RidgeCV(alphas=[0.1, 1, 10, 30, 100, 300, 1000, 3000, 10000])),

        # ElasticNet: l1_ratio como LISTA para que ElasticNetCV busque tambien la mezcla L1/L2.
        # ANTES estaba fijo en 0.5 (bug: ElasticNetCV acepta lista y busca sobre ella).
        # cv=5 en lugar de 3 para mayor estabilidad en N pequeno.
        # max_iter/tol aumentados para garantizar convergencia en espacios de alta dimension.
        "elasticnet": lambda: make_pipeline(
            SimpleImputer(strategy="median"),
            StandardScaler(),
            ElasticNetCV(
                l1_ratio=[0.1, 0.3, 0.5, 0.7, 0.9, 1.0],
                alphas=[1e-3, 1e-2, 1e-1, 1, 10, 30, 100, 300, 1000],
                cv=5, max_iter=5000, tol=1e-4, random_state=SEED)),

        # RF: min_samples_leaf=3 y max_features=0.33 controlan sobreajuste en N pequeno.
        # max_features=0.33 introduce diversidad entre arboles (recomendacion estandar para regresion tabular).
        "rf": lambda: make_pipeline(
            SimpleImputer(strategy="median"),
            RandomForestRegressor(nt, min_samples_leaf=3, max_features=0.33,
                                  random_state=SEED, n_jobs=-1)),

        # ExtraTrees: varianza extra compensada por min_samples_leaf=3.
        # Suele competir con RF en datasets pequenos por su menor sesgo.
        "extratrees": lambda: make_pipeline(
            SimpleImputer(strategy="median"),
            ExtraTreesRegressor(nt, min_samples_leaf=3, max_features=0.33,
                                random_state=SEED, n_jobs=-1)),

        # GBR: con lr=0.03 necesita >= 300 iteraciones para converger (antes 200, insuficiente).
        # min_samples_leaf=3 evita hojas con 1-2 muestras que memorizan el fold.
        # max_depth=2 (stumps casi) es la mejor opcion para N pequeno con GBR (Friedman 2001).
        "gbr": lambda: make_pipeline(
            SimpleImputer(strategy="median"),
            GradientBoostingRegressor(n_estimators=300, learning_rate=0.03, max_depth=2,
                                      subsample=0.7, min_samples_leaf=3, random_state=SEED)),
    }
    try:
        from catboost import CatBoostRegressor
        # rsm=0.6: subsampling de columnas. Con cientos de features satelitales reduce sobreajuste
        # y mejora diversidad entre arboles (analogo a colsample_bytree en XGB/LGB).
        # depth=4 conserva la capacidad de capturar interacciones satelite+clima+topo.
        m["catboost"] = lambda: CatBoostRegressor(
            iterations=400, depth=4, learning_rate=0.04,
            l2_leaf_reg=5, rsm=0.6,
            random_seed=SEED, verbose=0, thread_count=-1)
    except Exception:
        pass
    try:
        from xgboost import XGBRegressor
        # min_child_weight=3: con 138 muestras el default (1) es demasiado permisivo;
        # obliga a cada hoja a tener peso suficiente y evita memorizar outliers de un fold.
        m["xgboost"] = lambda: make_pipeline(
            SimpleImputer(strategy="median"),
            XGBRegressor(n_estimators=300, max_depth=3, learning_rate=0.03,
                         subsample=0.7, colsample_bytree=0.5, reg_lambda=5,
                         min_child_weight=3, random_state=SEED, n_jobs=-1))
    except Exception:
        pass
    try:
        from lightgbm import LGBMRegressor
        # min_child_samples=10: con folds de ~110 muestras, 8 es demasiado bajo;
        # 10 es el minimo recomendado para N < 200 (evita hojas con 1-2 muestras).
        m["lightgbm"] = lambda: make_pipeline(
            SimpleImputer(strategy="median"),
            LGBMRegressor(n_estimators=300, learning_rate=0.03, num_leaves=7,
                          min_child_samples=10, subsample=0.7, subsample_freq=1,
                          colsample_bytree=0.5, reg_lambda=5,
                          random_state=SEED, verbose=-1, n_jobs=-1))
    except Exception:
        pass
    return m
