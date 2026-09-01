from __future__ import annotations

import pytest

from hpl.scheduler import SchedulerContext, plan
from hpl.scheduler_witness_protocol import (
    SCHEDULER_WITNESS_PROTOCOL_ID,
    SCHEDULER_WITNESS_PROTOCOL_VERSION,
    SchedulerWitnessStage,
    resolve_scheduler_witness_contract,
    scheduler_witness_catalog,
    validate_scheduler_witness_pair,
    validate_scheduler_witness_record,
)


def _program_ir() -> dict[str, object]:
    return {
        "program_id": "scheduler-witness-protocol-test",
        "hamiltonian": {"terms": []},
        "operators": [],
        "invariants": [],
        "scheduler": {},
    }


def test_protocol_identity_is_frozen() -> None:
    assert SCHEDULER_WITNESS_PROTOCOL_ID == "hpl.scheduler-witness"
    assert SCHEDULER_WITNESS_PROTOCOL_VERSION == "1.0.0"


def test_catalog_is_deterministic_and_explicit() -> None:
    assert scheduler_witness_catalog() == {
        "epoch_verification": {
            "attestation": "epoch_verification_witness",
            "role": "verification",
            "terminal_planning_decision": False,
            "implies_execution_authorization": False,
        },
        "scheduler_plan": {
            "attestation": "scheduler_plan_witness",
            "role": "planning_decision",
            "terminal_planning_decision": True,
            "implies_execution_authorization": False,
        },
    }


def test_unknown_scheduler_stage_is_refused() -> None:
    with pytest.raises(ValueError, match="unknown scheduler witness stage"):
        resolve_scheduler_witness_contract("scheduler_approved")


def test_stage_attestation_drift_is_refused() -> None:
    with pytest.raises(ValueError, match="attestation mismatch"):
        validate_scheduler_witness_pair(
            SchedulerWitnessStage.SCHEDULER_PLAN,
            "execution_authorized_witness",
        )


def test_scheduler_plan_witness_does_not_imply_execution_authorization() -> None:
    contract = resolve_scheduler_witness_contract(SchedulerWitnessStage.SCHEDULER_PLAN)
    assert contract.terminal_planning_decision is True
    assert contract.implies_execution_authorization is False


def test_actual_scheduler_output_conforms_to_protocol() -> None:
    execution_plan = plan(_program_ir(), SchedulerContext())
    assert execution_plan.status == "planned"
    assert [record["stage"] for record in execution_plan.witness_records] == [
        "scheduler_plan"
    ]
    contracts = [
        validate_scheduler_witness_record(record)
        for record in execution_plan.witness_records
    ]
    assert [contract.stage for contract in contracts] == [
        SchedulerWitnessStage.SCHEDULER_PLAN
    ]


def test_denied_scheduler_plan_witness_is_not_authorization_evidence(tmp_path) -> None:
    missing_anchor = tmp_path / "missing.anchor.json"
    execution_plan = plan(
        _program_ir(),
        SchedulerContext(
            require_epoch_verification=True,
            anchor_path=missing_anchor,
        ),
    )
    assert execution_plan.status == "denied"
    assert execution_plan.reasons
    assert [record["stage"] for record in execution_plan.witness_records] == [
        "epoch_verification",
        "scheduler_plan",
    ]
    contracts = [
        validate_scheduler_witness_record(record)
        for record in execution_plan.witness_records
    ]
    planning_contract = contracts[-1]
    assert planning_contract.stage is SchedulerWitnessStage.SCHEDULER_PLAN
    assert planning_contract.terminal_planning_decision is True
    assert planning_contract.implies_execution_authorization is False
