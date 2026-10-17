"""Sella results/data_audit.json con la huella (hash) del dataset auditado.

Uso (después de la auditoría):   python audit_data.py ; python stamp_audit.py
Por qué: audit_data.py (que NO se modifica) no registra qué archivo auditó. Sin sello, `train_final_model.py`,
`generate_predictions.py` y `make_baseline_predictions.py` se niegan a exportar (audit-2026-10-14, Persona 2, pend. 4).

Reglas: no sella si la auditoría dice cutoff_ok=false, si apunta a otra carpeta de datos, o si es anterior a los
archivos del dataset (auditoría obsoleta). Exit code 1 en esos casos.
"""
import json, sys
from datetime import datetime, timezone
from src import config as C
from src.provenance import audit_path, dataset_fingerprint, sha256_file, read_json_tolerant, FINGERPRINT_FILES

p = audit_path()
if not p.exists():
    sys.exit(f"No existe {p}: corre primero `python audit_data.py`")
audit = read_json_tolerant(p)      # audit_data.py puede haberlo escrito en cp1252 (Windows)
if not audit.get("cutoff_ok"):
    sys.exit("La auditoría reporta cutoff_ok=false: no se sella. Corrige el dataset (Rol 1) y reejecuta audit_data.py")
if str(audit.get("data_root")) != str(C.DATA_ROOT):
    sys.exit(f"La auditoría es de {audit.get('data_root')} y el dataset actual es {C.DATA_ROOT}: reejecuta audit_data.py")
newest = max((C.DATA_ROOT / rel).stat().st_mtime for rel in FINGERPRINT_FILES.values())
if p.stat().st_mtime < newest:
    sys.exit("data_audit.json es anterior a los archivos del dataset (auditoría obsoleta): reejecuta audit_data.py")
fp = dataset_fingerprint()
audit["data_fingerprint"] = {**fp, "stamped_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                             "audit_script_sha256": sha256_file(C.ML_DIR / "audit_data.py")}
p.write_text(json.dumps(audit, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
print("Auditoría sellada para", fp["data_version"])
