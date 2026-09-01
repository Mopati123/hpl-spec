from hpl.architecture import (
    EVIDENCE_REQUIRED,
    EXECUTION_OWNER,
    FEDERATION_CONTRACT_ID,
    FEDERATION_CONTRACT_VERSION,
    PROGRAM_IR_COLLAPSE_POLICY,
    RECONCILIATION_REQUIRED,
    federation_contract,
)


def test_federation_contract_is_frozen_and_scheduler_owned():
    assert federation_contract() == {
        "contract_id": "hpl.architecture-federation",
        "version": "1.0.0",
        "execution_owner": "hpl.scheduler",
        "program_ir_collapse_policy": "architecture_ir_scheduler_sovereignty",
        "evidence_required": True,
        "reconciliation_required": True,
    }
    assert FEDERATION_CONTRACT_ID == "hpl.architecture-federation"
    assert FEDERATION_CONTRACT_VERSION == "1.0.0"
    assert EXECUTION_OWNER == "hpl.scheduler"
    assert PROGRAM_IR_COLLAPSE_POLICY == "architecture_ir_scheduler_sovereignty"
    assert EVIDENCE_REQUIRED is True
    assert RECONCILIATION_REQUIRED is True
