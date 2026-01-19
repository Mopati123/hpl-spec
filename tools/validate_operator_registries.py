from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "docs" / "spec" / "06_operator_registry_schema.json"


def main() -> int:
    schema = _load_schema()
    registry_paths = _resolve_registry_paths(sys.argv[1:])
    results = []
    all_ok = True

    for path in registry_paths:
        errors = validate_registry_file(path, schema)
        ok = not errors
        all_ok = all_ok and ok
        results.append({"path": str(path), "ok": ok, "errors": errors})
        status = "PASS" if ok else "FAIL"
        print(f"{status}: {path}")
        for err in errors:
            print(f"  - {err}")

    summary = {"ok": all_ok, "results": results}
    print(json.dumps(summary, indent=2))
    return 0 if all_ok else 1


def _load_schema() -> Dict:
    if not SCHEMA_PATH.exists():
        raise SystemExit(f"Schema not found: {SCHEMA_PATH}")
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _resolve_registry_paths(args: List[str]) -> List[Path]:
    if args:
        return [Path(arg).resolve() for arg in args]

    registries = []
    for folder in ROOT.iterdir():
        if folder.is_dir() and folder.name.endswith("_H"):
            candidate = folder / "operators" / "registry.json"
            if candidate.exists():
                registries.append(candidate)
    return sorted(registries)


def validate_registry_file(path: Path, schema: Dict) -> List[str]:
    errors: List[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"Invalid JSON: {exc}"]

    _validate_object(data, schema, errors, "root")
    return errors


def _validate_object(data: object, schema: Dict, errors: List[str], ctx: str) -> None:
    if schema.get("type") != "object":
        errors.append(f"{ctx}: schema expects object")
        return
    if not isinstance(data, dict):
        errors.append(f"{ctx}: expected object")
        return

    required = schema.get("required", [])
    for field in required:
        if field not in data:
            errors.append(f"{ctx}: missing required field '{field}'")

    properties = schema.get("properties", {})
    for key, value in data.items():
        prop_schema = properties.get(key)
        if prop_schema is None:
            if schema.get("additionalProperties") is False:
                errors.append(f"{ctx}: unknown field '{key}'")
            continue
        _validate_value(value, prop_schema, errors, f"{ctx}.{key}")


def _validate_value(value: object, schema: Dict, errors: List[str], ctx: str) -> None:
    schema_type = schema.get("type")
    if schema_type == "string":
        if not isinstance(value, str):
            errors.append(f"{ctx}: expected string")
        if "enum" in schema and value not in schema["enum"]:
            errors.append(f"{ctx}: value '{value}' not in enum")
        return

    if schema_type == "object":
        _validate_object(value, schema, errors, ctx)
        return

    if schema_type == "array":
        if not isinstance(value, list):
            errors.append(f"{ctx}: expected array")
            return
        item_schema = schema.get("items", {})
        for idx, item in enumerate(value):
            _validate_value(item, item_schema, errors, f"{ctx}[{idx}]")
        return

    errors.append(f"{ctx}: unsupported schema type '{schema_type}'")


if __name__ == "__main__":
    raise SystemExit(main())
