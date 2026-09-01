"""Typed, versioned semantic contract for deterministic constraint-refusal evidence.

Constraint witnesses use a distinct wire shape from attestation records: they
contain a deterministic witness_id, stage, refusal reasons, artifact digests,
and observer identity, but no attestation field. This protocol governs refusal
semantics without treating the record as scheduler authorization or execution
completion evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Mapping, Union


CONSTRAINT_WITNESS_PROTOCOL_ID = "hpl.constraint-witness"
CONSTRAINT_WITNESS_PROTOCOL_VERSION = "1.0.0"


class ConstraintWitnessStage(str, Enum):
    PLAN_REFUSAL = "plan_refusal"
    RUNTIME_REFUSAL = "runtime_refusal"
    TRADING_PAPER_REFUSAL = "trading_paper_refusal"
    CI_GOVERNANCE_REFUSAL = "ci_governance_refusal"
    NET_SHADOW_REFUSAL = "net_shadow_refusal"


@dataclass(frozen=True)
class ConstraintWitnessContract:
    stage: ConstraintWitnessStage
    role: str
    proves_refusal_record: bool = True
    implies_scheduler_authorization: bool = False
    implies_execution_completion: bool = False


CONSTRAINT_WITNESS_CONTRACTS: Mapping[
    ConstraintWitnessStage, ConstraintWitnessContract
] = {
    stage: ConstraintWitnessContract(stage=stage, role=stage.value)
    for stage in ConstraintWitnessStage
}


def resolve_constraint_witness_contract(
    stage: Union[str, ConstraintWitnessStage],
) -> ConstraintWitnessContract:
    try:
        typed_stage = (
            stage if isinstance(stage, ConstraintWitnessStage) else ConstraintWitnessStage(stage)
        )
    except ValueError as exc:
        raise ValueError(f"unknown constraint witness stage: {stage}") from exc
    return CONSTRAINT_WITNESS_CONTRACTS[typed_stage]


def validate_constraint_witness_record(
    record: Mapping[str, object],
) -> ConstraintWitnessContract:
    stage = record.get("stage")
    witness_id = record.get("witness_id")
    reasons = record.get("refusal_reasons")
    artifact_digests = record.get("artifact_digests")
    observer_id = record.get("observer_id")
    if not isinstance(stage, str):
        raise ValueError("constraint witness stage must be a string")
    contract = resolve_constraint_witness_contract(stage)
    if not isinstance(witness_id, str) or not witness_id:
        raise ValueError("constraint witness_id must be a non-empty string")
    if not isinstance(reasons, list):
        raise ValueError("constraint refusal_reasons must be a list")
    if not isinstance(artifact_digests, dict):
        raise ValueError("constraint artifact_digests must be an object")
    if not isinstance(observer_id, str) or not observer_id:
        raise ValueError("constraint observer_id must be a non-empty string")
    return contract


def constraint_witness_catalog() -> Dict[str, Dict[str, object]]:
    return {
        stage.value: {
            "role": contract.role,
            "proves_refusal_record": contract.proves_refusal_record,
            "implies_scheduler_authorization": contract.implies_scheduler_authorization,
            "implies_execution_completion": contract.implies_execution_completion,
        }
        for stage, contract in sorted(
            CONSTRAINT_WITNESS_CONTRACTS.items(), key=lambda item: item[0].value
        )
    }
