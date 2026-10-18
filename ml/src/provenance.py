"""Procedencia: huellas (hash) del dataset, versiones de entorno y estado de la auditoría.

Por qué existe (audit-2026-10-14, Persona 2, pendiente 4): `data_audit.json` no identificaba POR HASH el archivo
que auditó; un dataset distinto habría podido heredar un "OK". Aquí se define:
  - dataset_fingerprint(): hash de features_master + rendimiento + parcel_master  -> `data_version` (contrato §12)
  - audit_state():          ¿la auditoría guardada es válida PARA ESTE dataset? (cutoff_ok + sello de hash coincide)
`audit_data.py` no se modifica; `stamp_audit.py` agrega el sello de hash a su resultado.
"""
import hashlib
import json
import platform
import sys
from importlib import metadata
from pathlib import Path

from . import config as C

FINGERPRINT_FILES = {
    "features_master": "features/features_master.csv",
    "rendimiento": "targets/rendimiento.csv",
    "parcel_master": "parcel_master.csv",
}


def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def dataset_fingerprint(root=None):
    """{'files': {nombre: sha256}, 'data_version': 'sha256:<16>'} del dataset concreto. Falla si falta un archivo clave."""
    root = Path(root or C.DATA_ROOT)
    files = {}
    for name, rel in FINGERPRINT_FILES.items():
        p = root / rel
        if not p.exists():
            raise FileNotFoundError(f"Falta {p} (necesario para identificar la versión de los datos)")
        files[name] = sha256_file(p)
    combined = hashlib.sha256("".join(files[k] for k in sorted(files)).encode()).hexdigest()
    return {"files": files, "data_version": "sha256:" + combined[:16], "data_root": str(root)}


def data_version(root=None):
    return dataset_fingerprint(root)["data_version"]


def env_versions():
    """Versiones del entorno que afectan a la reproducibilidad del modelo serializado."""
    pk = {}
    for name in ("numpy", "pandas", "scipy", "scikit-learn", "joblib", "catboost", "xgboost", "lightgbm"):
        try:
            pk[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            pk[name] = None
    return {"python": platform.python_version(), "platform": platform.platform(), "packages": pk}


def read_json_tolerant(path):
    """Lee JSON en UTF-8 y, si falla, en cp1252: `audit_data.py` escribe con la codificación por defecto de Windows (cp1252)."""
    raw = Path(path).read_bytes()
    try:
        return json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError:
        return json.loads(raw.decode("cp1252"))


def audit_path():
    return C.RESULTS / "data_audit.json"


def audit_state(root=None):
    """Estado de la auditoría para el dataset actual.

    Devuelve {'valid': bool, 'cutoff_ok': bool|None, 'reason': str, 'data_version': str|None}.
    `valid` = el audit existe, dice cutoff_ok=True y lleva un sello de hash que coincide con el dataset actual.
    (`stamp_audit.py` solo sella auditorías posteriores a los archivos del dataset.)
    """
    root = Path(root or C.DATA_ROOT)
    ap = audit_path()
    if not ap.exists():
        return {"valid": False, "cutoff_ok": None, "data_version": None,
                "reason": "no existe results/data_audit.json: corre `python audit_data.py` y luego `python stamp_audit.py`"}
    audit = read_json_tolerant(ap)
    ok = bool(audit.get("cutoff_ok"))
    fp = audit.get("data_fingerprint")
    if not ok:
        return {"valid": False, "cutoff_ok": False, "data_version": None,
                "reason": "la auditoría reporta cutoff_ok=false (ver results/data_audit.json)"}
    if not fp:
        return {"valid": False, "cutoff_ok": True, "data_version": None,
                "reason": "data_audit.json no está sellado con el hash del dataset: corre `python stamp_audit.py`"}
    cur = dataset_fingerprint(root)
    if fp.get("data_version") != cur["data_version"]:
        return {"valid": False, "cutoff_ok": True, "data_version": cur["data_version"],
                "reason": (f"la auditoría corresponde a otro dataset ({fp.get('data_version')}) y el actual es "
                           f"{cur['data_version']}: reejecuta `python audit_data.py` y `python stamp_audit.py`")}
    return {"valid": True, "cutoff_ok": True, "data_version": cur["data_version"], "reason": "auditoría válida para este dataset"}


def run_meta(root=None, **extra):
    """Bloque de procedencia estándar para JSON de resultados (versiones exactas de datos/entorno/auditoría)."""
    st = audit_state(root)
    try:
        dv = dataset_fingerprint(root)["data_version"]
    except FileNotFoundError:
        dv = None
    meta = {"data_version": dv, "contract_version": C.CONTRACT_VERSION, "audit_valid_for_dataset": st["valid"],
            "audit_reason": st["reason"], "provisional": not st["valid"], "environment": env_versions(),
            "python_argv": sys.argv[1:]}
    meta.update(extra)
    return meta
