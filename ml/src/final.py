"""Construcción del modelo final (P2.8 -> P2.9) a partir de results/final_model_config.json.

La "especificación" (spec) es lo que select_model.py decide y train_final_model.py ejecuta:
  {"type": "single",   "model": "extratrees", "params": {...}}
  {"type": "ensemble", "members": [...], "weights": {...}, "member_params": {...}}
El modelo se entrena con un DataFrame para que sklearn registre `feature_names_in_` y verifique nombres/orden al predecir.
"""
import json

from . import config as C
from .provenance import read_json_tolerant
from .ensemble import build_ensemble
from .tuning import build

CONFIG_FILE = C.RESULTS / "final_model_config.json"


def load_config(path=None):
    p = path or CONFIG_FILE
    if not p.exists():
        raise FileNotFoundError(f"No existe {p}: corre primero `python select_model.py` (P2.8)")
    return read_json_tolerant(p)


def build_from_spec(spec, fast=False):
    if spec["type"] == "single":
        return build(spec["model"], spec.get("params") or None, fast)
    if spec["type"] == "ensemble":
        names = spec["members"]
        return build_ensemble(names, [spec["weights"][n] for n in names], spec.get("member_params") or {}, fast)
    raise ValueError(f"spec desconocida: {spec}")


def describe(spec):
    if spec["type"] == "single":
        return spec["model"]
    return "ensemble(" + ",".join(f"{n}:{spec['weights'][n]:.2f}" for n in spec["members"]) + ")"


def best_official_exp(leaderboard="leaderboard.csv"):
    """Experimento OFICIAL (E1–E5) con mejor RMSE en el leaderboard. Los X* (municipio/ubicación) no cuentan."""
    import pandas as pd
    lb = pd.read_csv(C.RESULTS / leaderboard)
    off = lb[lb.tipo == "oficial"] if "tipo" in lb.columns else lb[lb.exp.isin(C.OFFICIAL_EXPERIMENTS)]
    if off.empty:
        raise SystemExit(f"{leaderboard} no tiene experimentos oficiales: corre run_experiments.py")
    return off.sort_values("rmse").iloc[0].exp
