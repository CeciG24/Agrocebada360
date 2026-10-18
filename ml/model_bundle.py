"""P4.7: empaquetado e inspección sin deserializar ni entrenar modelos.

python -m ml.model_bundle pack --model ... --schema ... --out ...
python -m ml.model_bundle inspect --bundle ...
"""
import argparse
import json
import platform
import shutil
from importlib import metadata
from pathlib import Path

from .artifact_contract import (
    ArtifactContractError, BUNDLE_VERSION, VERSION_FIELDS, filename, sha256,
    valid_digest, validate_feature_schema, verify_model_file,
)

MANIFEST_FILE = "model_manifest.json"
SCHEMA_FILE = "feature_schema.json"


def read_json(path):
    def no_duplicates(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ArtifactContractError(f"Clave JSON duplicada: {key}")
            obj[key] = value
        return obj

    def reject_constant(value):
        raise ArtifactContractError(f"Constante JSON no finita: {value}")

    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream, object_pairs_hook=no_duplicates, parse_constant=reject_constant)


def member(root, name, suffix):
    filename(name, suffix)
    path = root / name
    if not path.resolve().is_relative_to(root.resolve()):
        raise ArtifactContractError("Un archivo del paquete sale de su carpeta.")
    return path


def environment_report(declared):
    packages = {}
    for name, wanted in declared["packages"].items():
        try:
            current = metadata.version(name)
        except metadata.PackageNotFoundError:
            current = None
        packages[name] = {"declared": wanted, "current": current,
                          "matches": None if wanted is None else current == wanted}
    return {"python": {"declared": declared["python"], "current": platform.python_version(),
                        "matches": declared["python"] == platform.python_version()}, "packages": packages}


def inspect_bundle(bundle_path):
    root = Path(bundle_path)
    manifest = read_json(root / MANIFEST_FILE)
    if (not isinstance(manifest, dict) or manifest.get("bundle_format_version") != BUNDLE_VERSION
            or manifest.get("serialization") != "joblib"):
        raise ArtifactContractError("Formato de paquete o serialización incompatible.")
    model_path = member(root, manifest.get("model_file"), ".joblib")
    schema_path = member(root, manifest.get("feature_schema_file"), ".json")
    for path, field in ((model_path, "model_sha256"), (schema_path, "feature_schema_sha256")):
        if not valid_digest(manifest.get(field)) or sha256(path) != manifest[field]:
            raise ArtifactContractError(f"El paquete no verifica {field}.")
    schema = read_json(schema_path)
    validate_feature_schema(schema, delivery=True)
    if any(manifest.get(field) != schema[field] for field in VERSION_FIELDS):
        raise ArtifactContractError("Las versiones del manifest y schema no coinciden.")
    verify_model_file(model_path, schema)
    return {"status": "ARTIFACTS_VERIFIED", "bundle_format_version": BUNDLE_VERSION,
            **{field: schema[field] for field in VERSION_FIELDS},
            "model_file": model_path.name, "feature_schema_file": schema_path.name,
            "n_features": len(schema["features"]), "deserialized": False,
            "environment": environment_report(schema["environment"]),
            "data_provenance_checked": False,
            "note": "Integridad de archivos comprobada; no certifica entrenamiento, procedencia ni aptitud para API real."}


def create_bundle(model_path, schema_path, output):
    model_path, schema_path, output = Path(model_path), Path(schema_path), Path(output)
    schema = read_json(schema_path)
    validate_feature_schema(schema, delivery=True)
    verify_model_file(model_path, schema)
    if model_path.name in (SCHEMA_FILE, MANIFEST_FILE):
        raise ArtifactContractError("Nombres de archivos en conflicto.")
    # No se reemplazan entregas congeladas; una versión nueva necesita otra carpeta.
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(model_path, output / model_path.name)
    shutil.copyfile(schema_path, output / SCHEMA_FILE)
    copied_schema = read_json(output / SCHEMA_FILE)
    validate_feature_schema(copied_schema, delivery=True)
    verify_model_file(output / model_path.name, copied_schema)
    manifest = {"bundle_format_version": BUNDLE_VERSION, "serialization": "joblib",
                **{field: copied_schema[field] for field in VERSION_FIELDS},
                "model_file": model_path.name, "feature_schema_file": SCHEMA_FILE,
                "model_sha256": sha256(output / model_path.name),
                "feature_schema_sha256": sha256(output / SCHEMA_FILE)}
    # Se escribe al final: una copia interrumpida sin manifest no es un paquete válido.
    (output / MANIFEST_FILE).write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return inspect_bundle(output)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    pack = commands.add_parser("pack")
    pack.add_argument("--model", required=True)
    pack.add_argument("--schema", required=True)
    pack.add_argument("--out", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("--bundle", required=True)
    args = parser.parse_args(argv)
    try:
        report = (create_bundle(args.model, args.schema, args.out) if args.command == "pack"
                  else inspect_bundle(args.bundle))
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(1, f"Paquete rechazado: {exc}\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
