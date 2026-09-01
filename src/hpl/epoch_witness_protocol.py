"""Typed, versioned semantic contract for epoch-anchor witness evidence.

This protocol governs witnesses emitted by the standalone epoch-anchor producer.
It intentionally does not claim scheduler/runtime ``epoch_verification`` stages;
those remain owned by their producer-specific witness protocols.

An ``epoch_anchor`` witness attests to the deterministic digest of an epoch
anchor artifact. It does not, by itself, prove that a cryptographic signature
exists, that a signature was verified, or that execution is authorized.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Mapping, Union


EPOCH_WITNESS_PROTOCOL_ID = "hpl.epoch-witness"
EPOCH_WITNESS_PROTOCOL_VERSION = "1.0.0"


class EpochWitnessStage(str, Enum):
    EPOCH_ANCHOR = "epoch_anchor"


@dataclass(frozen=True)
class EpochWitnessContract:
    stage: EpochWitnessStage
    attestation: str
    role: str
    proves_anchor_digest: bool = False
    proves_signature_presence: bool = False
    proves_signature_verification: bool = False
    implies_execution_authorization: bool = False


EPOCH_WITNESS_CONTRACTS: Mapping[EpochWitnessStage, EpochWitnessContract] = {
    EpochWitnessStage.EPOCH_ANCHOR: EpochWitnessContract(
        stage=EpochWitnessStage.EPOCH_ANCHOR,
        attestation="epoch_anchor_witness",
        role="anchor_attestation",
        proves_anchor_digest=True,
        proves_signature_presence=False,
        proves_signature_verification=False,
        implies_execution_authorization=False,
    ),
}


def resolve_epoch_witness_contract(
    stage: Union[str, EpochWitnessStage],
) -> EpochWitnessContract:
    """Resolve an epoch witness stage or refuse unknown vocabulary."""

    try:
        typed_stage = stage if isinstance(stage, EpochWitnessStage) else EpochWitnessStage(stage)
    except ValueError as exc:
        raise ValueError(f"unknown epoch witness stage: {stage}") from exc
    return EPOCH_WITNESS_CONTRACTS[typed_stage]


def validate_epoch_witness_pair(
    stage: Union[str, EpochWitnessStage], attestation: str
) -> EpochWitnessContract:
    """Refuse a stage/attestation pair that violates epoch protocol v1."""

    contract = resolve_epoch_witness_contract(stage)
    if attestation != contract.attestation:
        raise ValueError(
            "epoch witness attestation mismatch: "
            f"stage={contract.stage.value} expected={contract.attestation} "
            f"observed={attestation}"
        )
    return contract


def validate_epoch_witness_record(record: Mapping[str, object]) -> EpochWitnessContract:
    """Validate semantic identity fields of a serialized epoch witness."""

    stage = record.get("stage")
    attestation = record.get("attestation")
    if not isinstance(stage, str):
        raise ValueError("epoch witness stage must be a string")
    if not isinstance(attestation, str):
        raise ValueError("epoch witness attestation must be a string")
    return validate_epoch_witness_pair(stage, attestation)


def epoch_witness_catalog() -> Dict[str, Dict[str, object]]:
    """Return a deterministic serialization-friendly view of protocol v1."""

    return {
        stage.value: {
            "attestation": contract.attestation,
            "role": contract.role,
            "proves_anchor_digest": contract.proves_anchor_digest,
            "proves_signature_presence": contract.proves_signature_presence,
            "proves_signature_verification": contract.proves_signature_verification,
            "implies_execution_authorization": contract.implies_execution_authorization,
        }
        for stage, contract in sorted(
            EPOCH_WITNESS_CONTRACTS.items(), key=lambda item: item[0].value
        )
    }
