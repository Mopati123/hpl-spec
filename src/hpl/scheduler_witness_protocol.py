"""Typed, versioned semantic contract for scheduler witness vocabulary.

This module governs scheduler-produced witness stage identities without changing
the serialized witness-record shape. In particular, ``scheduler_plan`` records
that the scheduler produced a terminal planning decision; it does not by itself
mean the plan was approved for execution. Execution authority remains encoded
by the scheduler plan status/token contract and enforced by RuntimeEngine.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Mapping, Union


SCHEDULER_WITNESS_PROTOCOL_ID = "hpl.scheduler-witness"
SCHEDULER_WITNESS_PROTOCOL_VERSION = "1.0.0"


class SchedulerWitnessStage(str, Enum):
    EPOCH_VERIFICATION = "epoch_verification"
    SCHEDULER_PLAN = "scheduler_plan"


@dataclass(frozen=True)
class SchedulerWitnessContract:
    stage: SchedulerWitnessStage
    attestation: str
    role: str
    terminal_planning_decision: bool = False
    implies_execution_authorization: bool = False


SCHEDULER_WITNESS_CONTRACTS: Mapping[
    SchedulerWitnessStage, SchedulerWitnessContract
] = {
    SchedulerWitnessStage.EPOCH_VERIFICATION: SchedulerWitnessContract(
        stage=SchedulerWitnessStage.EPOCH_VERIFICATION,
        attestation="epoch_verification_witness",
        role="verification",
    ),
    SchedulerWitnessStage.SCHEDULER_PLAN: SchedulerWitnessContract(
        stage=SchedulerWitnessStage.SCHEDULER_PLAN,
        attestation="scheduler_plan_witness",
        role="planning_decision",
        terminal_planning_decision=True,
        implies_execution_authorization=False,
    ),
}


def resolve_scheduler_witness_contract(
    stage: Union[str, SchedulerWitnessStage],
) -> SchedulerWitnessContract:
    """Resolve a scheduler witness stage or refuse unknown vocabulary."""

    try:
        typed_stage = (
            stage if isinstance(stage, SchedulerWitnessStage) else SchedulerWitnessStage(stage)
        )
    except ValueError as exc:
        raise ValueError(f"unknown scheduler witness stage: {stage}") from exc
    return SCHEDULER_WITNESS_CONTRACTS[typed_stage]


def validate_scheduler_witness_pair(
    stage: Union[str, SchedulerWitnessStage], attestation: str
) -> SchedulerWitnessContract:
    """Refuse a stage/attestation pair that violates scheduler protocol v1."""

    contract = resolve_scheduler_witness_contract(stage)
    if attestation != contract.attestation:
        raise ValueError(
            "scheduler witness attestation mismatch: "
            f"stage={contract.stage.value} expected={contract.attestation} "
            f"observed={attestation}"
        )
    return contract


def validate_scheduler_witness_record(
    record: Mapping[str, object],
) -> SchedulerWitnessContract:
    """Validate semantic identity fields of a serialized scheduler witness."""

    stage = record.get("stage")
    attestation = record.get("attestation")
    if not isinstance(stage, str):
        raise ValueError("scheduler witness stage must be a string")
    if not isinstance(attestation, str):
        raise ValueError("scheduler witness attestation must be a string")
    return validate_scheduler_witness_pair(stage, attestation)


def scheduler_witness_catalog() -> Dict[str, Dict[str, object]]:
    """Return a deterministic serialization-friendly view of protocol v1."""

    return {
        stage.value: {
            "attestation": contract.attestation,
            "role": contract.role,
            "terminal_planning_decision": contract.terminal_planning_decision,
            "implies_execution_authorization": contract.implies_execution_authorization,
        }
        for stage, contract in sorted(
            SCHEDULER_WITNESS_CONTRACTS.items(), key=lambda item: item[0].value
        )
    }
