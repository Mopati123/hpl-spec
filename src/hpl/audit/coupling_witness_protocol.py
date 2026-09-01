"""Typed, versioned semantic contract for coupling/topology witness evidence.

This protocol governs coupling-event witnesses emitted by the audit layer. A
coupling witness attests to deterministic event binding for a declared
cross-sector edge/projector relationship. It does not, by itself, prove that
the topology is globally valid, that all invariants hold, or that execution is
authorized.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Mapping, Union


COUPLING_WITNESS_PROTOCOL_ID = "hpl.coupling-witness"
COUPLING_WITNESS_PROTOCOL_VERSION = "1.0.0"


class CouplingWitnessStage(str, Enum):
    COUPLING_VALIDATION = "coupling_validation"


@dataclass(frozen=True)
class CouplingWitnessContract:
    stage: CouplingWitnessStage
    attestation: str
    role: str
    proves_event_binding: bool = False
    proves_global_topology_validity: bool = False
    proves_all_invariants: bool = False
    implies_execution_authorization: bool = False


COUPLING_WITNESS_CONTRACTS: Mapping[CouplingWitnessStage, CouplingWitnessContract] = {
    CouplingWitnessStage.COUPLING_VALIDATION: CouplingWitnessContract(
        stage=CouplingWitnessStage.COUPLING_VALIDATION,
        attestation="coupling_event_witness",
        role="coupling_event_attestation",
        proves_event_binding=True,
        proves_global_topology_validity=False,
        proves_all_invariants=False,
        implies_execution_authorization=False,
    ),
}


def resolve_coupling_witness_contract(
    stage: Union[str, CouplingWitnessStage],
) -> CouplingWitnessContract:
    try:
        typed_stage = (
            stage if isinstance(stage, CouplingWitnessStage) else CouplingWitnessStage(stage)
        )
    except ValueError as exc:
        raise ValueError(f"unknown coupling witness stage: {stage}") from exc
    return COUPLING_WITNESS_CONTRACTS[typed_stage]


def validate_coupling_witness_pair(
    stage: Union[str, CouplingWitnessStage], attestation: str
) -> CouplingWitnessContract:
    contract = resolve_coupling_witness_contract(stage)
    if attestation != contract.attestation:
        raise ValueError(
            "coupling witness attestation mismatch: "
            f"stage={contract.stage.value} expected={contract.attestation} "
            f"observed={attestation}"
        )
    return contract


def validate_coupling_witness_record(
    record: Mapping[str, object],
) -> CouplingWitnessContract:
    stage = record.get("stage")
    attestation = record.get("attestation")
    if not isinstance(stage, str):
        raise ValueError("coupling witness stage must be a string")
    if not isinstance(attestation, str):
        raise ValueError("coupling witness attestation must be a string")
    return validate_coupling_witness_pair(stage, attestation)


def coupling_witness_catalog() -> Dict[str, Dict[str, object]]:
    return {
        stage.value: {
            "attestation": contract.attestation,
            "role": contract.role,
            "proves_event_binding": contract.proves_event_binding,
            "proves_global_topology_validity": contract.proves_global_topology_validity,
            "proves_all_invariants": contract.proves_all_invariants,
            "implies_execution_authorization": contract.implies_execution_authorization,
        }
        for stage, contract in sorted(
            COUPLING_WITNESS_CONTRACTS.items(), key=lambda item: item[0].value
        )
    }
