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


def test_load_cut_contract():
    tr, ev, feats = E.load_cut("junio")
    K.validate_ids(tr); assert (len(tr), len(ev)) == (138, 59) and ev[C.TARGET].isna().all()
    assert not [f for f in feats if f in E.NON_FEATURES or f.startswith("mun_")]
