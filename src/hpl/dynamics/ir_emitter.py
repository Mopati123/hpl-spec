"""IR emitter and schema validation (ProgramIR)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

from ..ast import Node
from ..errors import ValidationError
from ..trace import TraceCollector


def emit_program_ir(
    program: List[Node],
    program_id: str = "unknown",
    trace: TraceCollector | None = None,
) -> Dict:
    terms = _collect_terms(program)
    operator_ids = [term[0] for term in terms]

    ir = {
        "program_id": program_id,
        "hamiltonian": {
            "terms": [
                {
                    "operator_id": operator_id,
                    "cls": "C",
                    "coefficient": coefficient,
                }
                for operator_id, coefficient, _ in terms
            ]
        },
        "operators": {
            operator_id: {
                "type": "unspecified",
                "commutes_with": [],
                "backend_map": [],
            }
            for operator_id in operator_ids
        },
        "invariants": [],
        "scheduler": {
            "collapse_policy": "unspecified",
            "authorized_observers": [],
        },
    }

    validate_program_ir(ir)
    if trace:
        trace.record_phase(program, "axiomatic")
        for idx, (operator_id, _coefficient, node) in enumerate(terms):
            trace.record_ir_term(idx, node, "axiomatic", operator_id)
    return ir


def validate_program_ir(ir: Dict) -> None:
    schema = _load_schema()
    _validate_program_ir_schema(ir, schema)


def _collect_terms(program: List[Node]) -> List[Tuple[str, float, Node]]:
    terms: List[Tuple[str, float, Node]] = []
    for form in program:
        _collect_terms_from_node(form, terms)
    return terms


def _collect_terms_from_node(node: Node, terms: List[Tuple[str, float, Node]]) -> None:
    if node.is_atom:
        return
    items = node.as_list()
    if not items:
        return
    head = items[0]
    if head.is_atom and head.value == "hamiltonian":
        for item in items[1:]:
            term = _term_from_node(item)
            if term is not None:
                terms.append(term)
        return
    for item in items:
        _collect_terms_from_node(item, terms)


def _term_from_node(node: Node) -> Tuple[str, float, Node] | None:
    if node.is_atom:
        return None
    items = node.as_list()
    if len(items) != 3:
        return None
    head = items[0]
    if head.is_atom and head.value == "term":
        operator_ref = items[1]
        coefficient = items[2]
        if operator_ref.is_atom and isinstance(operator_ref.value, str) and coefficient.is_atom:
            if isinstance(coefficient.value, (int, float)):
                return operator_ref.value, float(coefficient.value), node
    return None


def _load_schema() -> Dict:
    root = Path(__file__).resolve().parents[3]
    schema_path = root / "docs" / "spec" / "04_ir_schema.json"
    with schema_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _validate_program_ir_schema(ir: Dict, schema: Dict) -> None:
    if not isinstance(ir, dict):
        raise ValidationError("IR must be an object")
    required = schema.get("required", [])
    for key in required:
        if key not in ir:
            raise ValidationError(f"Missing required field: {key}")

    _require_type(ir.get("program_id"), str, "program_id")
    _validate_hamiltonian(ir.get("hamiltonian"), schema)
    _validate_operators(ir.get("operators"))
    _validate_invariants(ir.get("invariants"))
    _validate_scheduler(ir.get("scheduler"))

    allowed_keys = set(schema.get("properties", {}).keys())
    for key in ir.keys():
        if key not in allowed_keys:
            raise ValidationError(f"Unknown IR field: {key}")


def _require_type(value, expected, field: str) -> None:
    if not isinstance(value, expected):
        raise ValidationError(f"Field '{field}' must be {expected.__name__}")


def _validate_hamiltonian(hamiltonian, schema: Dict) -> None:
    if not isinstance(hamiltonian, dict):
        raise ValidationError("hamiltonian must be an object")
    if "terms" not in hamiltonian:
        raise ValidationError("hamiltonian.terms is required")
    terms = hamiltonian.get("terms")
    if not isinstance(terms, list):
        raise ValidationError("hamiltonian.terms must be an array")
    enum_values = (
        schema.get("properties", {})
        .get("hamiltonian", {})
        .get("properties", {})
        .get("terms", {})
        .get("items", {})
        .get("properties", {})
        .get("cls", {})
        .get("enum", [])
    )
    for term in terms:
        if not isinstance(term, dict):
            raise ValidationError("term must be an object")
        for key in ("operator_id", "cls", "coefficient"):
            if key not in term:
                raise ValidationError(f"term missing field: {key}")
        _require_type(term.get("operator_id"), str, "term.operator_id")
        _require_type(term.get("cls"), str, "term.cls")
        if term.get("cls") not in enum_values:
            raise ValidationError("term.cls not in enum")
        if not isinstance(term.get("coefficient"), (int, float)):
            raise ValidationError("term.coefficient must be a number")


def _validate_operators(operators) -> None:
    if not isinstance(operators, dict):
        raise ValidationError("operators must be an object")
    for operator_id, operator in operators.items():
        _require_type(operator_id, str, "operators.key")
        if not isinstance(operator, dict):
            raise ValidationError("operator entry must be an object")
        for key in ("type", "commutes_with", "backend_map"):
            if key not in operator:
                raise ValidationError(f"operator missing field: {key}")
        _require_type(operator.get("type"), str, "operator.type")
        if not isinstance(operator.get("commutes_with"), list):
            raise ValidationError("operator.commutes_with must be an array")
        if not isinstance(operator.get("backend_map"), list):
            raise ValidationError("operator.backend_map must be an array")


def _validate_invariants(invariants) -> None:
    if not isinstance(invariants, list):
        raise ValidationError("invariants must be an array")
    for item in invariants:
        if not isinstance(item, dict):
            raise ValidationError("invariant entry must be an object")
        for key in ("id", "expression"):
            if key not in item:
                raise ValidationError(f"invariant missing field: {key}")
        _require_type(item.get("id"), str, "invariant.id")
        _require_type(item.get("expression"), str, "invariant.expression")


def _validate_scheduler(scheduler) -> None:
    if not isinstance(scheduler, dict):
        raise ValidationError("scheduler must be an object")
    for key in ("collapse_policy", "authorized_observers"):
        if key not in scheduler:
            raise ValidationError(f"scheduler missing field: {key}")
    _require_type(scheduler.get("collapse_policy"), str, "scheduler.collapse_policy")
    if not isinstance(scheduler.get("authorized_observers"), list):
        raise ValidationError("scheduler.authorized_observers must be an array")
