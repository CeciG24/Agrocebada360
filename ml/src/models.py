"""Zoo de modelos (P2.1/P2.3). Imputación/escalado van dentro del Pipeline: se ajustan POR FOLD."""
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
        "ridge": lambda: make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                                        RidgeCV(alphas=[1e-1, 1, 10, 30, 100, 300, 1000, 3000])),
        "elasticnet": lambda: make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                                             ElasticNetCV(l1_ratio=0.5, alphas=[1e-3, 1e-2, 1e-1, 1, 10, 30, 100, 300, 1000], cv=3, max_iter=2000, tol=1e-3, random_state=SEED)),
        "rf": lambda: make_pipeline(SimpleImputer(strategy="median"),
                                    RandomForestRegressor(nt, min_samples_leaf=3, max_features=0.33, random_state=SEED, n_jobs=-1)),
        "extratrees": lambda: make_pipeline(SimpleImputer(strategy="median"),
                                            ExtraTreesRegressor(nt, min_samples_leaf=3, max_features=0.33, random_state=SEED, n_jobs=-1)),
        "gbr": lambda: make_pipeline(SimpleImputer(strategy="median"),
                                     GradientBoostingRegressor(n_estimators=200, learning_rate=0.03, max_depth=2,
                                                               subsample=0.7, random_state=SEED)),
    }
    try:
        from catboost import CatBoostRegressor
        m["catboost"] = lambda: CatBoostRegressor(iterations=400, depth=4, learning_rate=0.04, l2_leaf_reg=5,
                                                  random_seed=SEED, verbose=0, thread_count=-1)
    except Exception:
        pass
    try:
        from xgboost import XGBRegressor
        m["xgboost"] = lambda: make_pipeline(SimpleImputer(strategy="median"),
                                             XGBRegressor(n_estimators=300, max_depth=3, learning_rate=0.03, subsample=0.7,
                                                          colsample_bytree=0.5, reg_lambda=5, random_state=SEED, n_jobs=-1))
    except Exception:
        pass
    try:
        from lightgbm import LGBMRegressor
        m["lightgbm"] = lambda: make_pipeline(SimpleImputer(strategy="median"),
                                              LGBMRegressor(n_estimators=300, learning_rate=0.03, num_leaves=7, min_child_samples=8,
                                                            subsample=0.7, subsample_freq=1, colsample_bytree=0.5, reg_lambda=5,
                                                            random_state=SEED, verbose=-1, n_jobs=-1))
    except Exception:
        pass
    return m
