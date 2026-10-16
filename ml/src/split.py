"""Listas oficiales de IDs versionadas (contrato §2.6 y §14: no hardcodear 138/59).

`split/official_ids_v1.json` se GENERA con `make_official_ids.py` a partir de la columna `dataset_split` del dataset
entregado por Data. Esa asignación fue contrastada contra el maestro original (DataSet.zip) en audit-2026-10-14;
cuando FIRA publique la lista oficial de IDs (contrato §20, PENDIENTE) debe compararse con este archivo.
Las cantidades (n_train / n_eval) son OBSERVACIONES del split actual, no constantes contractuales.
"""
import hashlib
import json
from datetime import datetime, timezone

from . import config as C
from .provenance import read_json_tolerant

TRAIN_LABEL, EVAL_LABEL = "ENTRENAMIENTO", "PREDICCION"


def ids_sha256(ids):
    return hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()


def build_official_ids(df, *, source, data_version, version="official-ids-v1"):
    """df con columnas parcel_id y dataset_split (str). No toca el target."""
    tr = sorted(df.loc[df.dataset_split == TRAIN_LABEL, C.ID].astype(str))
    ev = sorted(df.loc[df.dataset_split == EVAL_LABEL, C.ID].astype(str))
    if set(tr) & set(ev):
        raise ValueError("IDs en entrenamiento y evaluación a la vez")
    return {"version": version, "source": source, "data_version": data_version,
            "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "derivada de dataset_split; PENDIENTE confirmar contra la lista oficial de FIRA (contrato §20)",
            "observed_counts": {"train": len(tr), "eval": len(ev)},
            "train_ids": tr, "eval_ids": ev,
            "train_ids_sha256": ids_sha256(tr), "eval_ids_sha256": ids_sha256(ev)}


def load_official_ids(path=None):
    """Devuelve el dict de la lista oficial o None si no existe. Verifica la integridad interna (hashes)."""
    p = path or C.OFFICIAL_IDS_FILE
    if not p.exists():
        return None
    d = read_json_tolerant(p)
    if ids_sha256(d["train_ids"]) != d["train_ids_sha256"] or ids_sha256(d["eval_ids"]) != d["eval_ids_sha256"]:
        raise ValueError(f"{p}: los hashes internos no coinciden con las listas (archivo alterado)")
    return d


def diff_split(df, official):
    """Diferencias entre dataset_split del dataset y la lista oficial. Devuelve dict vacío si coincide."""
    got_tr = set(df.loc[df.dataset_split == TRAIN_LABEL, C.ID]); got_ev = set(df.loc[df.dataset_split == EVAL_LABEL, C.ID])
    exp_tr, exp_ev = set(official["train_ids"]), set(official["eval_ids"])
    d = {}
    for k, a, b in (("train_faltan", exp_tr, got_tr), ("train_sobran", got_tr, exp_tr),
                    ("eval_faltan", exp_ev, got_ev), ("eval_sobran", got_ev, exp_ev)):
        x = sorted(a - b)
        if x:
            d[k] = x[:10] + (["…"] if len(x) > 10 else [])
    return d
