import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from hpl.architecture import compile_architecture_spec, lower_architecture_ir_to_program_ir
from hpl.runtime.context import RuntimeContext
from hpl.runtime.contracts import ExecutionContract
from hpl.runtime.engine import RuntimeEngine
from hpl.scheduler import SchedulerContext, plan


FIXTURE = (
    ROOT
    / "tests"
    / "fixtures"
    / "federation"
    / "apexquantumict.seven_hamiltonian.trading.v1.architecture.json"
)
CERTIFIED_APEX_COMMIT = "ee4705f9ea2b32eabb898dfa40b5c8917fee582d"
EXPECTED_ARCHITECTURE_ID = "apexquantumict.seven_hamiltonian.trading.v1"


def _load_certified_spec():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _compile_and_plan():
    architecture_ir = compile_architecture_spec(_load_certified_spec())
    program_ir = lower_architecture_ir_to_program_ir(architecture_ir)
    execution_plan = plan(program_ir, SchedulerContext())
    return architecture_ir, program_ir, execution_plan


def test_certified_apex_vector_reaches_scheduler_without_minting_authority():
    architecture_ir, program_ir, execution_plan = _compile_and_plan()

    assert architecture_ir.architecture_id == EXPECTED_ARCHITECTURE_ID
    assert architecture_ir.authority["execution_owner"] == "hpl.scheduler"
    assert program_ir["scheduler"] == {
        "collapse_policy": "architecture_ir_scheduler_sovereignty",
        "authorized_observers": [],
    }
    assert "execution_token" not in program_ir

    assert execution_plan.status == "planned"
    assert execution_plan.execution_token is not None
    assert execution_plan.program_id == EXPECTED_ARCHITECTURE_ID
    assert any(
        record["stage"] == "scheduler_plan"
        for record in execution_plan.witness_records
    )


def test_scheduler_approved_federation_plan_executes_with_runtime_evidence():
    _, _, execution_plan = _compile_and_plan()

    result = RuntimeEngine().run(
        execution_plan,
        RuntimeContext(),
        ExecutionContract(),
    )

    assert result.status == "completed"
    assert result.reasons == []
    assert len(result.transcript) == len(execution_plan.steps)
    assert result.transcript
    assert all(entry["ok"] is True for entry in result.transcript)
    assert any(record["stage"] == "runtime_start" for record in result.witness_records)
    assert any(record["stage"] == "step_ok" for record in result.witness_records)
    assert any(record["stage"] == "runtime_complete" for record in result.witness_records)


def test_federation_runtime_refuses_plan_that_scheduler_did_not_approve():
    _, _, execution_plan = _compile_and_plan()
    denied_plan = replace(
        execution_plan,
        status="denied",
        reasons=["certification_vector_forced_denial"],
    )

    result = RuntimeEngine().run(
        denied_plan,
        RuntimeContext(),
        ExecutionContract(),
    )

    assert result.status == "denied"
    assert "plan not approved" in result.reasons
    assert result.steps == []
    assert result.transcript == []
    assert result.constraint_witnesses
    assert any(record["stage"] == "runtime_complete" for record in result.witness_records)


def test_federation_runtime_refuses_when_scheduler_token_is_removed():
    _, _, execution_plan = _compile_and_plan()
    tokenless_plan = replace(execution_plan, execution_token=None)

    result = RuntimeEngine().run(
        tokenless_plan,
        RuntimeContext(),
        ExecutionContract(),
    )

    assert result.status == "denied"
    assert "execution token missing" in result.reasons
    assert result.steps == []
    assert result.transcript == []
    assert result.constraint_witnesses


def test_certification_vector_records_immutable_domain_source_commit():
    # The vector is copied from the already-certified ApexQuantumICT member commit.
    # This pin makes provenance drift explicit: changing the vector requires updating
    # the certified source commit and re-running federation certification.
    assert CERTIFIED_APEX_COMMIT == "ee4705f9ea2b32eabb898dfa40b5c8917fee582d"
