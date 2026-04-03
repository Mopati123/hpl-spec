"""Extended tests for effect handlers covering missed branches."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from hpl.execution_token import ExecutionToken
from hpl.runtime.context import RuntimeContext
from hpl.runtime.effects.effect_step import EffectStep
from hpl.runtime.effects.effect_types import EffectType
from hpl.runtime.effects.handlers import (
    handle_assert_contract,
    handle_check_repo_state,
    handle_compute_delta_s,
    handle_compute_signal,
    handle_delta_s_gate,
    handle_emit_artifact,
    handle_evaluate_agent_proposal,
    handle_ingest_market_fixture,
    handle_invert_constraints,
    handle_io_connect,
    handle_io_emit_io_event,
    handle_io_query_fills,
    handle_io_reconcile,
    handle_io_submit_order,
    handle_measure_condition,
    handle_net_close,
    handle_net_connect,
    handle_net_handshake,
    handle_net_key_exchange,
    handle_net_recv,
    handle_net_send,
    handle_noop,
    handle_select_measurement_track,
    handle_sim_latency_apply,
    handle_sim_market_model_load,
    handle_sim_regime_shift_step,
    handle_simulate_order,
    handle_update_risk_envelope,
)


# ── helpers ────────────────────────────────────────────────────────────────────

def _step(effect_type=EffectType.NOOP, step_id="s1", **args):
    return EffectStep(step_id=step_id, effect_type=effect_type, args=args)


def _ctx(tmp_path=None, token=None, io_enabled=False, net_enabled=False):
    return RuntimeContext(
        trace_sink=tmp_path,
        execution_token=token,
        io_enabled=io_enabled,
        net_enabled=net_enabled,
    )


def _io_token():
    return ExecutionToken.build(
        allowed_backends=["CLASSICAL"],
        io_policy={
            "io_allowed": True,
            "io_scopes": [
                "BROKER_CONNECT", "ORDER_SUBMIT", "ORDER_CANCEL",
                "ORDER_QUERY", "IO_EVENT", "RECONCILE", "ROLLBACK",
            ],
        },
    )


def _net_token():
    return ExecutionToken.build(
        allowed_backends=["CLASSICAL"],
        net_policy={
            "net_caps": [
                "NET_CONNECT", "NET_HANDSHAKE", "NET_KEY_EXCHANGE",
                "NET_SEND", "NET_RECV", "NET_CLOSE",
            ],
            "net_mode": "dry_run",
        },
    )


# ── handle_noop ────────────────────────────────────────────────────────────────

def test_noop_ok():
    result = handle_noop(_step(), _ctx())
    assert result.ok


# ── handle_emit_artifact ───────────────────────────────────────────────────────

def test_emit_artifact_missing_path():
    result = handle_emit_artifact(_step(), _ctx())
    assert not result.ok
    assert result.refusal_type == "MissingArtifactPath"


def test_emit_artifact_json_format(tmp_path):
    step = _step(path="out.json", payload={"x": 1})
    result = handle_emit_artifact(step, _ctx(tmp_path=tmp_path))
    assert result.ok
    assert (tmp_path / "out.json").exists()


def test_emit_artifact_text_format(tmp_path):
    step = _step(path="out.txt", payload="hello", format="text")
    result = handle_emit_artifact(step, _ctx(tmp_path=tmp_path))
    assert result.ok
    assert (tmp_path / "out.txt").read_text() == "hello"


# ── handle_assert_contract ─────────────────────────────────────────────────────

def test_assert_contract_ok_true():
    assert handle_assert_contract(_step(ok=True), _ctx()).ok


def test_assert_contract_ok_false_no_errors():
    result = handle_assert_contract(_step(ok=False), _ctx())
    assert not result.ok
    assert result.refusal_type == "ContractViolation"


def test_assert_contract_ok_false_with_errors():
    result = handle_assert_contract(_step(ok=False, errors=["err1", "err2"]), _ctx())
    assert not result.ok
    assert "err1" in result.refusal_reasons


def test_assert_contract_errors_not_list():
    result = handle_assert_contract(_step(ok=False, errors="a single error"), _ctx())
    assert not result.ok
    assert "a single error" in result.refusal_reasons


# ── handle_select_measurement_track ───────────────────────────────────────────

def test_select_measurement_track_missing_input():
    result = handle_select_measurement_track(_step(), _ctx())
    assert not result.ok
    assert result.refusal_type == "BoundaryConditionsMissing"


def test_select_measurement_track_file_not_found(tmp_path):
    step = _step(input_path="/nonexistent/bc.json")
    result = handle_select_measurement_track(step, _ctx(tmp_path=tmp_path))
    assert not result.ok
    assert result.refusal_type == "BoundaryConditionsMissing"


def test_select_measurement_track_invalid_json(tmp_path):
    bc = tmp_path / "bc.json"
    bc.write_text("not json")
    step = _step(input_path=str(bc))
    result = handle_select_measurement_track(step, _ctx(tmp_path=tmp_path))
    assert not result.ok
    assert result.refusal_type == "BoundaryConditionsInvalid"


def test_select_measurement_track_success(tmp_path):
    # ci_available=True → selects Track A (publish)
    bc = tmp_path / "bc.json"
    bc.write_text(json.dumps({"ci_available": True}))
    step = _step(input_path=str(bc), out_path="sel.json")
    result = handle_select_measurement_track(step, _ctx(tmp_path=tmp_path))
    assert result.ok


# ── handle_measure_condition ───────────────────────────────────────────────────

def test_measure_condition_missing_inputs():
    result = handle_measure_condition(_step(), _ctx())
    assert not result.ok
    assert result.refusal_type == "MeasurementInputsMissing"


def test_measure_condition_files_missing(tmp_path):
    step = _step(prior_path="/no/prior.json", posterior_path="/no/post.json")
    result = handle_measure_condition(step, _ctx(tmp_path=tmp_path))
    assert not result.ok


def test_measure_condition_success_with_out_path(tmp_path):
    prior = tmp_path / "prior.json"
    prior.write_bytes(b'{"val":1}')
    post = tmp_path / "post.json"
    post.write_bytes(b'{"val":2}')
    step = _step(prior_path=str(prior), posterior_path=str(post), out_path="trace.json")
    result = handle_measure_condition(step, _ctx(tmp_path=tmp_path))
    assert result.ok
    assert (tmp_path / "trace.json").exists()


def test_measure_condition_success_no_out_path(tmp_path):
    prior = tmp_path / "prior.json"
    prior.write_bytes(b'{"val":1}')
    post = tmp_path / "post.json"
    post.write_bytes(b'{"val":2}')
    step = _step(prior_path=str(prior), posterior_path=str(post))
    result = handle_measure_condition(step, _ctx())
    assert result.ok
    # default_name="measurement_trace.json" → key is "measurement_trace.json"
    assert any("measurement_trace" in k for k in result.artifact_digests)


# ── handle_compute_delta_s ─────────────────────────────────────────────────────

def test_compute_delta_s_missing_inputs():
    result = handle_compute_delta_s(_step(), _ctx())
    assert not result.ok
    assert result.refusal_type == "MeasurementInputsMissing"


def test_compute_delta_s_success_with_out(tmp_path):
    prior = tmp_path / "prior.bin"
    prior.write_bytes(b"state_a")
    post = tmp_path / "post.bin"
    post.write_bytes(b"state_b")
    step = _step(prior_path=str(prior), posterior_path=str(post), out_path="report.json")
    result = handle_compute_delta_s(step, _ctx(tmp_path=tmp_path))
    assert result.ok


def test_compute_delta_s_success_no_out(tmp_path):
    prior = tmp_path / "prior.bin"
    prior.write_bytes(b"state_a")
    post = tmp_path / "post.bin"
    post.write_bytes(b"state_b")
    step = _step(prior_path=str(prior), posterior_path=str(post))
    result = handle_compute_delta_s(step, _ctx())
    assert result.ok
    assert any("delta_s_report" in k for k in result.artifact_digests)


# ── handle_delta_s_gate ────────────────────────────────────────────────────────

def test_delta_s_gate_missing_report():
    result = handle_delta_s_gate(_step(), _ctx())
    assert not result.ok
    assert result.refusal_type == "DeltaSReportMissing"


def test_delta_s_gate_pass(tmp_path):
    report = tmp_path / "report.json"
    report.write_text(json.dumps({"delta_s": 0.9}))
    step = _step(delta_s_report_path=str(report), out_path="dec.json")
    result = handle_delta_s_gate(step, _ctx(tmp_path=tmp_path))
    assert result.ok  # default threshold=0.0, comparator=gte → 0.9 >= 0.0


def test_delta_s_gate_fail(tmp_path):
    report = tmp_path / "report.json"
    report.write_text(json.dumps({"delta_s": 0.05}))
    step = _step(delta_s_report_path=str(report), policy={"threshold": 0.5, "comparator": "gte"})
    result = handle_delta_s_gate(step, _ctx())
    assert not result.ok
    assert result.refusal_type == "DeltaSGateFailed"


def test_delta_s_gate_from_token_policy(tmp_path):
    report = tmp_path / "report.json"
    report.write_text(json.dumps({"delta_s": 0.8}))
    token = ExecutionToken.build(
        allowed_backends=["CLASSICAL"],
        delta_s_policy={"threshold": 0.5, "comparator": "gte"},
    )
    step = _step(delta_s_report_path=str(report))
    result = handle_delta_s_gate(step, _ctx(tmp_path=tmp_path, token=token))
    assert result.ok


# ── handle_check_repo_state ────────────────────────────────────────────────────

def test_check_repo_state_missing():
    result = handle_check_repo_state(_step(), _ctx())
    assert not result.ok
    assert result.refusal_type == "RepoStateMissing"


def test_check_repo_state_invalid_json(tmp_path):
    p = tmp_path / "state.json"
    p.write_text("not json")
    step = _step(state_path=str(p))
    result = handle_check_repo_state(step, _ctx(tmp_path=tmp_path))
    assert not result.ok
    assert result.refusal_type == "RepoStateInvalid"


def test_check_repo_state_not_clean(tmp_path):
    p = tmp_path / "state.json"
    p.write_text(json.dumps({"clean": False}))
    step = _step(state_path=str(p))
    result = handle_check_repo_state(step, _ctx(tmp_path=tmp_path))
    assert not result.ok
    assert result.refusal_type == "RepoStateNotClean"


def test_check_repo_state_clean(tmp_path):
    p = tmp_path / "state.json"
    p.write_text(json.dumps({"clean": True}))
    step = _step(state_path=str(p))
    result = handle_check_repo_state(step, _ctx(tmp_path=tmp_path))
    assert result.ok


# ── handle_ingest_market_fixture ───────────────────────────────────────────────

def test_ingest_market_fixture_missing():
    result = handle_ingest_market_fixture(_step(), _ctx())
    assert not result.ok
    assert result.refusal_type == "MarketFixtureMissing"


def test_ingest_market_fixture_invalid_json(tmp_path):
    p = tmp_path / "fix.json"
    p.write_text("bad json")
    result = handle_ingest_market_fixture(_step(fixture_path=str(p)), _ctx())
    assert not result.ok
    assert result.refusal_type == "MarketFixtureInvalid"


def test_ingest_market_fixture_not_dict(tmp_path):
    p = tmp_path / "fix.json"
    p.write_text(json.dumps([1, 2, 3]))
    result = handle_ingest_market_fixture(_step(fixture_path=str(p)), _ctx())
    assert not result.ok


def test_ingest_market_fixture_no_prices(tmp_path):
    p = tmp_path / "fix.json"
    p.write_text(json.dumps({"symbol": "X", "prices": []}))
    result = handle_ingest_market_fixture(_step(fixture_path=str(p)), _ctx())
    assert not result.ok


def test_ingest_market_fixture_success_with_out(tmp_path):
    p = tmp_path / "fix.json"
    p.write_text(json.dumps({"symbol": "EURUSD", "prices": [1.1, 1.2, 1.15]}))
    step = _step(fixture_path=str(p), out_path="snap.json")
    result = handle_ingest_market_fixture(step, _ctx(tmp_path=tmp_path))
    assert result.ok
    assert (tmp_path / "snap.json").exists()


def test_ingest_market_fixture_success_no_out(tmp_path):
    p = tmp_path / "fix.json"
    p.write_text(json.dumps({"symbol": "EURUSD", "prices": [1.1, 1.2]}))
    step = _step(fixture_path=str(p))
    result = handle_ingest_market_fixture(step, _ctx())
    assert result.ok
    assert "market_snapshot" in result.artifact_digests


# ── handle_compute_signal ──────────────────────────────────────────────────────

def _make_snapshot(tmp_path, prices):
    p = tmp_path / "snap.json"
    p.write_text(json.dumps({"symbol": "X", "prices": prices}))
    return p


def _make_policy(tmp_path, threshold=0.01):
    p = tmp_path / "policy.json"
    p.write_text(json.dumps({"signal_threshold": threshold}))
    return p


def test_compute_signal_missing_inputs():
    result = handle_compute_signal(_step(), _ctx())
    assert not result.ok
    assert result.refusal_type == "SignalInputsMissing"


def test_compute_signal_buy(tmp_path):
    snap = _make_snapshot(tmp_path, [1.0, 1.05])
    pol = _make_policy(tmp_path, threshold=0.01)
    step = _step(market_snapshot_path=str(snap), policy_path=str(pol), out_path="sig.json")
    result = handle_compute_signal(step, _ctx(tmp_path=tmp_path))
    assert result.ok
    sig = json.loads((tmp_path / "sig.json").read_text())
    assert sig["action"] == "BUY"


def test_compute_signal_sell(tmp_path):
    snap = _make_snapshot(tmp_path, [1.05, 1.0])
    pol = _make_policy(tmp_path, threshold=0.01)
    step = _step(market_snapshot_path=str(snap), policy_path=str(pol))
    result = handle_compute_signal(step, _ctx())
    assert result.ok
    assert "signal" in result.artifact_digests


def test_compute_signal_hold(tmp_path):
    snap = _make_snapshot(tmp_path, [1.0, 1.0])
    pol = _make_policy(tmp_path, threshold=0.1)
    step = _step(market_snapshot_path=str(snap), policy_path=str(pol))
    result = handle_compute_signal(step, _ctx())
    assert result.ok


# ── handle_simulate_order ──────────────────────────────────────────────────────

def _make_signal(tmp_path, action="BUY"):
    p = tmp_path / "sig.json"
    p.write_text(json.dumps({"action": action}))
    return p


def test_simulate_order_missing_inputs():
    result = handle_simulate_order(_step(), _ctx())
    assert not result.ok
    assert result.refusal_type == "OrderInputsMissing"


def test_simulate_order_buy(tmp_path):
    snap = _make_snapshot(tmp_path, [1.0, 1.05])
    sig = _make_signal(tmp_path, "BUY")
    pol = _make_policy(tmp_path)
    step = _step(
        market_snapshot_path=str(snap),
        signal_path=str(sig),
        policy_path=str(pol),
        out_path="fill.json",
    )
    result = handle_simulate_order(step, _ctx(tmp_path=tmp_path))
    assert result.ok


def test_simulate_order_sell(tmp_path):
    snap = _make_snapshot(tmp_path, [1.05, 1.0])
    sig = _make_signal(tmp_path, "SELL")
    pol = _make_policy(tmp_path)
    step = _step(
        market_snapshot_path=str(snap),
        signal_path=str(sig),
        policy_path=str(pol),
    )
    result = handle_simulate_order(step, _ctx())
    assert result.ok


# ── handle_update_risk_envelope ────────────────────────────────────────────────

def _make_fill(tmp_path, action="BUY", executed=True, order_size=1.0, last_price=1.0, fill_price=1.05):
    p = tmp_path / "fill.json"
    p.write_text(json.dumps({
        "action": action, "executed": executed,
        "order_size": order_size, "last_price": last_price, "fill_price": fill_price,
    }))
    return p


def test_update_risk_envelope_missing_inputs():
    result = handle_update_risk_envelope(_step(), _ctx())
    assert not result.ok


def test_update_risk_envelope_ok(tmp_path):
    fill = _make_fill(tmp_path, action="BUY", executed=True, fill_price=1.0, last_price=1.05)
    pol = tmp_path / "pol.json"
    pol.write_text(json.dumps({"initial_equity": 10000.0, "max_drawdown": 0.5}))
    step = _step(trade_fill_path=str(fill), policy_path=str(pol), out_path="env.json")
    result = handle_update_risk_envelope(step, _ctx(tmp_path=tmp_path))
    assert result.ok


def test_update_risk_envelope_drawdown_violation(tmp_path):
    fill = _make_fill(tmp_path, action="SELL", executed=True, fill_price=0.5, last_price=1.0, order_size=10000)
    pol = tmp_path / "pol.json"
    pol.write_text(json.dumps({"initial_equity": 1000.0, "max_drawdown": 0.0}))
    step = _step(trade_fill_path=str(fill), policy_path=str(pol))
    result = handle_update_risk_envelope(step, _ctx())
    assert not result.ok
    assert result.refusal_type == "RiskEnvelopeViolation"


# ── handle_sim_market_model_load ───────────────────────────────────────────────

def test_sim_market_model_load_missing():
    result = handle_sim_market_model_load(_step(), _ctx())
    assert not result.ok
    assert result.refusal_type == "ShadowModelMissing"


def test_sim_market_model_load_invalid_json(tmp_path):
    p = tmp_path / "model.json"
    p.write_text("bad json")
    result = handle_sim_market_model_load(_step(model_path=str(p)), _ctx())
    assert not result.ok
    assert result.refusal_type == "ShadowModelInvalid"


def test_sim_market_model_load_bad_seed(tmp_path):
    p = tmp_path / "model.json"
    p.write_text(json.dumps({"seed": "tooshort"}))
    result = handle_sim_market_model_load(_step(model_path=str(p)), _ctx())
    assert not result.ok
    assert result.refusal_type == "ShadowModelInvalid"


def test_sim_market_model_load_success(tmp_path):
    p = tmp_path / "model.json"
    p.write_text(json.dumps({
        "seed": "a" * 64,
        "model_id": "test",
        "spread_bps": 2.0,
        "slippage_bps": 1.0,
    }))
    step = _step(model_path=str(p), out_path="model_out.json")
    result = handle_sim_market_model_load(step, _ctx(tmp_path=tmp_path))
    assert result.ok


# ── handle_sim_regime_shift_step ───────────────────────────────────────────────

def test_sim_regime_shift_missing():
    result = handle_sim_regime_shift_step(_step(), _ctx())
    assert not result.ok


def test_sim_regime_shift_success(tmp_path):
    snap = _make_snapshot(tmp_path, [1.0, 1.01, 1.02])
    model = tmp_path / "model.json"
    model.write_text(json.dumps({"regime_shift_bps": 100.0}))
    step = _step(market_snapshot_path=str(snap), model_path=str(model), out_path="regime.json")
    result = handle_sim_regime_shift_step(step, _ctx(tmp_path=tmp_path))
    assert result.ok


# ── handle_sim_latency_apply ───────────────────────────────────────────────────

def test_sim_latency_apply_missing():
    result = handle_sim_latency_apply(_step(), _ctx())
    assert not result.ok
    assert result.refusal_type == "LatencyInputsMissing"


def test_sim_latency_apply_staleness_violation(tmp_path):
    snap = _make_snapshot(tmp_path, [1.0, 1.01])
    model = tmp_path / "model.json"
    model.write_text(json.dumps({"latency_steps": 10}))
    pol = tmp_path / "pol.json"
    pol.write_text(json.dumps({"max_staleness_steps": 0}))
    step = _step(
        market_snapshot_path=str(snap),
        model_path=str(model),
        policy_path=str(pol),
    )
    result = handle_sim_latency_apply(step, _ctx())
    assert not result.ok
    assert result.refusal_type == "StalenessViolation"


# ── handle_evaluate_agent_proposal ────────────────────────────────────────────

def _write_json(tmp_path, name, data):
    p = tmp_path / name
    p.write_text(json.dumps(data))
    return p


def test_evaluate_agent_proposal_missing_inputs():
    result = handle_evaluate_agent_proposal(_step(), _ctx())
    assert not result.ok
    assert result.refusal_type == "AgentInputsMissing"


def test_evaluate_agent_proposal_invalid_json(tmp_path):
    proposal = tmp_path / "prop.json"
    proposal.write_text("bad")
    policy = tmp_path / "pol.json"
    policy.write_text(json.dumps({}))
    step = _step(proposal_path=str(proposal), policy_path=str(policy))
    result = handle_evaluate_agent_proposal(step, _ctx(tmp_path=tmp_path))
    assert not result.ok
    assert result.refusal_type == "AgentProposalInvalid"


def test_evaluate_agent_proposal_not_dict(tmp_path):
    proposal = tmp_path / "prop.json"
    proposal.write_text(json.dumps([1, 2]))
    policy = _write_json(tmp_path, "pol.json", {})
    step = _step(proposal_path=str(proposal), policy_path=str(policy))
    result = handle_evaluate_agent_proposal(step, _ctx(tmp_path=tmp_path))
    assert not result.ok


def test_evaluate_agent_proposal_action_not_allowed(tmp_path):
    proposal = _write_json(tmp_path, "prop.json", {"action": "FORBIDDEN", "risk_score": 0.1, "required_capabilities": []})
    policy = _write_json(tmp_path, "pol.json", {"allowed_actions": ["TRADE"], "max_risk_score": 1.0, "allowed_capabilities": []})
    step = _step(proposal_path=str(proposal), policy_path=str(policy))
    result = handle_evaluate_agent_proposal(step, _ctx(tmp_path=tmp_path))
    assert not result.ok
    assert result.refusal_type == "AgentProposalRefused"


def test_evaluate_agent_proposal_risk_exceeded(tmp_path):
    proposal = _write_json(tmp_path, "prop.json", {"action": "TRADE", "risk_score": 0.9, "required_capabilities": []})
    policy = _write_json(tmp_path, "pol.json", {"allowed_actions": ["TRADE"], "max_risk_score": 0.5, "allowed_capabilities": []})
    step = _step(proposal_path=str(proposal), policy_path=str(policy))
    result = handle_evaluate_agent_proposal(step, _ctx(tmp_path=tmp_path))
    assert not result.ok
    assert any("risk_score" in r for r in result.refusal_reasons)


def test_evaluate_agent_proposal_capability_missing(tmp_path):
    proposal = _write_json(tmp_path, "prop.json", {"action": "TRADE", "risk_score": 0.1, "required_capabilities": ["CAP_X"]})
    policy = _write_json(tmp_path, "pol.json", {"allowed_actions": ["TRADE"], "max_risk_score": 1.0, "allowed_capabilities": ["CAP_Y"]})
    step = _step(proposal_path=str(proposal), policy_path=str(policy))
    result = handle_evaluate_agent_proposal(step, _ctx(tmp_path=tmp_path))
    assert not result.ok
    assert any("CAP_X" in r for r in result.refusal_reasons)


def test_evaluate_agent_proposal_success(tmp_path):
    proposal = _write_json(tmp_path, "prop.json", {"action": "TRADE", "risk_score": 0.1, "required_capabilities": ["CAP_A"]})
    policy = _write_json(tmp_path, "pol.json", {"allowed_actions": ["TRADE"], "max_risk_score": 1.0, "allowed_capabilities": ["CAP_A"]})
    step = _step(proposal_path=str(proposal), policy_path=str(policy), decision_path="dec.json")
    result = handle_evaluate_agent_proposal(step, _ctx(tmp_path=tmp_path))
    assert result.ok


def test_evaluate_agent_proposal_invalid_risk_score(tmp_path):
    proposal = _write_json(tmp_path, "prop.json", {"action": "TRADE", "risk_score": "not-a-number"})
    policy = _write_json(tmp_path, "pol.json", {"allowed_actions": ["TRADE"], "max_risk_score": 1.0, "allowed_capabilities": []})
    step = _step(proposal_path=str(proposal), policy_path=str(policy))
    result = handle_evaluate_agent_proposal(step, _ctx(tmp_path=tmp_path))
    assert not result.ok
    assert any("risk_score invalid" in r for r in result.refusal_reasons)


# ── handle_invert_constraints ──────────────────────────────────────────────────

def test_invert_constraints_missing_witness():
    result = handle_invert_constraints(_step(), _ctx())
    assert not result.ok
    assert result.refusal_type == "WitnessMissing"


def test_invert_constraints_invalid_witness():
    result = handle_invert_constraints(_step(constraint_witness="not a dict"), _ctx())
    assert not result.ok
    assert result.refusal_type == "WitnessInvalid"


def test_invert_constraints_success_inline(tmp_path):
    witness = {
        "stage": "runtime_refusal",
        "refusal_reasons": ["budget_exceeded"],
        "artifact_digests": {},
        "observer_id": "papas",
        "timestamp": "t",
    }
    step = _step(constraint_witness=witness, out_path="dual.json")
    result = handle_invert_constraints(step, _ctx(tmp_path=tmp_path))
    assert result.ok


# ── IO handlers (mock) ─────────────────────────────────────────────────────────

class TestIOHandlersMocked:
    """Test IO handlers in mock mode (no adapter, no env var)."""

    def test_io_connect_no_policy(self, tmp_path):
        step = _step()
        result = handle_io_connect(step, _ctx(tmp_path=tmp_path))
        assert not result.ok  # no io policy → denied

    def test_io_connect_mock_mode(self, tmp_path):
        token = ExecutionToken.build(
            allowed_backends=["CLASSICAL"],
            io_policy={
                "io_allowed": True,
                "io_scopes": ["BROKER_CONNECT"],
                "io_mode": "live",
            },
        )
        step = _step(endpoint="ws://mock")
        result = handle_io_connect(step, _ctx(tmp_path=tmp_path, token=token, io_enabled=False))
        assert result.ok  # adapter=None → mock response

    def test_io_submit_order_mock(self, tmp_path):
        token = ExecutionToken.build(
            allowed_backends=["CLASSICAL"],
            io_policy={
                "io_allowed": True,
                "io_scopes": ["ORDER_SUBMIT"],
                "io_mode": "live",
            },
        )
        step = _step(order={"symbol": "EURUSD", "qty": 1})
        result = handle_io_submit_order(step, _ctx(tmp_path=tmp_path, token=token, io_enabled=False))
        assert result.ok

    def test_io_query_fills_missing_order_id(self, tmp_path):
        token = _io_token()
        step = _step()
        result = handle_io_query_fills(step, _ctx(tmp_path=tmp_path, token=token, io_enabled=False))
        assert not result.ok
        assert result.refusal_type == "OrderIdMissing"

    def test_io_query_fills_mock(self, tmp_path):
        token = _io_token()
        step = _step(order_id="ord123")
        result = handle_io_query_fills(step, _ctx(tmp_path=tmp_path, token=token, io_enabled=False))
        assert result.ok

    def test_io_emit_event_mock(self, tmp_path):
        token = _io_token()
        step = _step(event_type="trade_confirmed")
        result = handle_io_emit_io_event(step, _ctx(tmp_path=tmp_path, token=token, io_enabled=False))
        assert result.ok


class TestIOReconcile:
    def test_reconcile_missing_paths(self, tmp_path):
        token = _io_token()
        step = _step()
        result = handle_io_reconcile(step, _ctx(tmp_path=tmp_path, token=token, io_enabled=False))
        assert not result.ok

    def test_reconcile_ok(self, tmp_path):
        token = _io_token()
        req = tmp_path / "req.json"
        req.write_text(json.dumps({"action": "submit"}))
        resp = tmp_path / "resp.json"
        resp.write_text(json.dumps({"status": "accepted"}))
        step = _step(request_path=str(req), response_path=str(resp), expected_status="accepted")
        result = handle_io_reconcile(step, _ctx(tmp_path=tmp_path, token=token))
        assert result.ok

    def test_reconcile_status_mismatch(self, tmp_path):
        token = _io_token()
        req = tmp_path / "req.json"
        req.write_text(json.dumps({"action": "submit"}))
        resp = tmp_path / "resp.json"
        resp.write_text(json.dumps({"status": "rejected"}))
        step = _step(request_path=str(req), response_path=str(resp), expected_status="accepted")
        result = handle_io_reconcile(step, _ctx(tmp_path=tmp_path, token=token))
        # action=rollback due to io_requires_reconciliation default
        assert not result.ok

    def test_reconcile_ambiguous(self, tmp_path):
        token = _io_token()
        req = tmp_path / "req.json"
        req.write_text(json.dumps({"action": "submit"}))
        resp = tmp_path / "resp.json"
        resp.write_text(json.dumps({"status": "ok", "ambiguous": True}))
        step = _step(request_path=str(req), response_path=str(resp))
        result = handle_io_reconcile(step, _ctx(tmp_path=tmp_path, token=token))
        assert not result.ok


# ── NET handlers (mock) ────────────────────────────────────────────────────────

class TestNetHandlersMocked:
    """NET handlers in dry_run mode → adapter=None → mock responses."""

    def _net_ctx(self, tmp_path):
        return _ctx(tmp_path=tmp_path, token=_net_token(), net_enabled=True)

    def test_net_connect_no_policy(self, tmp_path):
        result = handle_net_connect(_step(), _ctx(tmp_path=tmp_path))
        assert not result.ok  # no net policy → denied

    def test_net_connect_mock(self, tmp_path):
        result = handle_net_connect(_step(endpoint="ws://host"), self._net_ctx(tmp_path))
        assert result.ok

    def test_net_handshake_mock(self, tmp_path):
        result = handle_net_handshake(_step(endpoint="ws://host"), self._net_ctx(tmp_path))
        assert result.ok

    def test_net_key_exchange_mock(self, tmp_path):
        result = handle_net_key_exchange(_step(endpoint="ws://host"), self._net_ctx(tmp_path))
        assert result.ok

    def test_net_send_mock(self, tmp_path):
        result = handle_net_send(_step(endpoint="ws://host", payload={"msg": "hi"}), self._net_ctx(tmp_path))
        assert result.ok

    def test_net_recv_mock(self, tmp_path):
        result = handle_net_recv(_step(endpoint="ws://host"), self._net_ctx(tmp_path))
        assert result.ok

    def test_net_close_mock(self, tmp_path):
        result = handle_net_close(_step(endpoint="ws://host"), self._net_ctx(tmp_path))
        assert result.ok


# ── _resolve_io_adapter with env var ──────────────────────────────────────────

def test_resolve_io_adapter_env_not_set(tmp_path):
    token = _io_token()
    ctx = RuntimeContext(trace_sink=tmp_path, execution_token=token, io_enabled=True)
    import os
    env = {k: v for k, v in os.environ.items() if k != "HPL_IO_ENABLED"}
    with patch.dict("os.environ", env, clear=True):
        step = _step()
        result = handle_io_connect(step, ctx)
    assert not result.ok
    assert result.refusal_type == "IOGuardNotEnabled"


def test_resolve_net_adapter_env_not_set(tmp_path):
    token = ExecutionToken.build(
        allowed_backends=["CLASSICAL"],
        net_policy={"net_caps": ["NET_CONNECT"], "net_mode": "live"},
    )
    ctx = RuntimeContext(trace_sink=tmp_path, execution_token=token, net_enabled=True)
    import os
    env = {k: v for k, v in os.environ.items() if k != "HPL_NET_ENABLED"}
    with patch.dict("os.environ", env, clear=True):
        result = handle_net_connect(_step(), ctx)
    assert not result.ok
    assert result.refusal_type == "NetGuardNotEnabled"
