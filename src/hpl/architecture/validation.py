"""Refusal-first validation for ArchitectureSpec and ArchitectureIR."""

from __future__ import annotations

from typing import Any, Dict, Iterable

from ..errors import ValidationError
from .federation_contract import (
    EVIDENCE_REQUIRED,
    EXECUTION_OWNER,
    RECONCILIATION_REQUIRED,
)
from .models import ArchitectureIR, ArchitectureSpec

_REQUIRED_SPEC_COLLECTIONS = (
    "states",
    "observables",
    "dynamics",
    "proposals",
    "constraints",
    "invariants",
    "authorities",
    "effects",
    "evidence",
    "reconciliation",
)
_OPERATOR_SPEC_COLLECTIONS = (
    "observables",
    "dynamics",
    "proposals",
    "constraints",
    "authorities",
    "effects",
    "evidence",
    "reconciliation",
)


def _require_nonempty_string(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field} must be a non-empty string")


def _validate_id_collection(items: Iterable[Dict[str, Any]], field: str, *, allow_empty: bool = True) -> None:
    items = list(items)
    if not allow_empty and not items:
        raise ValidationError(f"{field} must not be empty")
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValidationError(f"{field} entries must be objects")
        item_id = item.get("id")
        _require_nonempty_string(item_id, f"{field}.id")
        if item_id in seen:
            raise ValidationError(f"duplicate {field} id: {item_id}")
        seen.add(item_id)


def validate_architecture_spec(spec: ArchitectureSpec) -> None:
    if not isinstance(spec, ArchitectureSpec):
        raise ValidationError("architecture spec must be ArchitectureSpec")
    _require_nonempty_string(spec.architecture_id, "architecture_id")
    _require_nonempty_string(spec.domain, "domain")
    for field in _REQUIRED_SPEC_COLLECTIONS:
        value = getattr(spec, field)
        if not isinstance(value, list):
            raise ValidationError(f"{field} must be an array")
        _validate_id_collection(value, field)

    global_operator_ids = {}
    for field in _OPERATOR_SPEC_COLLECTIONS:
        for item in getattr(spec, field):
            item_id = item["id"]
            previous = global_operator_ids.get(item_id)
            if previous is not None:
                raise ValidationError(
                    f"operator id '{item_id}' is declared in both {previous} and {field}"
                )
            global_operator_ids[item_id] = field

    if not spec.authorities:
        raise ValidationError("authorities must declare scheduler-owned execution authority")
    if EVIDENCE_REQUIRED and not spec.evidence:
        raise ValidationError("evidence contract is required")
    if RECONCILIATION_REQUIRED and not spec.reconciliation:
        raise ValidationError("reconciliation contract is required")
    for authority in spec.authorities:
        if authority.get("kind") == "execution" and authority.get("owner") != EXECUTION_OWNER:
            raise ValidationError(f"execution authority owner must be {EXECUTION_OWNER}")
    if not any(a.get("kind") == "execution" for a in spec.authorities):
        raise ValidationError("execution authority declaration is required")


def validate_architecture_ir(ir: ArchitectureIR) -> None:
    if not isinstance(ir, ArchitectureIR):
        raise ValidationError("architecture IR must be ArchitectureIR")
    _require_nonempty_string(ir.architecture_id, "architecture_id")
    _require_nonempty_string(ir.domain, "domain")
    _require_nonempty_string(ir.source_digest, "source_digest")
    _validate_id_collection(ir.operators, "operators")
    _validate_id_collection(ir.invariants, "invariants")
    if ir.authority.get("execution_owner") != EXECUTION_OWNER:
        raise ValidationError("ArchitectureIR cannot mint or reassign execution authority")
    if ir.evidence_contract.get("required", False) is not EVIDENCE_REQUIRED:
        raise ValidationError("ArchitectureIR evidence requirement must match federation contract")
    if ir.reconciliation_contract.get("required", False) is not RECONCILIATION_REQUIRED:
        raise ValidationError("ArchitectureIR reconciliation requirement must match federation contract")
