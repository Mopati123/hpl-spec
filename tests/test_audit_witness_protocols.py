from __future__ import annotations

import pytest

from hpl.audit.constraint_witness import build_constraint_witness
from hpl.audit.constraint_witness_protocol import (
    CONSTRAINT_WITNESS_PROTOCOL_ID,
    CONSTRAINT_WITNESS_PROTOCOL_VERSION,
    ConstraintWitnessStage,
    constraint_witness_catalog,
    resolve_constraint_witness_contract,
    validate_constraint_witness_record,
)
from hpl.audit.coupling_event import build_coupling_event_from_registry
from hpl.audit.coupling_witness_protocol import (
    COUPLING_WITNESS_PROTOCOL_ID,
    COUPLING_WITNESS_PROTOCOL_VERSION,
    CouplingWitnessStage,
    coupling_witness_catalog,
    resolve_coupling_witness_contract,
    validate_coupling_witness_record,
)


def _registry():
    return {
        "projectors": [{"id": "projector:v1", "version": "1.0.0"}],
        "edges": [
            {
                "id": "edge:a-b",
                "projector": "projector:v1",
                "operator_name": "couple_a_b",
                "sector_src": "a",
                "sector_dst": "b",
                "invariants_checked": ["bounded"],
            }
        ],
    }


def test_audit_protocol_identities_are_frozen():
    assert COUPLING_WITNESS_PROTOCOL_ID == "hpl.coupling-witness"
    assert COUPLING_WITNESS_PROTOCOL_VERSION == "1.0.0"
    assert CONSTRAINT_WITNESS_PROTOCOL_ID == "hpl.constraint-witness"
    assert CONSTRAINT_WITNESS_PROTOCOL_VERSION == "1.0.0"


def test_coupling_catalog_matches_typed_vocabulary():
    assert set(coupling_witness_catalog()) == {stage.value for stage in CouplingWitnessStage}
    contract = resolve_coupling_witness_contract("coupling_validation")
    assert contract.proves_event_binding is True
    assert contract.proves_global_topology_validity is False
    assert contract.proves_all_invariants is False
    assert contract.implies_execution_authorization is False


def test_actual_coupling_producer_conforms_and_is_deterministic():
    first = build_coupling_event_from_registry(_registry())
    second = build_coupling_event_from_registry(_registry())
    contract = validate_coupling_witness_record(first.witness_record)
    assert contract.stage is CouplingWitnessStage.COUPLING_VALIDATION
    assert first.witness_record == second.witness_record
    assert first.event == second.event


def test_unknown_coupling_stage_is_refused():
    with pytest.raises(ValueError, match="unknown coupling witness stage"):
        resolve_coupling_witness_contract("topology_probably_valid")


def test_coupling_attestation_drift_is_refused():
    record = dict(build_coupling_event_from_registry(_registry()).witness_record)
    record["attestation"] = "execution_completed_witness"
    with pytest.raises(ValueError, match="attestation mismatch"):
        validate_coupling_witness_record(record)


def test_constraint_catalog_matches_observed_refusal_vocabulary():
    assert set(constraint_witness_catalog()) == {stage.value for stage in ConstraintWitnessStage}
    for stage in ConstraintWitnessStage:
        contract = resolve_constraint_witness_contract(stage)
        assert contract.proves_refusal_record is True
        assert contract.implies_scheduler_authorization is False
        assert contract.implies_execution_completion is False


@pytest.mark.parametrize("stage", [stage.value for stage in ConstraintWitnessStage])
def test_actual_constraint_producer_conforms_for_every_governed_stage(stage):
    record = build_constraint_witness(
        stage=stage,
        refusal_reasons=["z_reason", "a_reason"],
        artifact_digests={"plan": "sha256:deadbeef"},
        timestamp="1970-01-01T00:00:00Z",
    )
    contract = validate_constraint_witness_record(record)
    assert contract.stage.value == stage
    assert record["refusal_reasons"] == ["a_reason", "z_reason"]


def test_constraint_witness_is_deterministic():
    kwargs = {
        "stage": "runtime_refusal",
        "refusal_reasons": ["b", "a"],
        "artifact_digests": {"plan": "sha256:deadbeef"},
        "timestamp": "1970-01-01T00:00:00Z",
    }
    assert build_constraint_witness(**kwargs) == build_constraint_witness(**kwargs)


def test_unknown_constraint_stage_is_refused():
    record = build_constraint_witness(
        stage="maybe_refused",
        refusal_reasons=["reason"],
        artifact_digests={"plan": "sha256:deadbeef"},
    )
    with pytest.raises(ValueError, match="unknown constraint witness stage"):
        validate_constraint_witness_record(record)
