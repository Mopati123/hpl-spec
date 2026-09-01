import hashlib
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


APEX_FIXTURE = (
    ROOT
    / "tests"
    / "fixtures"
    / "federation"
    / "apexquantumict.seven_hamiltonian.trading.v1.architecture.json"
)
MARKET_FIXTURE = ROOT / "tests" / "fixtures" / "trading" / "price_series_simple.json"
SHADOW_POLICY = ROOT / "tests" / "fixtures" / "trading" / "shadow_policy_safe.json"
SHADOW_MODEL = ROOT / "tests" / "fixtures" / "trading" / "shadow_model.json"


def _program_ir():
    spec = json.loads(APEX_FIXTURE.read_text(encoding="utf-8"))
    return lower_architecture_ir_to_program_ir(compile_architecture_spec(spec))


def _context(track: str) -> SchedulerContext:
    return SchedulerContext(
        emit_effect_steps=True,
        track=track,
        trading_fixture_path=MARKET_FIXTURE,
        trading_policy_path=SHADOW_POLICY,
        trading_shadow_model_path=SHADOW_MODEL,
        trading_report_json_path=Path("trade_report.json"),
        trading_report_md_path=Path("trade_report.md"),
    )


def _plan_core(execution_plan):
    payload = execution_plan.to_dict()
    return {
        "program_id": payload["program_id"],
        "status": payload["status"],
        "steps": payload["steps"],
        "reasons": payload["reasons"],
        "verification": payload["verification"],
        "execution_token": payload["execution_token"],
        "operator_registry_enforced": payload["operator_registry_enforced"],
        "operator_registry_paths": payload["operator_registry_paths"],
        "completion_requirements": payload["completion_requirements"],
    }


def _plan_id(plan_core):
    canonical = json.dumps(plan_core, sort_keys=True, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def test_shadow_scheduler_declares_reconciliation_completion_requirements():
    execution_plan = plan(_program_ir(), _context("trading_shadow_mode"))

    assert execution_plan.completion_requirements == {
        "required_successful_effects": ["SIM_RECONCILE_TRADE"],
        "required_artifact_digests": ["shadow_reconciliation.json"],
    }
    assert execution_plan.steps[-1]["effect_type"] == "SIM_RECONCILE_TRADE"
    assert execution_plan.to_dict()["completion_requirements"] == execution_plan.completion_requirements


def test_completion_requirements_are_bound_into_deterministic_plan_identity():
    execution_plan = plan(_program_ir(), _context("trading_shadow_mode"))
    plan_core = _plan_core(execution_plan)

    assert execution_plan.plan_id == _plan_id(plan_core)

    tampered = dict(plan_core)
    tampered["completion_requirements"] = {}
    assert execution_plan.plan_id != _plan_id(tampered)


def test_generic_effect_track_has_no_shadow_reconciliation_requirement():
    execution_plan = plan(_program_ir(), _context("trading_paper_mode"))
    assert execution_plan.completion_requirements == {}
    assert "SIM_RECONCILE_TRADE" not in [
        step["effect_type"] for step in execution_plan.steps
    ]


def test_runtime_denies_shadow_plan_when_reconciliation_step_is_removed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    execution_plan = plan(_program_ir(), _context("trading_shadow_mode"))
    without_reconciliation = replace(
        execution_plan,
        steps=execution_plan.steps[:-1],
    )

    result = RuntimeEngine().run(
        without_reconciliation,
        RuntimeContext(io_enabled=False, net_enabled=False),
        ExecutionContract(),
    )

    assert result.status == "denied"
    assert result.reasons == ["plan_integrity_mismatch"]
    assert result.transcript == []
    assert not (tmp_path / "shadow_reconciliation.json").exists()
    assert any(record["stage"] == "plan_integrity_denied" for record in result.witness_records)
