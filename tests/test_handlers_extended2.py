"""Handlers batch 2 — covers verify_epoch, verify_signature, validate_*, sign/verify_bundle, sim/NS handlers."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from hpl.execution_token import ExecutionToken
from hpl.runtime.context import RuntimeContext
from hpl.runtime.effects.effect_step import EffectStep
from hpl.runtime.effects.effect_types import EffectType
from hpl.runtime.effects.handlers import (
    handle_ns_apply_duhamel,
    handle_ns_check_barrier,
    handle_ns_emit_state,
    handle_ns_evolve_linear,
    handle_ns_measure_observables,
    handle_ns_pressure_recover,
    handle_ns_project_leray,
    handle_sign_bundle,
    handle_sim_emit_trade_ledger,
    handle_sim_latency_apply,
    handle_sim_order_lifecycle,
    handle_sim_partial_fill_model,
    handle_validate_coupling_topology,
    handle_validate_quantum_semantics,
    handle_validate_registries,
    handle_verify_epoch,
    handle_verify_signature,
)


def _step(**args):
    return EffectStep(step_id="s1", effect_type=EffectType.NOOP, args=args)


def _ctx(tmp_path=None):
    return RuntimeContext(trace_sink=tmp_path)


def _wj(tmp_path, name, data):
    p = tmp_path / name
    p.write_text(json.dumps(data))
    return p


# ── handle_verify_epoch ────────────────────────────────────────────────────────

class TestVerifyEpoch:
    def test_missing_anchor(self):
        result = handle_verify_epoch(_step(), _ctx())
        assert not result.ok
        assert result.refusal_type == "AnchorMissing"

    def test_anchor_not_exists(self, tmp_path):
        step = _step(anchor_path=str(tmp_path / "no_anchor.json"))
        result = handle_verify_epoch(step, _ctx(tmp_path))
        assert not result.ok

    def test_epoch_ok(self, tmp_path):
        anchor = {"git_commit": "abc", "merkle_root": "mr", "timestamp": "t"}
        ap = tmp_path / "anchor.json"
        ap.write_text(json.dumps(anchor))

        mock_tool = MagicMock()
        mock_tool.verify_epoch_anchor.return_value = (True, [])

        with patch("hpl.runtime.effects.handlers._load_tool", return_value=mock_tool):
            step = _step(anchor_path=str(ap))
            result = handle_verify_epoch(step, _ctx(tmp_path))
        assert result.ok

    def test_epoch_failed(self, tmp_path):
        anchor = {"git_commit": "abc"}
        ap = tmp_path / "anchor.json"
        ap.write_text(json.dumps(anchor))

        mock_tool = MagicMock()
        mock_tool.verify_epoch_anchor.return_value = (False, ["bad epoch"])

        with patch("hpl.runtime.effects.handlers._load_tool", return_value=mock_tool):
            step = _step(anchor_path=str(ap))
            result = handle_verify_epoch(step, _ctx(tmp_path))
        assert not result.ok
        assert result.refusal_type == "EpochVerificationFailed"


# ── handle_verify_signature ────────────────────────────────────────────────────

class TestVerifySignature:
    def test_missing_inputs(self):
        result = handle_verify_signature(_step(), _ctx())
        assert not result.ok
        assert result.refusal_type == "SignatureInputsMissing"

    def test_files_not_exist(self, tmp_path):
        step = _step(
            anchor_path=str(tmp_path / "a.json"),
            sig_path=str(tmp_path / "s.bin"),
            pub_path=str(tmp_path / "p.pub"),
        )
        result = handle_verify_signature(step, _ctx(tmp_path))
        assert not result.ok

    def test_sig_ok(self, tmp_path):
        ap = tmp_path / "anchor.json"; ap.write_bytes(b'{}')
        sp = tmp_path / "sig.bin";    sp.write_bytes(b'sig')
        pp = tmp_path / "pub.pub";    pp.write_bytes(b'pub')

        mock_tool = MagicMock()
        mock_tool._load_verify_key.return_value = "vk"
        mock_tool.verify_anchor_signature.return_value = (True, [])

        with patch("hpl.runtime.effects.handlers._load_tool", return_value=mock_tool):
            step = _step(anchor_path=str(ap), sig_path=str(sp), pub_path=str(pp))
            result = handle_verify_signature(step, _ctx(tmp_path))
        assert result.ok

    def test_sig_failed(self, tmp_path):
        ap = tmp_path / "anchor.json"; ap.write_bytes(b'{}')
        sp = tmp_path / "sig.bin";    sp.write_bytes(b'sig')
        pp = tmp_path / "pub.pub";    pp.write_bytes(b'pub')

        mock_tool = MagicMock()
        mock_tool._load_verify_key.return_value = "vk"
        mock_tool.verify_anchor_signature.return_value = (False, ["bad sig"])

        with patch("hpl.runtime.effects.handlers._load_tool", return_value=mock_tool):
            step = _step(anchor_path=str(ap), sig_path=str(sp), pub_path=str(pp))
            result = handle_verify_signature(step, _ctx(tmp_path))
        assert not result.ok
        assert result.refusal_type == "SignatureVerificationFailed"


# ── handle_validate_registries ─────────────────────────────────────────────────

class TestValidateRegistries:
    def test_validation_ok(self):
        mock_tool = MagicMock()
        mock_tool._load_schema.return_value = {}
        mock_tool._resolve_registry_paths.return_value = []
        mock_tool.validate_registry_file.return_value = []

        with patch("hpl.runtime.effects.handlers._load_tool", return_value=mock_tool):
            result = handle_validate_registries(_step(), _ctx())
        assert result.ok

    def test_validation_failed(self, tmp_path):
        fake_reg = tmp_path / "reg.json"
        fake_reg.write_text("{}")

        mock_tool = MagicMock()
        mock_tool._load_schema.return_value = {}
        mock_tool._resolve_registry_paths.return_value = [fake_reg]
        mock_tool.validate_registry_file.return_value = ["schema error"]

        with patch("hpl.runtime.effects.handlers._load_tool", return_value=mock_tool):
            result = handle_validate_registries(_step(), _ctx(tmp_path))
        assert not result.ok
        assert result.refusal_type == "RegistryValidationFailed"


# ── handle_validate_coupling_topology ─────────────────────────────────────────

class TestValidateCouplingTopology:
    def test_missing_registry(self):
        result = handle_validate_coupling_topology(_step(), _ctx())
        assert not result.ok
        assert result.refusal_type == "CouplingRegistryMissing"

    def test_topology_ok(self, tmp_path):
        reg = tmp_path / "coupling.json"
        reg.write_text("{}")

        mock_tool = MagicMock()
        mock_tool.validate_coupling_registry_file.return_value = []

        with patch("hpl.runtime.effects.handlers._load_tool", return_value=mock_tool):
            step = _step(registry_path=str(reg))
            result = handle_validate_coupling_topology(step, _ctx(tmp_path))
        assert result.ok

    def test_topology_invalid(self, tmp_path):
        reg = tmp_path / "coupling.json"
        reg.write_text("{}")

        mock_tool = MagicMock()
        mock_tool.validate_coupling_registry_file.return_value = ["bad edge"]

        with patch("hpl.runtime.effects.handlers._load_tool", return_value=mock_tool):
            step = _step(registry_path=str(reg))
            result = handle_validate_coupling_topology(step, _ctx(tmp_path))
        assert not result.ok
        assert result.refusal_type == "CouplingTopologyInvalid"


# ── handle_validate_quantum_semantics ─────────────────────────────────────────

class TestValidateQuantumSemantics:
    def test_semantics_ok(self):
        mock_tool = MagicMock()
        mock_tool.validate_quantum_execution_semantics.return_value = {"ok": True, "errors": []}

        with patch("hpl.runtime.effects.handlers._load_tool", return_value=mock_tool):
            result = handle_validate_quantum_semantics(_step(), _ctx())
        assert result.ok

    def test_semantics_invalid(self):
        mock_tool = MagicMock()
        mock_tool.validate_quantum_execution_semantics.return_value = {"ok": False, "errors": ["missing IR"]}

        with patch("hpl.runtime.effects.handlers._load_tool", return_value=mock_tool):
            result = handle_validate_quantum_semantics(_step(), _ctx())
        assert not result.ok
        assert result.refusal_type == "QuantumSemanticsInvalid"


# ── handle_sign_bundle ─────────────────────────────────────────────────────────

class TestSignBundle:
    def test_missing_inputs(self):
        result = handle_sign_bundle(_step(), _ctx())
        assert not result.ok
        assert result.refusal_type == "BundleSigningInputsMissing"

    def test_files_not_exist(self, tmp_path):
        step = _step(bundle_manifest=str(tmp_path / "m.json"), signing_key=str(tmp_path / "k.key"))
        result = handle_sign_bundle(step, _ctx(tmp_path))
        assert not result.ok

    def test_sign_ok(self, tmp_path):
        manifest = tmp_path / "manifest.json"; manifest.write_bytes(b'{}')
        key = tmp_path / "key.key";            key.write_bytes(b'key')
        sig = tmp_path / "manifest.json.sig";  sig.write_bytes(b'sig')

        mock_tool = MagicMock()
        mock_tool.sign_bundle_manifest.return_value = sig

        with patch("hpl.runtime.effects.handlers._load_tool", return_value=mock_tool):
            step = _step(bundle_manifest=str(manifest), signing_key=str(key))
            result = handle_sign_bundle(step, _ctx(tmp_path))
        assert result.ok


# ── sim handlers ───────────────────────────────────────────────────────────────

def _snap(tmp_path, prices=None):
    p = tmp_path / "snap.json"
    p.write_text(json.dumps({"symbol": "X", "prices": prices or [1.0, 1.01]}))
    return p

def _model(tmp_path, **kw):
    p = tmp_path / "model.json"
    p.write_text(json.dumps({"seed": "a"*64, "latency_steps": 1, "spread_bps": 1.0,
                              "slippage_bps": 0.5, "partial_fill_ratio": 0.8, **kw}))
    return p

def _pol(tmp_path, **kw):
    p = tmp_path / "pol.json"
    p.write_text(json.dumps(kw))
    return p

def _fill(tmp_path, action="BUY", executed=True, fill_fraction=1.0, order_size=1.0, fill_price=1.01, last_price=1.0):
    p = tmp_path / "fill.json"
    p.write_text(json.dumps({
        "action": action, "executed": executed, "fill_fraction": fill_fraction,
        "filled_size": order_size * fill_fraction, "order_size": order_size,
        "fill_price": fill_price, "last_price": last_price,
    }))
    return p


class TestSimPartialFillModel:
    def test_missing(self):
        result = handle_sim_partial_fill_model(_step(), _ctx())
        assert not result.ok

    def test_fill_too_low(self, tmp_path):
        f = _fill(tmp_path)
        m = _model(tmp_path, partial_fill_ratio=0.1)
        p = _pol(tmp_path, min_fill_ratio=0.5)
        step = _step(trade_fill_path=str(f), model_path=str(m), policy_path=str(p))
        result = handle_sim_partial_fill_model(step, _ctx(tmp_path))
        assert not result.ok
        assert result.refusal_type == "PartialFillTooLow"

    def test_ok(self, tmp_path):
        f = _fill(tmp_path)
        m = _model(tmp_path, partial_fill_ratio=0.8)
        p = _pol(tmp_path, min_fill_ratio=0.5)
        step = _step(trade_fill_path=str(f), model_path=str(m), policy_path=str(p), out_path="sf.json")
        result = handle_sim_partial_fill_model(step, _ctx(tmp_path))
        assert result.ok


class TestSimOrderLifecycle:
    def test_missing(self):
        result = handle_sim_order_lifecycle(_step(), _ctx())
        assert not result.ok

    def test_executed_full(self, tmp_path):
        sf = tmp_path / "sf.json"
        sf.write_text(json.dumps({"executed": True, "fill_fraction": 1.0}))
        m = _model(tmp_path, latency_steps=2)
        step = _step(shadow_fill_path=str(sf), model_path=str(m), out_path="log.json")
        result = handle_sim_order_lifecycle(step, _ctx(tmp_path))
        assert result.ok

    def test_executed_partial(self, tmp_path):
        sf = tmp_path / "sf.json"
        sf.write_text(json.dumps({"executed": True, "fill_fraction": 0.5}))
        m = _model(tmp_path)
        step = _step(shadow_fill_path=str(sf), model_path=str(m))
        result = handle_sim_order_lifecycle(step, _ctx(tmp_path))
        assert result.ok

    def test_not_executed(self, tmp_path):
        sf = tmp_path / "sf.json"
        sf.write_text(json.dumps({"executed": False, "fill_fraction": 0.0}))
        m = _model(tmp_path)
        step = _step(shadow_fill_path=str(sf), model_path=str(m))
        result = handle_sim_order_lifecycle(step, _ctx(tmp_path))
        assert result.ok


class TestSimEmitTradeLedger:
    def test_missing(self):
        result = handle_sim_emit_trade_ledger(_step(), _ctx())
        assert not result.ok

    def test_ok(self, tmp_path):
        f = _fill(tmp_path)
        r = tmp_path / "risk.json"
        r.write_text(json.dumps({"equity": 10100.0, "drawdown": 0.0, "pnl": 100.0}))
        s = tmp_path / "sig.json"
        s.write_text(json.dumps({"action": "BUY"}))
        step = _step(shadow_fill_path=str(f), risk_envelope_path=str(r), signal_path=str(s))
        result = handle_sim_emit_trade_ledger(step, _ctx(tmp_path))
        assert result.ok


class TestSimLatencyApply:
    def test_ok(self, tmp_path):
        snap = _snap(tmp_path, [1.0, 1.01, 1.02])
        m = _model(tmp_path, latency_steps=1, spread_bps=2.0, slippage_bps=1.0)
        p = _pol(tmp_path, max_staleness_steps=5)
        step = _step(market_snapshot_path=str(snap), model_path=str(m), policy_path=str(p), out_path="lat.json")
        result = handle_sim_latency_apply(step, _ctx(tmp_path))
        assert result.ok


# ── NS (Navier-Stokes) handlers ────────────────────────────────────────────────

def _ns_state(tmp_path, nx=2, ny=2, u=0.1, v=0.0):
    state = {
        "grid": {"nx": nx, "ny": ny, "dx": 1.0, "dy": 1.0},
        "field": [{"u": u, "v": v}] * (nx * ny),
        "t": 0.0, "dt": 0.01, "nu": 0.01,
    }
    p = tmp_path / "state.json"
    p.write_text(json.dumps(state))
    return p


class TestNSHandlers:
    def test_evolve_linear_missing(self):
        result = handle_ns_evolve_linear(_step(), _ctx())
        assert not result.ok

    def test_evolve_linear_ok(self, tmp_path):
        sp = _ns_state(tmp_path)
        step = _step(state_path=str(sp), out_path="ev.json")
        result = handle_ns_evolve_linear(step, _ctx(tmp_path))
        assert result.ok

    def test_apply_duhamel_missing(self):
        result = handle_ns_apply_duhamel(_step(), _ctx())
        assert not result.ok

    def test_apply_duhamel_ok(self, tmp_path):
        sp = _ns_state(tmp_path)
        step = _step(state_path=str(sp), out_path="duh.json")
        result = handle_ns_apply_duhamel(step, _ctx(tmp_path))
        assert result.ok

    def test_project_leray_missing(self):
        result = handle_ns_project_leray(_step(), _ctx())
        assert not result.ok

    def test_project_leray_ok(self, tmp_path):
        sp = _ns_state(tmp_path)
        step = _step(state_path=str(sp), out_path="proj.json")
        result = handle_ns_project_leray(step, _ctx(tmp_path))
        assert result.ok

    def test_pressure_recover_missing(self):
        result = handle_ns_pressure_recover(_step(), _ctx())
        assert not result.ok

    def test_pressure_recover_ok(self, tmp_path):
        sp = _ns_state(tmp_path)
        step = _step(state_path=str(sp), out_path="pres.json")
        result = handle_ns_pressure_recover(step, _ctx(tmp_path))
        assert result.ok

    def test_measure_observables_missing(self):
        result = handle_ns_measure_observables(_step(), _ctx())
        assert not result.ok

    def test_measure_observables_ok(self, tmp_path):
        sp = _ns_state(tmp_path)
        step = _step(state_path=str(sp), out_path="obs.json")
        result = handle_ns_measure_observables(step, _ctx(tmp_path))
        assert result.ok

    def test_emit_state_missing(self):
        result = handle_ns_emit_state(_step(), _ctx())
        assert not result.ok

    def test_emit_state_ok(self, tmp_path):
        sp = _ns_state(tmp_path)
        step = _step(state_path=str(sp), out_path="final.json")
        result = handle_ns_emit_state(step, _ctx(tmp_path))
        assert result.ok

    def test_check_barrier_missing(self):
        result = handle_ns_check_barrier(_step(), _ctx())
        assert not result.ok

    def test_check_barrier_ok(self, tmp_path):
        sp = _ns_state(tmp_path)
        # First emit observables
        obs_step = _step(state_path=str(sp), out_path="obs.json")
        handle_ns_measure_observables(obs_step, _ctx(tmp_path))
        obs_path = tmp_path / "obs.json"
        pol = _pol(tmp_path, max_energy=1000.0, max_cfl=100.0)
        step = _step(observables_path=str(obs_path), policy_path=str(pol))
        result = handle_ns_check_barrier(step, _ctx(tmp_path))
        assert result.ok

    def test_check_barrier_energy_violated(self, tmp_path):
        obs = tmp_path / "obs.json"
        obs.write_text(json.dumps({"energy": 999.0, "divergence_residual": 0.0,
                                    "dissipation": 0.0, "cfl": 0.0, "dt": 0.01}))
        pol = _pol(tmp_path, max_energy=0.001)
        step = _step(observables_path=str(obs), policy_path=str(pol))
        result = handle_ns_check_barrier(step, _ctx(tmp_path))
        assert not result.ok
        assert result.refusal_type == "EnergyBarrierViolated"


# ── _load_pde_state error branches ─────────────────────────────────────────────

class TestLoadPdeStateErrors:
    """Force _load_pde_state errors via ns_evolve_linear (which calls it)."""

    def _write_state(self, tmp_path, data, filename="state.json"):
        p = tmp_path / filename
        p.write_text(json.dumps(data) if not isinstance(data, str) else data)
        return p

    def test_invalid_json(self, tmp_path):
        sp = tmp_path / "state.json"; sp.write_text("not json")
        step = _step(state_path=str(sp))
        with pytest.raises(ValueError, match="invalid json"):
            handle_ns_evolve_linear(step, _ctx(tmp_path))

    def test_not_dict(self, tmp_path):
        sp = self._write_state(tmp_path, [1, 2, 3])
        step = _step(state_path=str(sp))
        with pytest.raises(ValueError, match="must be an object"):
            handle_ns_evolve_linear(step, _ctx(tmp_path))

    def test_invalid_grid(self, tmp_path):
        sp = self._write_state(tmp_path, {"grid": {"nx": 0, "ny": 2}, "field": []})
        step = _step(state_path=str(sp))
        with pytest.raises(ValueError, match="grid dimensions"):
            handle_ns_evolve_linear(step, _ctx(tmp_path))

    def test_field_wrong_length(self, tmp_path):
        sp = self._write_state(tmp_path, {
            "grid": {"nx": 2, "ny": 2}, "field": [{"u": 0.0, "v": 0.0}]
        })
        step = _step(state_path=str(sp))
        with pytest.raises(ValueError, match="length nx"):
            handle_ns_evolve_linear(step, _ctx(tmp_path))

    def test_field_cell_not_dict(self, tmp_path):
        sp = self._write_state(tmp_path, {
            "grid": {"nx": 2, "ny": 1}, "field": [1.0, 2.0]
        })
        step = _step(state_path=str(sp))
        with pytest.raises(ValueError, match="cell must be an object"):
            handle_ns_evolve_linear(step, _ctx(tmp_path))
