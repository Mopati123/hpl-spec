from __future__ import annotations

import json

import pytest

from hpl.backends.classical_lowering import lower_program_ir_to_backend_ir
from hpl.backends.qasm_lowering import build_qasm_artifact
from hpl.backends.witness_protocol import (
    BACKEND_WITNESS_PROTOCOL_ID,
    BACKEND_WITNESS_PROTOCOL_VERSION,
    BackendWitnessStage,
    backend_witness_catalog,
    resolve_backend_witness_contract,
    validate_backend_witness_pair,
    validate_backend_witness_record,
)


PROGRAM_IR = {
    "program_id": "backend-witness-protocol-test",
    "hamiltonian": {
        "terms": [
            {"operator_id": "u0", "cls": "U", "coefficient": 0.25},
            {"operator_id": "m0", "cls": "M", "coefficient": 1.0},
        ]
    },
}


def test_protocol_identity_is_frozen() -> None:
    assert BACKEND_WITNESS_PROTOCOL_ID == "hpl.backend-witness"
    assert BACKEND_WITNESS_PROTOCOL_VERSION == "1.0.0"


def test_catalog_has_unique_typed_stage_contracts() -> None:
    catalog = backend_witness_catalog()
    assert set(catalog) == {stage.value for stage in BackendWitnessStage}
    for stage in BackendWitnessStage:
        contract = resolve_backend_witness_contract(stage)
        entry = catalog[stage.value]
        assert entry["attestation"] == contract.attestation
        assert entry["proves_artifact_binding"] is True
        assert entry["proves_semantic_equivalence"] is False
        assert entry["implies_execution_authorization"] is False


def test_unknown_stage_is_refused() -> None:
    with pytest.raises(ValueError, match="unknown backend witness stage"):
        resolve_backend_witness_contract("backend_magic_complete")


def test_attestation_drift_is_refused() -> None:
    with pytest.raises(ValueError, match="backend witness attestation mismatch"):
        validate_backend_witness_pair("backend_lowering", "qasm_lowering_witness")


def test_classical_lowering_witness_conforms_to_protocol() -> None:
    backend_ir = lower_program_ir_to_backend_ir(PROGRAM_IR)
    record = json.loads(backend_ir.evidence["papas_witness_record"])
    contract = validate_backend_witness_record(record)
    assert contract.stage is BackendWitnessStage.BACKEND_LOWERING
    assert contract.role == "backend_transformation"
    assert contract.proves_artifact_binding is True
    assert contract.proves_semantic_equivalence is False
    assert contract.implies_execution_authorization is False


def test_qasm_lowering_witness_conforms_to_protocol() -> None:
    backend_ir = lower_program_ir_to_backend_ir(PROGRAM_IR).to_dict()
    artifact = build_qasm_artifact(backend_ir)
    record = json.loads(artifact["evidence"]["papas_witness_record"])
    contract = validate_backend_witness_record(record)
    assert contract.stage is BackendWitnessStage.QASM_LOWERING
    assert contract.role == "qasm_transformation"
    assert contract.proves_artifact_binding is True
    assert contract.proves_semantic_equivalence is False
    assert contract.implies_execution_authorization is False


def test_backend_witnesses_are_deterministic_for_identical_inputs() -> None:
    first_backend = lower_program_ir_to_backend_ir(PROGRAM_IR)
    second_backend = lower_program_ir_to_backend_ir(PROGRAM_IR)
    assert first_backend.evidence == second_backend.evidence

    first_qasm = build_qasm_artifact(first_backend.to_dict())
    second_qasm = build_qasm_artifact(second_backend.to_dict())
    assert first_qasm == second_qasm
