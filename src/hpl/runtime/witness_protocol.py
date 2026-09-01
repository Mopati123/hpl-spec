"""Typed, versioned contract for RuntimeEngine witness vocabulary.

The protocol intentionally versions the semantic contract without changing the
serialized witness-record shape. Existing deterministic evidence therefore
keeps its wire representation while CI can reject undeclared stage names or
stage/attestation drift.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Mapping, Union


RUNTIME_WITNESS_PROTOCOL_ID = "hpl.runtime-witness"
RUNTIME_WITNESS_PROTOCOL_VERSION = "1.0.0"


class RuntimeWitnessStage(str, Enum):
    RUNTIME_START = "runtime_start"
    PLAN_INTEGRITY_DENIED = "plan_integrity_denied"
    EPOCH_VERIFICATION = "epoch_verification"
    OPERATOR_REGISTRY_DENIED = "operator_registry_denied"
    BUDGET_DENIED = "budget_denied"
    DELTA_S_BUDGET_DENIED = "delta_s_budget_denied"
    IO_BUDGET_DENIED = "io_budget_denied"
    NET_BUDGET_DENIED = "net_budget_denied"
    DELTA_S_GATE_DENIED = "delta_s_gate_denied"
    STEP_DENIED = "step_denied"
    STEP_OK = "step_ok"
    COMPLETION_DENIED = "completion_denied"
    RUNTIME_TERMINAL = "runtime_terminal"
    RUNTIME_COMPLETE = "runtime_complete"
    EXECUTION_COMPLETED = "execution_completed"


@dataclass(frozen=True)
class RuntimeWitnessContract:
    stage: RuntimeWitnessStage
    attestation: str
    terminal: bool = False
    successful_completion: bool = False
    legacy: bool = False


RUNTIME_WITNESS_CONTRACTS: Mapping[RuntimeWitnessStage, RuntimeWitnessContract] = {
    RuntimeWitnessStage.RUNTIME_START: RuntimeWitnessContract(
        RuntimeWitnessStage.RUNTIME_START, "runtime_start_witness"
    ),
    RuntimeWitnessStage.PLAN_INTEGRITY_DENIED: RuntimeWitnessContract(
        RuntimeWitnessStage.PLAN_INTEGRITY_DENIED, "plan_integrity_denied_witness"
    ),
    RuntimeWitnessStage.EPOCH_VERIFICATION: RuntimeWitnessContract(
        RuntimeWitnessStage.EPOCH_VERIFICATION, "epoch_verification_witness"
    ),
    RuntimeWitnessStage.OPERATOR_REGISTRY_DENIED: RuntimeWitnessContract(
        RuntimeWitnessStage.OPERATOR_REGISTRY_DENIED,
        "operator_registry_denied_witness",
    ),
    RuntimeWitnessStage.BUDGET_DENIED: RuntimeWitnessContract(
        RuntimeWitnessStage.BUDGET_DENIED, "budget_denied_witness"
    ),
    RuntimeWitnessStage.DELTA_S_BUDGET_DENIED: RuntimeWitnessContract(
        RuntimeWitnessStage.DELTA_S_BUDGET_DENIED, "delta_s_budget_denied_witness"
    ),
    RuntimeWitnessStage.IO_BUDGET_DENIED: RuntimeWitnessContract(
        RuntimeWitnessStage.IO_BUDGET_DENIED, "io_budget_denied_witness"
    ),
    RuntimeWitnessStage.NET_BUDGET_DENIED: RuntimeWitnessContract(
        RuntimeWitnessStage.NET_BUDGET_DENIED, "net_budget_denied_witness"
    ),
    RuntimeWitnessStage.DELTA_S_GATE_DENIED: RuntimeWitnessContract(
        RuntimeWitnessStage.DELTA_S_GATE_DENIED, "delta_s_gate_denied_witness"
    ),
    RuntimeWitnessStage.STEP_DENIED: RuntimeWitnessContract(
        RuntimeWitnessStage.STEP_DENIED, "step_denied_witness"
    ),
    RuntimeWitnessStage.STEP_OK: RuntimeWitnessContract(
        RuntimeWitnessStage.STEP_OK, "step_ok_witness"
    ),
    RuntimeWitnessStage.COMPLETION_DENIED: RuntimeWitnessContract(
        RuntimeWitnessStage.COMPLETION_DENIED, "completion_denied_witness"
    ),
    RuntimeWitnessStage.RUNTIME_TERMINAL: RuntimeWitnessContract(
        RuntimeWitnessStage.RUNTIME_TERMINAL,
        "runtime_terminal_witness",
        terminal=True,
    ),
    RuntimeWitnessStage.RUNTIME_COMPLETE: RuntimeWitnessContract(
        RuntimeWitnessStage.RUNTIME_COMPLETE,
        "runtime_complete_witness",
        successful_completion=True,
        legacy=True,
    ),
    RuntimeWitnessStage.EXECUTION_COMPLETED: RuntimeWitnessContract(
        RuntimeWitnessStage.EXECUTION_COMPLETED,
        "execution_completed_witness",
        successful_completion=True,
    ),
}


def resolve_runtime_witness_contract(
    stage: Union[str, RuntimeWitnessStage],
) -> RuntimeWitnessContract:
    """Resolve a runtime witness stage or refuse unknown vocabulary."""

    try:
        typed_stage = stage if isinstance(stage, RuntimeWitnessStage) else RuntimeWitnessStage(stage)
    except ValueError as exc:
        raise ValueError(f"unknown runtime witness stage: {stage}") from exc
    return RUNTIME_WITNESS_CONTRACTS[typed_stage]


def validate_runtime_witness_pair(
    stage: Union[str, RuntimeWitnessStage], attestation: str
) -> RuntimeWitnessContract:
    """Refuse a stage/attestation pair that violates the frozen v1 contract."""

    contract = resolve_runtime_witness_contract(stage)
    if attestation != contract.attestation:
        raise ValueError(
            "runtime witness attestation mismatch: "
            f"stage={contract.stage.value} expected={contract.attestation} "
            f"observed={attestation}"
        )
    return contract


def validate_runtime_witness_record(record: Mapping[str, object]) -> RuntimeWitnessContract:
    """Validate the semantic identity fields of a serialized runtime witness."""

    stage = record.get("stage")
    attestation = record.get("attestation")
    if not isinstance(stage, str):
        raise ValueError("runtime witness stage must be a string")
    if not isinstance(attestation, str):
        raise ValueError("runtime witness attestation must be a string")
    return validate_runtime_witness_pair(stage, attestation)


def runtime_witness_catalog() -> Dict[str, Dict[str, object]]:
    """Return a deterministic, serialization-friendly view of protocol v1."""

    return {
        stage.value: {
            "attestation": contract.attestation,
            "terminal": contract.terminal,
            "successful_completion": contract.successful_completion,
            "legacy": contract.legacy,
        }
        for stage, contract in sorted(
            RUNTIME_WITNESS_CONTRACTS.items(), key=lambda item: item[0].value
        )
    }
