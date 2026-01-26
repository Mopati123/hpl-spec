"""Deterministic lowering from BackendIR to OpenQASM (subset)."""

from __future__ import annotations

import json
from typing import Dict, List

from ..trace import emit_witness_record
from .backend_ir import canonical_json, digest_text


DEFAULT_TIMESTAMP = "1970-01-01T00:00:00Z"


def lower_backend_ir_to_qasm(backend_ir: Dict[str, object]) -> str:
    lines: List[str] = [
        "OPENQASM 2.0;",
        "qreg q[1];",
        "creg c[1];",
    ]
    for op in _ops_from_backend_ir(backend_ir):
        cls = op.get("cls", "")
        if cls == "U":
            angle = _format_number(op.get("coefficient", 0.0))
            lines.append(f"ry({angle}) q[0];")
        elif cls == "M":
            lines.append("measure q[0] -> c[0];")
    return "\n".join(lines) + "\n"


def build_qasm_artifact(
    backend_ir: Dict[str, object],
    timestamp: str = DEFAULT_TIMESTAMP,
) -> Dict[str, object]:
    qasm = lower_backend_ir_to_qasm(backend_ir)
    qasm_digest = digest_text(qasm)
    witness_record = emit_witness_record(
        observer_id="papas",
        stage="qasm_lowering",
        artifact_digests={"qasm": qasm_digest},
        timestamp=timestamp,
        attestation="qasm_lowering_witness",
    )
    witness_json = canonical_json(witness_record)
    return {
        "qasm": qasm,
        "evidence": {
            "qasm_digest": qasm_digest,
            "papas_witness_record": witness_json,
            "papas_witness_digest": digest_text(witness_json),
        },
    }


def _ops_from_backend_ir(backend_ir: Dict[str, object]) -> List[Dict[str, object]]:
    ops = backend_ir.get("ops", [])
    if isinstance(ops, list):
        return [op for op in ops if isinstance(op, dict)]
    return []


def _format_number(value: object) -> str:
    return json.dumps(value)
