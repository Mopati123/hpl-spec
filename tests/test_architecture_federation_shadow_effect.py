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
    "shadow_reconciliation.json",
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


def _sha256_digest(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


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
        "SIM_RECONCILE_TRADE",
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
    assert (tmp_path / "shadow_reconciliation.json").is_file()

    ledger = json.loads((tmp_path / "shadow_trade_ledger.json").read_text(encoding="utf-8"))
    report = json.loads((tmp_path / "trade_report.json").read_text(encoding="utf-8"))
    reconciliation = json.loads(
        (tmp_path / "shadow_reconciliation.json").read_text(encoding="utf-8")
    )
    assert ledger
    assert report
    assert reconciliation["ok"] is True
    assert any(record["stage"] == "scheduler_plan" for record in execution_plan.witness_records)
    assert any(record["stage"] == "runtime_complete" for record in result.witness_records)


def test_apex_shadow_effects_refuse_if_scheduler_token_is_removed_after_planning(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _, _, execution_plan = _shadow_plan()
    tokenless_plan = replace(execution_plan, execution_token=None)

    result = RuntimeEngine().run(
        tokenless_plan,
        RuntimeContext(io_enabled=False, net_enabled=False),
        ExecutionContract(),
    )

    assert result.status == "denied"
    assert result.reasons == ["plan_integrity_mismatch"]
    assert result.steps == []
    assert result.transcript == []
    assert result.constraint_witnesses
    assert any(record["stage"] == "plan_integrity_denied" for record in result.witness_records)
    assert not (tmp_path / "shadow_trade_ledger.json").exists()
    assert not (tmp_path / "trade_report.json").exists()
    assert not (tmp_path / "shadow_reconciliation.json").exists()


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
    assert not (tmp_path / "shadow_reconciliation.json").exists()


def test_federated_apex_shadow_state_reconciles_with_runtime_evidence(tmp_path):
    architecture_ir, _, _, result = _run_shadow(tmp_path)

    assert result.status == "completed"
    assert architecture_ir.reconciliation_contract["required"] is True
    expected_operators = {
        "reconcile_trade_effect",
        "reconcile_portfolio_state",
    }
    assert set(architecture_ir.reconciliation_contract["operators"]) == expected_operators

    signal = json.loads((tmp_path / "signal.json").read_text(encoding="utf-8"))
    fill = json.loads((tmp_path / "shadow_fill.json").read_text(encoding="utf-8"))
    risk = json.loads((tmp_path / "risk_envelope.json").read_text(encoding="utf-8"))
    ledger = json.loads((tmp_path / "shadow_trade_ledger.json").read_text(encoding="utf-8"))
    report = json.loads((tmp_path / "trade_report.json").read_text(encoding="utf-8"))
    reconciliation = json.loads(
        (tmp_path / "shadow_reconciliation.json").read_text(encoding="utf-8")
    )

    assert ledger["action"] == signal["action"] == report["action"]
    assert ledger["executed"] == fill["executed"] == report["executed"]
    assert ledger["fill_fraction"] == fill["fill_fraction"] == report["fill_fraction"]
    assert ledger["fill_price"] == fill["fill_price"] == report["fill_price"]
    assert ledger["filled_size"] == fill["filled_size"]
    assert ledger["equity"] == risk["equity"] == report["equity"]
    assert ledger["drawdown"] == risk["drawdown"] == report["drawdown"]
    assert ledger["pnl"] == risk["pnl"] == report["pnl"]
    assert report["max_drawdown"] == risk["max_drawdown"]

    assert reconciliation["schema_version"] == "hpl.shadow_reconciliation.v1"
    assert reconciliation["ok"] is True
    assert set(reconciliation["operators"]) == expected_operators
    assert all(reconciliation["comparisons"].values())
    assert reconciliation["reasons"] == []

    source_paths = {
        "signal": tmp_path / "signal.json",
        "shadow_fill": tmp_path / "shadow_fill.json",
        "risk_envelope": tmp_path / "risk_envelope.json",
        "shadow_trade_ledger": tmp_path / "shadow_trade_ledger.json",
        "trade_report": tmp_path / "trade_report.json",
    }
    assert reconciliation["source_digests"] == {
        name: _sha256_digest(path) for name, path in source_paths.items()
    }

    transcript_by_effect = {entry["effect_type"]: entry for entry in result.transcript}
    ledger_evidence = transcript_by_effect["SIM_EMIT_TRADE_LEDGER"]["artifact_digests"]
    report_evidence = transcript_by_effect["EMIT_TRADE_REPORT"]["artifact_digests"]
    execution_evidence = transcript_by_effect["SIM_ORDER_LIFECYCLE"]["artifact_digests"]
    reconciliation_evidence = transcript_by_effect["SIM_RECONCILE_TRADE"]["artifact_digests"]

    assert ledger_evidence["shadow_trade_ledger.json"] == _sha256_digest(
        tmp_path / "shadow_trade_ledger.json"
    )
    assert report_evidence["trade_report.json"] == _sha256_digest(tmp_path / "trade_report.json")
    assert report_evidence["trade_report.md"] == _sha256_digest(tmp_path / "trade_report.md")
    assert execution_evidence["shadow_execution_log.json"] == _sha256_digest(
        tmp_path / "shadow_execution_log.json"
    )
    assert reconciliation_evidence["shadow_reconciliation.json"] == _sha256_digest(
        tmp_path / "shadow_reconciliation.json"
    )
