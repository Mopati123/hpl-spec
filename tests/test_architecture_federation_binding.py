from hpl.architecture import (
    EVIDENCE_REQUIRED,
    EXECUTION_OWNER,
    PROGRAM_IR_COLLAPSE_POLICY,
    RECONCILIATION_REQUIRED,
    compile_architecture_spec,
    lower_architecture_ir_to_program_ir,
)


def _spec():
    return {
        "architecture_id": "test.federation.binding.v1",
        "domain": "test",
        "states": [{"id": "state"}],
        "observables": [{"id": "observe"}],
        "dynamics": [{"id": "evolve"}],
        "proposals": [{"id": "propose"}],
        "constraints": [{"id": "project"}],
        "invariants": [{"id": "scheduler_sovereignty"}],
        "authorities": [
            {"id": "execution_authority", "kind": "execution", "owner": EXECUTION_OWNER}
        ],
        "effects": [{"id": "commit"}],
        "evidence": [{"id": "emit_receipt"}],
        "reconciliation": [{"id": "reconcile"}],
        "metadata": {},
    }


def test_compiler_binds_architecture_ir_to_federation_contract():
    ir = compile_architecture_spec(_spec())

    assert ir.authority["execution_owner"] == EXECUTION_OWNER
    assert ir.evidence_contract["required"] is EVIDENCE_REQUIRED
    assert ir.reconciliation_contract["required"] is RECONCILIATION_REQUIRED


def test_lowering_binds_program_ir_to_federation_collapse_policy():
    ir = compile_architecture_spec(_spec())
    program_ir = lower_architecture_ir_to_program_ir(ir)

    assert program_ir["scheduler"]["collapse_policy"] == PROGRAM_IR_COLLAPSE_POLICY
    assert program_ir["scheduler"]["authorized_observers"] == []
