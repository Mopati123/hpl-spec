from __future__ import annotations

import pytest

from hpl.trace import emit_witness_record


BASE = {
    "observer_id": "papas",
    "artifact_digests": {"artifact": "sha256:test"},
    "timestamp": "1970-01-01T00:00:00Z",
}


@pytest.mark.parametrize(
    ("stage", "attestation"),
    [
        ("epoch_anchor", "epoch_anchor_witness"),
        ("epoch_verification", "epoch_verification_witness"),
        ("scheduler_plan", "scheduler_plan_witness"),
        ("runtime_start", "runtime_start_witness"),
        ("runtime_terminal", "runtime_terminal_witness"),
        ("execution_completed", "execution_completed_witness"),
        ("backend_lowering", "backend_ir_witness"),
        ("qasm_lowering", "qasm_lowering_witness"),
        ("coupling_validation", "coupling_event_witness"),
        ("dev_change", "dev_change_witness"),
    ],
)
def test_shared_emitter_accepts_declared_protocol_pairs(stage: str, attestation: str) -> None:
    record = emit_witness_record(stage=stage, attestation=attestation, **BASE)
    assert record["stage"] == stage
    assert record["attestation"] == attestation


@pytest.mark.parametrize(
    ("stage", "attestation"),
    [
        ("scheduler_plan", "execution_completed_witness"),
        ("runtime_terminal", "runtime_complete_witness"),
        ("backend_lowering", "qasm_lowering_witness"),
        ("epoch_anchor", "epoch_verification_witness"),
        ("coupling_validation", "dev_change_witness"),
    ],
)
def test_shared_emitter_refuses_attestation_drift(stage: str, attestation: str) -> None:
    with pytest.raises(ValueError):
        emit_witness_record(stage=stage, attestation=attestation, **BASE)


def test_shared_emitter_refuses_undeclared_stage() -> None:
    with pytest.raises(ValueError, match="ungoverned witness stage"):
        emit_witness_record(stage="invented_stage", attestation="invented_witness", **BASE)


def test_scheduler_plan_witness_does_not_accept_execution_authorization_attestation() -> None:
    with pytest.raises(ValueError):
        emit_witness_record(
            stage="scheduler_plan",
            attestation="execution_authorization_witness",
            **BASE,
        )
