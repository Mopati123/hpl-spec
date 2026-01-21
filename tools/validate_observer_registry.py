from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
OBSERVERS_PATH = ROOT / "observers_H" / "manifests" / "observers.json"
TRACE_SCHEMA_PATH = ROOT / "audit_H" / "manifests" / "trace_schema.json"


def main() -> int:
    errors = []
    errors.extend(_validate_observers_registry(OBSERVERS_PATH))
    errors.extend(_validate_trace_schema(TRACE_SCHEMA_PATH))

    ok = not errors
    status = "PASS" if ok else "FAIL"
    print(f"{status}: observer registry validation")
    for err in errors:
        print(f"  - {err}")
    return 0 if ok else 1


def _validate_observers_registry(path: Path) -> List[str]:
    errors: List[str] = []
    if not path.exists():
        return [f"Observer registry not found: {path}"]

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"Invalid observer registry JSON: {exc}"]

    observers = data.get("observers", [])
    if not isinstance(observers, list):
        return ["Observer registry: 'observers' must be a list"]

    papas = next((o for o in observers if o.get("id") == "papas"), None)
    if not papas:
        errors.append("Observer registry: missing 'papas' observer")
        return errors

    prohibitions = papas.get("prohibitions", {})
    permissions = papas.get("permissions", {})

    if prohibitions.get("can_authorize_collapse") is not False:
        errors.append("Papas must prohibit collapse authority")
    if prohibitions.get("can_define_semantics") is not False:
        errors.append("Papas must prohibit semantic authority")
    if prohibitions.get("can_override_invariants") is not False:
        errors.append("Papas must prohibit invariant overrides")

    if permissions.get("can_observe") is not True:
        errors.append("Papas must allow observation")
    if permissions.get("can_emit_trace") is not True:
        errors.append("Papas must allow trace emission")
    if permissions.get("can_emit_witness_attestation") is not True:
        errors.append("Papas must allow witness attestations")

    return errors


def _validate_trace_schema(path: Path) -> List[str]:
    errors: List[str] = []
    if not path.exists():
        return [f"Trace schema not found: {path}"]

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"Invalid trace schema JSON: {exc}"]

    record = data.get("WitnessRecord")
    if not isinstance(record, dict):
        return ["Trace schema: missing WitnessRecord"]

    props = record.get("properties", {})
    observer_id = props.get("observer_id", {})
    if "papas" not in observer_id.get("enum", []):
        errors.append("Trace schema: WitnessRecord must allow observer_id 'papas'")

    return errors


if __name__ == "__main__":
    raise SystemExit(main())
