"""Deterministic ArchitectureSpec -> ArchitectureIR -> HPL ProgramIR compiler."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List

from ..dynamics.ir_emitter import validate_program_ir
from .models import ArchitectureIR, ArchitectureSpec
from .validation import validate_architecture_ir, validate_architecture_spec

_CLASS_MAP = {
    "dynamics": "U",
    "observable": "M",
    "proposal": "Ω",
    "constraint": "C",
    "invariant": "I",
    "authority": "A",
    "effect": "C",
    "evidence": "M",
    "reconciliation": "M",
}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _normalize_operator(item: Dict[str, Any], kind: str) -> Dict[str, Any]:
    return {
        "id": item["id"],
        "kind": kind,
        "class": _CLASS_MAP[kind],
        "coefficient": float(item.get("coefficient", 1.0)),
        "commutes_with": sorted(set(item.get("commutes_with", []))),
        "backend_map": sorted(set(item.get("backend_map", []))),
        "type": str(item.get("type", kind)),
    }


def compile_architecture_spec(spec: ArchitectureSpec | Dict[str, Any]) -> ArchitectureIR:
    if isinstance(spec, dict):
        raw = spec
        spec = ArchitectureSpec.from_dict(spec)
    else:
        raw = {
            "architecture_id": spec.architecture_id,
            "domain": spec.domain,
            "states": spec.states,
            "observables": spec.observables,
            "dynamics": spec.dynamics,
            "proposals": spec.proposals,
            "constraints": spec.constraints,
            "invariants": spec.invariants,
            "authorities": spec.authorities,
            "effects": spec.effects,
            "evidence": spec.evidence,
            "reconciliation": spec.reconciliation,
            "metadata": spec.metadata,
        }
    validate_architecture_spec(spec)

    operators: List[Dict[str, Any]] = []
    for field, kind in (
        (spec.dynamics, "dynamics"),
        (spec.observables, "observable"),
        (spec.proposals, "proposal"),
        (spec.constraints, "constraint"),
        (spec.authorities, "authority"),
        (spec.effects, "effect"),
        (spec.evidence, "evidence"),
        (spec.reconciliation, "reconciliation"),
    ):
        operators.extend(_normalize_operator(item, kind) for item in field)
    operators.sort(key=lambda item: (item["kind"], item["id"]))

    ir = ArchitectureIR(
        architecture_id=spec.architecture_id,
        domain=spec.domain,
        states=sorted(spec.states, key=lambda item: item["id"]),
        observables=sorted(spec.observables, key=lambda item: item["id"]),
        operators=operators,
        invariants=sorted(spec.invariants, key=lambda item: item["id"]),
        authority={
            "execution_owner": "hpl.scheduler",
            "declared_authorities": sorted(a["id"] for a in spec.authorities),
        },
        evidence_contract={
            "required": True,
            "operators": sorted(item["id"] for item in spec.evidence),
        },
        reconciliation_contract={
            "required": True,
            "operators": sorted(item["id"] for item in spec.reconciliation),
        },
        source_digest=_digest(raw),
    )
    validate_architecture_ir(ir)
    return ir


def lower_architecture_ir_to_program_ir(ir: ArchitectureIR) -> Dict[str, Any]:
    validate_architecture_ir(ir)
    terms = []
    operators: Dict[str, Dict[str, Any]] = {}
    for operator in ir.operators:
        operator_id = operator["id"]
        terms.append({
            "operator_id": operator_id,
            "cls": operator["class"],
            "coefficient": operator["coefficient"],
        })
        operators[operator_id] = {
            "type": operator["type"],
            "commutes_with": operator["commutes_with"],
            "backend_map": operator["backend_map"],
        }

    program_ir = {
        "program_id": ir.architecture_id,
        "hamiltonian": {"terms": terms},
        "operators": operators,
        "invariants": [
            {"id": item["id"], "expression": str(item.get("expression", "true"))}
            for item in ir.invariants
        ],
        "scheduler": {
            "collapse_policy": "architecture_ir_scheduler_sovereignty",
            "authorized_observers": [],
        },
    }
    validate_program_ir(program_ir)
    return program_ir
