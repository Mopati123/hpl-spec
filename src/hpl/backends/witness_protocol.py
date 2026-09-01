"""Typed, versioned semantic contract for backend-lowering witness evidence.

This protocol governs witnesses emitted by backend transformation producers.
It preserves the existing serialized witness-record shape and does not elevate
transformation evidence into scheduler authority, execution authority, or a
claim of semantic correctness beyond deterministic artifact binding.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Mapping, Union


BACKEND_WITNESS_PROTOCOL_ID = "hpl.backend-witness"
BACKEND_WITNESS_PROTOCOL_VERSION = "1.0.0"


class BackendWitnessStage(str, Enum):
    BACKEND_LOWERING = "backend_lowering"
    QASM_LOWERING = "qasm_lowering"


@dataclass(frozen=True)
class BackendWitnessContract:
    stage: BackendWitnessStage
    attestation: str
    role: str
    proves_artifact_binding: bool = False
    proves_semantic_equivalence: bool = False
    implies_execution_authorization: bool = False


BACKEND_WITNESS_CONTRACTS: Mapping[BackendWitnessStage, BackendWitnessContract] = {
    BackendWitnessStage.BACKEND_LOWERING: BackendWitnessContract(
        stage=BackendWitnessStage.BACKEND_LOWERING,
        attestation="backend_ir_witness",
        role="backend_transformation",
        proves_artifact_binding=True,
        proves_semantic_equivalence=False,
        implies_execution_authorization=False,
    ),
    BackendWitnessStage.QASM_LOWERING: BackendWitnessContract(
        stage=BackendWitnessStage.QASM_LOWERING,
        attestation="qasm_lowering_witness",
        role="qasm_transformation",
        proves_artifact_binding=True,
        proves_semantic_equivalence=False,
        implies_execution_authorization=False,
    ),
}


def resolve_backend_witness_contract(
    stage: Union[str, BackendWitnessStage],
) -> BackendWitnessContract:
    """Resolve a backend witness stage or refuse unknown vocabulary."""

    try:
        typed_stage = (
            stage if isinstance(stage, BackendWitnessStage) else BackendWitnessStage(stage)
        )
    except ValueError as exc:
        raise ValueError(f"unknown backend witness stage: {stage}") from exc
    return BACKEND_WITNESS_CONTRACTS[typed_stage]


def validate_backend_witness_pair(
    stage: Union[str, BackendWitnessStage], attestation: str
) -> BackendWitnessContract:
    """Refuse a stage/attestation pair that violates backend protocol v1."""

    contract = resolve_backend_witness_contract(stage)
    if attestation != contract.attestation:
        raise ValueError(
            "backend witness attestation mismatch: "
            f"stage={contract.stage.value} expected={contract.attestation} "
            f"observed={attestation}"
        )
    return contract


def validate_backend_witness_record(
    record: Mapping[str, object],
) -> BackendWitnessContract:
    """Validate semantic identity fields of a serialized backend witness."""

    stage = record.get("stage")
    attestation = record.get("attestation")
    if not isinstance(stage, str):
        raise ValueError("backend witness stage must be a string")
    if not isinstance(attestation, str):
        raise ValueError("backend witness attestation must be a string")
    return validate_backend_witness_pair(stage, attestation)


def backend_witness_catalog() -> Dict[str, Dict[str, object]]:
    """Return a deterministic serialization-friendly view of protocol v1."""

    return {
        stage.value: {
            "attestation": contract.attestation,
            "role": contract.role,
            "proves_artifact_binding": contract.proves_artifact_binding,
            "proves_semantic_equivalence": contract.proves_semantic_equivalence,
            "implies_execution_authorization": contract.implies_execution_authorization,
        }
        for stage, contract in sorted(
            BACKEND_WITNESS_CONTRACTS.items(), key=lambda item: item[0].value
        )
    }
