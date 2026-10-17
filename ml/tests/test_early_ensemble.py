"""Tests de P2.6 (cortes tempranos) y P2.7 (ensemble). Los de ensemble usan datos sintéticos; los de cortes requieren CEBADA_DATA."""
import numpy as np, pandas as pd, pytest

from src import config as C, contract as K
from src import ensemble as EN
from src import early as E


def test_simplex_weights_valid():
    rng = np.random.default_rng(0); y = rng.normal(size=80)
    P = np.c_[y + rng.normal(0, .1, 80), y + rng.normal(0, 1, 80), rng.normal(size=80)]
    w = EN.simplex_weights(P, y)
    assert abs(w.sum() - 1) < 1e-6 and (w >= 0).all() and w.argmax() == 0      # premia al modelo más preciso


def test_decide_discards_when_no_gain():
    y = np.random.default_rng(1).normal(size=60)
    R = 4; P = np.stack([np.c_[y + .5, y + .5] for _ in range(R)])              # miembros idénticos: ensemble = miembro
    res = EN.compare(P, P[0], y, ["a", "b"])
    assert EN.decide(res)["keep"] is False


def test_build_ensemble_predicts_and_serializes(tmp_path):
    import joblib
    rng = np.random.default_rng(2); X = rng.normal(size=(60, 5)); y = X[:, 0] + rng.normal(0, .1, 60)
    m = EN.build_ensemble(["ridge", "extratrees"], [0.5, 0.5], fast=True).fit(X, y)
    joblib.dump(m, tmp_path / "m.joblib")
    assert np.isfinite(joblib.load(tmp_path / "m.joblib").predict(X[:3])).all()


def test_cuts_never_exceed_cutoff():
    assert all(pd.Timestamp(d) <= pd.Timestamp(C.DATA_CUTOFF) for d in E.CUTS.values())


def test_load_cut_contract(data):
    from src.split import load_official_ids
    tr, ev, feats = E.load_cut("junio")
    K.validate_ids(tr); assert ev[C.TARGET].isna().all() and tr[C.TARGET].notna().all()
    off = load_official_ids()
    if off is not None:                                  # la partición viene de la lista oficial, no de constantes 138/59
        assert set(tr[C.ID]) == set(off["train_ids"]) and set(ev[C.ID]) == set(off["eval_ids"])
    assert not [f for f in feats if f in E.NON_FEATURES or f.startswith("mun_")]


def test_nested_weighted_oof_has_no_leakage():
    """Cambiar el target de las filas de validación NO debe cambiar su predicción (pesos y miembros solo ven el train)."""
    rng = np.random.default_rng(3); X = rng.normal(size=(60, 4)); y = X[:, 0] + rng.normal(0, .3, 60)
    tr = np.arange(0, 45); va = np.arange(45, 60)
    p1, W = EN.nested_weighted_oof(["ridge", "extratrees"], {}, X, y, [(tr, va)], fast=True)
    y2 = y.copy(); y2[va] += 100.0
    p2, _ = EN.nested_weighted_oof(["ridge", "extratrees"], {}, X, y2, [(tr, va)], fast=True)
    assert np.allclose(p1[va], p2[va]) and abs(W[0].sum() - 1) < 1e-6 and (W[0] >= 0).all()


def test_decide_never_keeps_without_nested_weighted_if_mean_is_not_better():
    y = np.random.default_rng(4).normal(size=60); R = 4
    P = np.stack([np.c_[y + .5, y + .5] for _ in range(R)])
    res = EN.compare(P, P[0], y, ["a", "b"])             # sin Pw: la variante ponderada no existe (NaN) y no puede elegirse
    assert np.isnan(res["weighted"]).all() and EN.decide(res)["variant"] == "mean"
