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
FORBIDDEN_SHADOW_POLICY = (
    ROOT / "tests" / "fixtures" / "trading" / "shadow_policy_forbidden.json"
)
SHADOW_MODEL = ROOT / "tests" / "fixtures" / "trading" / "shadow_model.json"
EXPECTED_ARCHITECTURE_ID = "apexquantumict.seven_hamiltonian.trading.v1"
SHADOW_ARTIFACTS = (
    "shadow_seed.json",
    "shadow_model.json",
    "market_snapshot.json",
    "regime_snapshot.json",
    "latency_snapshot.json",
    "signal.json",
    "trade_fill.json",
    "shadow_fill.json",
    "risk_envelope.json",
    "shadow_execution_log.json",
    "shadow_trade_ledger.json",
    "trade_report.json",
    "trade_report.md",
)


def _apex_program_ir():
    spec = json.loads(APEX_FIXTURE.read_text(encoding="utf-8"))
    architecture_ir = compile_architecture_spec(spec)
    return architecture_ir, lower_architecture_ir_to_program_ir(architecture_ir)


def _shadow_plan(policy_path: Path = SHADOW_POLICY):
    architecture_ir, program_ir = _apex_program_ir()
    execution_plan = plan(
        program_ir,
        SchedulerContext(
            emit_effect_steps=True,
            track="trading_shadow_mode",
            trading_fixture_path=MARKET_FIXTURE,
            trading_policy_path=policy_path,
            trading_shadow_model_path=SHADOW_MODEL,
            trading_report_json_path=Path("trade_report.json"),
            trading_report_md_path=Path("trade_report.md"),
        ),
    )
    return architecture_ir, program_ir, execution_plan


def _run_shadow(work_dir: Path, policy_path: Path = SHADOW_POLICY):
    architecture_ir, program_ir, execution_plan = _shadow_plan(policy_path)
    previous = Path.cwd()
    try:
        work_dir.mkdir(parents=True, exist_ok=True)
        __import__("os").chdir(work_dir)
        result = RuntimeEngine().run(
            execution_plan,
            RuntimeContext(io_enabled=False, net_enabled=False),
            ExecutionContract(),
        )
    finally:
        __import__("os").chdir(previous)
    return architecture_ir, program_ir, execution_plan, result


def test_certified_apex_program_runs_only_scheduler_selected_shadow_effects(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    architecture_ir, program_ir, execution_plan = _shadow_plan()

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
    _, _, execution_plan = _shadow_plan()
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


def test_federated_apex_shadow_effects_are_byte_replayable(tmp_path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"

    first_ir, first_program, first_plan, first_result = _run_shadow(first_dir)
    second_ir, second_program, second_plan, second_result = _run_shadow(second_dir)

    assert first_ir.to_dict() == second_ir.to_dict()
    assert first_program == second_program
    assert first_plan.plan_id == second_plan.plan_id
    assert first_plan.to_dict() == second_plan.to_dict()
    assert first_result.result_id == second_result.result_id
    assert first_result.to_dict() == second_result.to_dict()

    first_artifacts = {name: (first_dir / name).read_bytes() for name in SHADOW_ARTIFACTS}
    second_artifacts = {name: (second_dir / name).read_bytes() for name in SHADOW_ARTIFACTS}
    assert first_artifacts == second_artifacts


def test_federated_apex_shadow_policy_refusal_stops_before_trade_commit(tmp_path):
    _, _, execution_plan, result = _run_shadow(tmp_path, FORBIDDEN_SHADOW_POLICY)

    assert execution_plan.status == "planned"
    assert result.status == "denied"
    assert result.constraint_witnesses
    assert result.transcript
    assert result.transcript[-1]["effect_type"] == "SIM_LATENCY_APPLY"
    assert result.transcript[-1]["ok"] is False
    assert result.transcript[-1]["refusal_type"] == "StalenessViolation"
    assert not (tmp_path / "signal.json").exists()
    assert not (tmp_path / "trade_fill.json").exists()
    assert not (tmp_path / "shadow_fill.json").exists()
    assert not (tmp_path / "shadow_trade_ledger.json").exists()
    assert not (tmp_path / "trade_report.json").exists()
