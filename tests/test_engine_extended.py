"""Extended tests for RuntimeEngine to cover missed branches."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from hpl.execution_token import ExecutionToken
from hpl.runtime.context import RuntimeContext
from hpl.runtime.contracts import ExecutionContract
from hpl.runtime.engine import (
    RuntimeEngine,
    RuntimeResult,
    _canonical_json,
    _digest_text,
    _is_measurement_effect,
    _plan_to_dict,
    _required_delta_s_roles,
    _requires_delta_s,
    _requires_io,
    _requires_net,
    _steps_from_plan,
    _token_from_plan,
    _update_evidence_roles,
)


def _basic_token(**kwargs):
    defaults = {"allowed_backends": ["CLASSICAL"]}
    defaults.update(kwargs)
    return ExecutionToken.build(**defaults)


def _planned_step(operator_id="op1", effect_type="NOOP", requires=None):
    s = {"operator_id": operator_id, "allowed_steps": [operator_id], "effect_type": effect_type}
    if requires:
        s["requires"] = requires
    return s


def _planned_plan(steps=None, token=None):
    t = token or _basic_token()
    plan = {
        "plan_id": "plan1",
        "status": "planned",
        "steps": steps or [],
        "execution_token": t.to_dict(),
    }
    return plan


def _make_ctx(**kwargs):
    defaults = {}
    defaults.update(kwargs)
    return RuntimeContext(**defaults)


def _make_contract(**kwargs):
    defaults = {}
    defaults.update(kwargs)
    return ExecutionContract(**defaults)


class TestEngineNoToken:
    def test_missing_token_denied(self):
        engine = RuntimeEngine()
        plan = {"plan_id": "p", "status": "planned", "steps": []}
        ctx = _make_ctx()
        result = engine.run(plan, ctx, _make_contract())
        assert result.status == "denied"
        assert any("execution token missing" in r for r in result.reasons)

    def test_token_from_plan_dict(self):
        engine = RuntimeEngine()
        t = _basic_token()
        plan = _planned_plan(token=t)
        ctx = _make_ctx()  # no token in ctx
        result = engine.run(plan, ctx, _make_contract())
        assert result.status == "completed"


class TestEnginePlanStatus:
    def test_not_planned_denied(self):
        engine = RuntimeEngine()
        t = _basic_token()
        plan = {"plan_id": "p", "status": "denied", "steps": [], "execution_token": t.to_dict()}
        ctx = _make_ctx(execution_token=t)
        result = engine.run(plan, ctx, _make_contract())
        assert result.status == "denied"
        assert any("plan not approved" in r for r in result.reasons)


class TestEngineBudgetSteps:
    def test_budget_steps_exceeded(self):
        engine = RuntimeEngine()
        t = ExecutionToken.build(allowed_backends=["CLASSICAL"], budget_steps=1)
        steps = [
            _planned_step("op1"),
            _planned_step("op2"),
        ]
        plan = _planned_plan(steps=steps, token=t)
        ctx = _make_ctx(execution_token=t)
        result = engine.run(plan, ctx, _make_contract())
        # Second step should be denied
        assert result.status == "denied"
        assert any("budget_steps_exceeded" in r for r in result.reasons)

    def test_zero_budget_steps(self):
        engine = RuntimeEngine()
        t = ExecutionToken.build(allowed_backends=["CLASSICAL"], budget_steps=0)
        plan = _planned_plan(steps=[_planned_step("op1")], token=t)
        ctx = _make_ctx(execution_token=t)
        result = engine.run(plan, ctx, _make_contract())
        assert result.status == "denied"


class TestEngineDeltaSBudget:
    def test_delta_s_budget_exceeded(self, tmp_path):
        """With delta_s_budget=1, two measurement steps → second exceeds budget."""
        from unittest.mock import patch
        from hpl.runtime.effects.effect_step import EffectResult

        engine = RuntimeEngine()
        t = ExecutionToken.build(allowed_backends=["CLASSICAL"], delta_s_budget=1)

        def mock_handler(step, ctx):
            return EffectResult(
                step_id=step.step_id,
                effect_type=str(step.effect_type),
                ok=True,
                refusal_type=None,
                refusal_reasons=[],
                artifact_digests={"out": "sha256:abc"},
            )

        steps = [
            _planned_step("op1", effect_type="COMPUTE_DELTA_S"),
            _planned_step("op2", effect_type="COMPUTE_DELTA_S"),
        ]
        plan = _planned_plan(steps=steps, token=t)
        ctx = _make_ctx(execution_token=t, trace_sink=tmp_path)

        with patch("hpl.runtime.engine.get_handler", return_value=mock_handler):
            result = engine.run(plan, ctx, _make_contract())

        assert result.status == "denied"
        assert any("delta_s_budget_exceeded" in r for r in result.reasons)


class TestEngineIOBudget:
    def test_io_budget_exceeded(self):
        engine = RuntimeEngine()
        t = ExecutionToken.build(
            allowed_backends=["CLASSICAL"],
            io_policy={
                "io_allowed": True,
                "io_scopes": ["BROKER_CONNECT"],
                "io_budget_calls": 0,
            }
        )
        step = _planned_step("op1", effect_type="NOOP")
        step["requires"] = {"io_scope": "BROKER_CONNECT"}
        plan = _planned_plan(steps=[step], token=t)
        ctx = _make_ctx(execution_token=t)
        result = engine.run(plan, ctx, _make_contract())
        assert result.status == "denied"
        assert any("IOBudgetExceeded" in r for r in result.reasons)


class TestEngineNetBudget:
    def test_net_budget_exceeded(self):
        engine = RuntimeEngine()
        t = ExecutionToken.build(
            allowed_backends=["CLASSICAL"],
            net_policy={
                "net_caps": ["NET_CONNECT"],
                "net_budget_calls": 0,
            }
        )
        step = _planned_step("op1", effect_type="NOOP")
        step["requires"] = {"net_cap": "NET_CONNECT"}
        net_steps = [step]
        plan = _planned_plan(steps=net_steps, token=t)
        ctx = _make_ctx(execution_token=t)
        result = engine.run(plan, ctx, _make_contract())
        assert result.status == "denied"
        assert any("NetBudgetExceeded" in r for r in result.reasons)


class TestEngineDeltaSGate:
    def test_delta_s_evidence_missing(self):
        engine = RuntimeEngine()
        t = ExecutionToken.build(allowed_backends=["CLASSICAL"], collapse_requires_delta_s=True)
        step = _planned_step("op1", effect_type="NOOP")
        step["requires"] = {"irreversible": True}
        plan = _planned_plan(steps=[step], token=t)
        ctx = _make_ctx(execution_token=t)
        result = engine.run(plan, ctx, _make_contract())
        assert result.status == "denied"
        assert any("delta_s_evidence_missing" in r for r in result.reasons)


class TestEngineContractPreconditions:
    def test_precondition_failure_denied(self):
        engine = RuntimeEngine()
        t = _basic_token()
        step = _planned_step("op_bad", effect_type="NOOP")
        step["requires"] = {"backend": "QASM"}  # not in allowed_backends
        plan = _planned_plan(steps=[step], token=t)
        ctx = _make_ctx(execution_token=t)
        result = engine.run(plan, ctx, _make_contract())
        assert result.status == "denied"


class TestEnginePostconditionFailure:
    def test_postcondition_always_ok(self):
        engine = RuntimeEngine()
        t = _basic_token()
        plan = _planned_plan(steps=[_planned_step()], token=t)
        ctx = _make_ctx(execution_token=t)
        result = engine.run(plan, ctx, _make_contract())
        # Default postconditions always pass
        assert result.status == "completed"


class TestEngineRegistryEnforcement:
    def test_registry_enforced_empty_paths_no_operators(self):
        """Registry enforced with no registry paths → load defaults; unknown op denied."""
        engine = RuntimeEngine()
        t = _basic_token()
        plan = _planned_plan(steps=[_planned_step("totally_unknown_op_xyz")], token=t)
        plan["operator_registry_enforced"] = True
        plan["operator_registry_paths"] = []
        ctx = _make_ctx(execution_token=t)
        result = engine.run(plan, ctx, _make_contract())
        # totally_unknown_op_xyz not in any registry → denied
        assert result.status == "denied"


class TestEngineEpochVerification:
    def test_require_epoch_no_anchor_path(self):
        engine = RuntimeEngine()
        t = _basic_token()
        plan = _planned_plan(token=t)
        ctx = _make_ctx(execution_token=t)
        contract = _make_contract(require_epoch_verification=True)
        result = engine.run(plan, ctx, contract)
        assert result.status == "denied"
        assert any("epoch_anchor_path" in r for r in result.reasons)

    def test_require_epoch_anchor_not_found(self):
        engine = RuntimeEngine()
        t = _basic_token()
        plan = _planned_plan(token=t)
        ctx = _make_ctx(execution_token=t, epoch_anchor_path=Path("/nonexistent/anchor.json"))
        contract = _make_contract(require_epoch_verification=True)
        result = engine.run(plan, ctx, contract)
        assert result.status == "denied"
        assert any("epoch anchor not found" in r or "epoch_anchor_path" in r for r in result.reasons)

    def test_require_signature_no_sig_path(self, tmp_path):
        engine = RuntimeEngine()
        t = _basic_token()
        anchor = {"git_commit": "abc123", "merkle_root": "mr", "timestamp": "t"}
        anchor_path = tmp_path / "anchor.json"
        anchor_path.write_text(json.dumps(anchor))

        mock_verify_epoch = MagicMock()
        mock_verify_epoch.verify_epoch_anchor.return_value = (True, [])

        plan = _planned_plan(token=t)
        ctx = _make_ctx(execution_token=t, epoch_anchor_path=anchor_path)
        contract = _make_contract(
            require_epoch_verification=True,
            require_signature_verification=True,
        )
        with patch("hpl.runtime.engine._load_verify_epoch", return_value=mock_verify_epoch):
            result = engine.run(plan, ctx, contract)
        assert result.status == "denied"
        assert any("epoch_sig_path missing" in r for r in result.reasons)

    def test_require_signature_sig_not_found(self, tmp_path):
        engine = RuntimeEngine()
        t = _basic_token()
        anchor = {"git_commit": "abc123", "merkle_root": "mr", "timestamp": "t"}
        anchor_path = tmp_path / "anchor.json"
        anchor_path.write_text(json.dumps(anchor))

        mock_verify_epoch = MagicMock()
        mock_verify_epoch.verify_epoch_anchor.return_value = (True, [])

        plan = _planned_plan(token=t)
        ctx = _make_ctx(
            execution_token=t,
            epoch_anchor_path=anchor_path,
            epoch_sig_path=Path("/nonexistent/sig.bin"),
        )
        contract = _make_contract(
            require_epoch_verification=True,
            require_signature_verification=True,
        )
        with patch("hpl.runtime.engine._load_verify_epoch", return_value=mock_verify_epoch):
            result = engine.run(plan, ctx, contract)
        assert result.status == "denied"
        assert any("epoch signature not found" in r for r in result.reasons)


class TestPlanToDict:
    def test_dict_passthrough(self):
        plan = {"status": "planned"}
        assert _plan_to_dict(plan) == plan

    def test_object_with_to_dict(self):
        obj = MagicMock()
        obj.to_dict.return_value = {"status": "planned"}
        assert _plan_to_dict(obj) == {"status": "planned"}

    def test_invalid_raises(self):
        with pytest.raises(TypeError):
            _plan_to_dict(42)


class TestTokenFromPlan:
    def test_dict_with_token(self):
        t = _basic_token()
        plan = {"execution_token": t.to_dict()}
        result = _token_from_plan(plan)
        assert result is not None
        assert result.token_id == t.token_id

    def test_object_with_execution_token(self):
        t = _basic_token()
        obj = MagicMock()
        obj.execution_token = t.to_dict()
        result = _token_from_plan(obj)
        assert result is not None

    def test_no_token_returns_none(self):
        assert _token_from_plan({}) is None
        assert _token_from_plan({"execution_token": "not a dict"}) is None


class TestHelperFunctions:
    def test_is_measurement_effect_measure(self):
        assert _is_measurement_effect("MEASURE_CONDITION")
        assert _is_measurement_effect("MEASURE_something")
        assert _is_measurement_effect("COMPUTE_DELTA_S")
        assert _is_measurement_effect("DELTA_S_GATE")
        assert not _is_measurement_effect("NOOP")
        assert not _is_measurement_effect("IO_CONNECT")

    def test_requires_delta_s_no_token(self):
        assert not _requires_delta_s({}, None)

    def test_requires_delta_s_not_collapse(self):
        t = _basic_token()  # collapse_requires_delta_s=False
        assert not _requires_delta_s({"requires": {"irreversible": True}}, t)

    def test_requires_delta_s_with_collapse(self):
        t = ExecutionToken.build(allowed_backends=["CLASSICAL"], collapse_requires_delta_s=True)
        assert _requires_delta_s({"requires": {"irreversible": True}}, t)
        assert not _requires_delta_s({"requires": {"irreversible": False}}, t)
        assert not _requires_delta_s({}, t)

    def test_required_delta_s_roles_default(self):
        roles = _required_delta_s_roles({})
        assert "delta_s_report" in roles
        assert "admissibility_certificate" in roles
        assert "collapse_decision" in roles

    def test_required_delta_s_roles_custom(self):
        step = {"requires": {"required_roles": ["role_a", "role_b"]}}
        roles = _required_delta_s_roles(step)
        assert roles == {"role_a", "role_b"}

    def test_required_delta_s_roles_empty_list(self):
        step = {"requires": {"required_roles": []}}
        roles = _required_delta_s_roles(step)
        assert "delta_s_report" in roles  # falls back to default

    def test_update_evidence_roles(self):
        roles: set = set()
        _update_evidence_roles(roles, {"delta_s_report.json": "sha256:abc"})
        assert "delta_s_report" in roles
        _update_evidence_roles(roles, {"admissibility_certificate.json": "sha256:abc"})
        assert "admissibility_certificate" in roles
        _update_evidence_roles(roles, {"collapse_decision.json": "sha256:abc"})
        assert "collapse_decision" in roles
        _update_evidence_roles(roles, {"measurement_trace.json": "sha256:abc"})
        assert "measurement_trace" in roles

    def test_requires_io(self):
        assert _requires_io({"requires": {"io_scope": "BROKER_CONNECT"}})
        assert _requires_io({"requires": {"io_scopes": ["BROKER_CONNECT"]}})
        assert _requires_io({"requires": {"io_endpoint": "http://x"}})
        assert not _requires_io({"requires": {}})
        assert not _requires_io({})
        assert not _requires_io({"requires": "not a dict"})

    def test_requires_net(self):
        assert _requires_net({"requires": {"net_cap": "NET_CONNECT"}})
        assert _requires_net({"requires": {"net_caps": ["NET_CONNECT"]}})
        assert _requires_net({"requires": {"net_endpoint": "ws://x"}})
        assert not _requires_net({"requires": {}})
        assert not _requires_net({})

    def test_steps_from_plan(self):
        plan = {"steps": [{"effect_type": "NOOP"}, "not a dict", {"effect_type": "NOOP"}]}
        steps = _steps_from_plan(plan)
        assert len(steps) == 2

    def test_steps_from_plan_not_list(self):
        assert _steps_from_plan({"steps": "bad"}) == []
        assert _steps_from_plan({}) == []


class TestRuntimeResultToDict:
    def test_to_dict_structure(self):
        result = RuntimeResult(
            result_id="r1",
            status="completed",
            reasons=[],
            steps=[],
            verification=None,
            witness_records=[],
            constraint_witnesses=[],
            transcript=[],
            observer_reports=[],
        )
        d = result.to_dict()
        assert d["result_id"] == "r1"
        assert d["status"] == "completed"
        assert isinstance(d["steps"], list)
