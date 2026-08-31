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
EXPECTED_ARCHITECTURE_ID = "apexquantumict.seven_hamiltonian.trading.v1"


def _apex_program_ir():
    spec = json.loads(APEX_FIXTURE.read_text(encoding="utf-8"))
    architecture_ir = compile_architecture_spec(spec)
    return architecture_ir, lower_architecture_ir_to_program_ir(architecture_ir)


def _shadow_plan(tmp_path: Path):
    architecture_ir, program_ir = _apex_program_ir()
    execution_plan = plan(
        program_ir,
        SchedulerContext(
            emit_effect_steps=True,
            track="trading_shadow_mode",
            trading_fixture_path=MARKET_FIXTURE,
            trading_policy_path=SHADOW_POLICY,
            trading_shadow_model_path=SHADOW_MODEL,
            trading_report_json_path=tmp_path / "trade_report.json",
            trading_report_md_path=tmp_path / "trade_report.md",
        ),
    )
    return architecture_ir, program_ir, execution_plan


def test_certified_apex_program_runs_only_scheduler_selected_shadow_effects(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    architecture_ir, program_ir, execution_plan = _shadow_plan(tmp_path)

    assert architecture_ir.architecture_id == EXPECTED_ARCHITECTURE_ID
    assert architecture_ir.authority["execution_owner"] == "hpl.scheduler"
    assert "execution_token" not in program_ir
    assert execution_plan.status == "planned"
    assert execution_plan.execution_token is not None

    effect_types = [str(step["effect_type"]) for step in execution_plan.steps]
    assert effect_types == [
        "SIM_MARKET_MODEL_LOAD",
        "INGEST_MARKET_FIXTURE",
        "SIM_REGIME_SHIFT_STEP",
        "SIM_LATENCY_APPLY",
        "COMPUTE_SIGNAL",
        "SIMULATE_ORDER",
        "SIM_PARTIAL_FILL_MODEL",
        "UPDATE_RISK_ENVELOPE",
        "SIM_ORDER_LIFECYCLE",
        "SIM_EMIT_TRADE_LEDGER",
        "EMIT_TRADE_REPORT",
    ]
    assert not any(effect.startswith("IO_") or effect.startswith("NET_") for effect in effect_types)

    result = RuntimeEngine().run(
        execution_plan,
        RuntimeContext(io_enabled=False, net_enabled=False),
        ExecutionContract(),
    )

    assert result.status == "completed"
    assert result.reasons == []
    assert [entry["effect_type"] for entry in result.transcript] == effect_types
    assert all(entry["ok"] is True for entry in result.transcript)
    assert (tmp_path / "shadow_trade_ledger.json").is_file()
    assert (tmp_path / "shadow_execution_log.json").is_file()
    assert (tmp_path / "trade_report.json").is_file()
    assert (tmp_path / "trade_report.md").is_file()

    ledger = json.loads((tmp_path / "shadow_trade_ledger.json").read_text(encoding="utf-8"))
    report = json.loads((tmp_path / "trade_report.json").read_text(encoding="utf-8"))
    assert ledger
    assert report
    assert any(record["stage"] == "scheduler_plan" for record in execution_plan.witness_records)
    assert any(record["stage"] == "runtime_complete" for record in result.witness_records)


def test_apex_shadow_effects_refuse_without_scheduler_token_before_any_effect(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _, _, execution_plan = _shadow_plan(tmp_path)
    tokenless_plan = replace(execution_plan, execution_token=None)

    result = RuntimeEngine().run(
        tokenless_plan,
        RuntimeContext(io_enabled=False, net_enabled=False),
        ExecutionContract(),
    )

    assert result.status == "denied"
    assert "execution token missing" in result.reasons
    assert result.steps == []
    assert result.transcript == []
    assert result.constraint_witnesses
    assert not (tmp_path / "shadow_trade_ledger.json").exists()
    assert not (tmp_path / "trade_report.json").exists()
