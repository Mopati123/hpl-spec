"""Typed semantic contract for development-change witness evidence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Mapping, Union

DEV_WITNESS_PROTOCOL_ID = "hpl.dev-witness"
DEV_WITNESS_PROTOCOL_VERSION = "1.0.0"


class DevWitnessStage(str, Enum):
    DEV_CHANGE = "dev_change"


@dataclass(frozen=True)
class DevWitnessContract:
    stage: DevWitnessStage
    attestation: str
    role: str
    proves_change_evidence_binding: bool = True
    implies_execution_authorization: bool = False


DEV_WITNESS_CONTRACTS: Mapping[DevWitnessStage, DevWitnessContract] = {
    DevWitnessStage.DEV_CHANGE: DevWitnessContract(
        stage=DevWitnessStage.DEV_CHANGE,
        attestation="dev_change_witness",
        role="development_change_attestation",
    )
}


def resolve_dev_witness_contract(stage: Union[str, DevWitnessStage]) -> DevWitnessContract:
    try:
        typed_stage = stage if isinstance(stage, DevWitnessStage) else DevWitnessStage(stage)
    except ValueError as exc:
        raise ValueError(f"unknown dev witness stage: {stage}") from exc
    return DEV_WITNESS_CONTRACTS[typed_stage]


def validate_dev_witness_pair(stage: Union[str, DevWitnessStage], attestation: str) -> DevWitnessContract:
    contract = resolve_dev_witness_contract(stage)
    if attestation != contract.attestation:
        raise ValueError(
            "dev witness attestation mismatch: "
            f"stage={contract.stage.value} expected={contract.attestation} observed={attestation}"
        )
    return contract


def validate_dev_witness_record(record: Mapping[str, object]) -> DevWitnessContract:
    stage = record.get("stage")
    attestation = record.get("attestation")
    if not isinstance(stage, str):
        raise ValueError("dev witness stage must be a string")
    if not isinstance(attestation, str):
        raise ValueError("dev witness attestation must be a string")
    return validate_dev_witness_pair(stage, attestation)


def dev_witness_catalog() -> Dict[str, Dict[str, object]]:
    return {
        stage.value: {
            "attestation": contract.attestation,
            "role": contract.role,
            "proves_change_evidence_binding": contract.proves_change_evidence_binding,
            "implies_execution_authorization": contract.implies_execution_authorization,
        }
        for stage, contract in DEV_WITNESS_CONTRACTS.items()
    }
