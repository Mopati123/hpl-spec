from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from tools import validate_operator_registries


ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class OperatorRegistry:
    operators: Dict[str, Dict[str, object]]
    sources: List[Path]
    errors: List[str]


def resolve_registry_paths(
    root: Path = ROOT, registry_paths: Optional[Sequence[Path]] = None
) -> List[Path]:
    if registry_paths:
        return sorted(Path(path).resolve() for path in registry_paths)

    registries: List[Path] = []
    for folder in root.iterdir():
        if folder.is_dir() and folder.name.endswith("_H"):
            candidate = folder / "operators" / "registry.json"
            if candidate.exists():
                registries.append(candidate.resolve())
    return sorted(registries)


def load_operator_registries(
    root: Path = ROOT, registry_paths: Optional[Sequence[Path]] = None
) -> OperatorRegistry:
    sources = resolve_registry_paths(root, registry_paths)
    errors: List[str] = []
    operators: Dict[str, Dict[str, object]] = {}

    if not sources:
        errors.append("operator registries not found")
        return OperatorRegistry(operators=operators, sources=sources, errors=errors)

    schema = validate_operator_registries._load_schema()
    for path in sources:
        validation_errors = validate_operator_registries.validate_registry_file(path, schema)
        if validation_errors:
            errors.extend([f"{path}: {err}" for err in validation_errors])

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{path}: invalid JSON ({exc})")
            continue

        entries = payload.get("operators", [])
        if not isinstance(entries, list):
            errors.append(f"{path}: operators must be a list")
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                errors.append(f"{path}: operator entry must be an object")
                continue
            operator_id = entry.get("id")
            if not isinstance(operator_id, str) or not operator_id.strip():
                errors.append(f"{path}: operator id missing or invalid")
                continue
            if operator_id in operators:
                errors.append(f"{path}: duplicate operator id '{operator_id}'")
                continue
            operators[operator_id] = dict(entry)

    return OperatorRegistry(operators=operators, sources=sources, errors=errors)


def extract_operator_ids(program_ir: Dict[str, object]) -> List[str]:
    ids: List[str] = []
    hamiltonian = program_ir.get("hamiltonian", {})
    terms = hamiltonian.get("terms", []) if isinstance(hamiltonian, dict) else []
    if isinstance(terms, list):
        for term in terms:
            if isinstance(term, dict) and term.get("operator_id"):
                ids.append(str(term["operator_id"]))

    operators = program_ir.get("operators")
    if isinstance(operators, dict):
        ids.extend(str(key) for key in operators.keys())

    return sorted({item for item in ids if item.strip()})


def validate_program_operators(
    program_ir: Dict[str, object], registry: OperatorRegistry, enforce: bool
) -> Tuple[bool, List[str]]:
    if not enforce:
        return True, []
    errors = list(registry.errors)
    operator_ids = extract_operator_ids(program_ir)
    missing = sorted(set(operator_ids) - set(registry.operators.keys()))
    if missing:
        errors.append(f"operator registry missing: {', '.join(missing)}")
    return not errors, errors


def validate_plan_operators(
    steps: Iterable[Dict[str, object]], registry: OperatorRegistry, enforce: bool
) -> Tuple[bool, List[str]]:
    if not enforce:
        return True, []
    errors = list(registry.errors)
    operator_ids: List[str] = []
    for step in steps:
        operator_id = step.get("operator_id")
        if operator_id:
            operator_ids.append(str(operator_id))
    missing = sorted(set(operator_ids) - set(registry.operators.keys()))
    if missing:
        errors.append(f"operator registry missing: {', '.join(missing)}")
    return not errors, errors
