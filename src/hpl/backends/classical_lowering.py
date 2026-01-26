"""Deterministic lowering from ProgramIR to BackendIR (classical)."""

from __future__ import annotations

from typing import Dict, List

from ..trace import emit_witness_record
from .backend_ir import BackendIR, canonical_json, digest_program_ir, digest_text


DEFAULT_TIMESTAMP = "1970-01-01T00:00:00Z"


def lower_program_ir_to_backend_ir(
    program_ir: Dict[str, object],
    target: str = "classical",
    timestamp: str = DEFAULT_TIMESTAMP,
) -> BackendIR:
    ops = _build_ops(program_ir)
    program_digest = digest_program_ir(program_ir)
    metadata = {
        "program_id": str(program_ir.get("program_id", "unknown")),
        "lowering_target": target,
    }

    core = {
        "backend_target": target,
        "program_digest": program_digest,
        "ops": ops,
        "metadata": metadata,
    }
    core_digest = digest_text(canonical_json(core))

    witness_record = emit_witness_record(
        observer_id="papas",
        stage="backend_lowering",
        artifact_digests={"backend_ir_core": core_digest},
        timestamp=timestamp,
        attestation="backend_ir_witness",
    )
    witness_json = canonical_json(witness_record)
    evidence = {
        "backend_ir_core_digest": core_digest,
        "papas_witness_record": witness_json,
        "papas_witness_digest": digest_text(witness_json),
        "stage": "backend_lowering",
    }

    return BackendIR(
        backend_target=target,
        program_digest=program_digest,
        ops=ops,
        metadata=metadata,
        evidence=evidence,
    )


def _build_ops(program_ir: Dict[str, object]) -> List[Dict[str, object]]:
    hamiltonian = program_ir.get("hamiltonian", {})
    terms = hamiltonian.get("terms", []) if isinstance(hamiltonian, dict) else []
    if not isinstance(terms, list):
        return []
    ops: List[Dict[str, object]] = []
    for idx, term in enumerate(terms):
        if not isinstance(term, dict):
            continue
        ops.append(
            {
                "index": idx,
                "operator_id": str(term.get("operator_id", "unknown")),
                "cls": str(term.get("cls", "unknown")),
                "coefficient": term.get("coefficient", 0.0),
            }
        )
    return ops
