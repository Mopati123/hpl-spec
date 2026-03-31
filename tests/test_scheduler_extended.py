"""Extended tests for hpl.scheduler — covers large missed blocks."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from hpl import scheduler
from hpl.scheduler import (
    ExecutionPlan,
    SchedulerContext,
    _build_steps,
    _build_effect_steps,
    plan,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_ir(program_id: str = "test_program") -> dict:
    return {
        "program_id": program_id,
        "hamiltonian": {
            "terms": [
                {"operator_id": "SURF_A", "cls": "C", "coefficient": 1.0},
                {"operator_id": "SURF_B", "cls": "C", "coefficient": 2.0},
            ]
        },
        "operators": {
            "SURF_A": {"type": "unspecified", "commutes_with": [], "backend_map": []},
            "SURF_B": {"type": "unspecified", "commutes_with": [], "backend_map": []},
        },
        "invariants": [],
        "scheduler": {"collapse_policy": "unspecified", "authorized_observers": []},
    }


def _empty_ir() -> dict:
    return {
        "program_id": "empty",
        "hamiltonian": {"terms": []},
        "operators": {},
        "invariants": [],
        "scheduler": {"collapse_policy": "unspecified", "authorized_observers": []},
    }


# ---------------------------------------------------------------------------
# _build_steps — lines 192-209
# ---------------------------------------------------------------------------

class BuildStepsTests(unittest.TestCase):
    def test_returns_steps_for_valid_terms(self):
        ir = _minimal_ir()
        steps = _build_steps(ir)
        self.assertEqual(len(steps), 2)
        self.assertEqual(steps[0]["operator_id"], "SURF_A")
        self.assertEqual(steps[1]["operator_id"], "SURF_B")

    def test_skips_non_dict_terms(self):
        ir = _minimal_ir()
        ir["hamiltonian"]["terms"] = ["not_a_dict", {"operator_id": "X", "cls": "C", "coefficient": 1.0}]
        steps = _build_steps(ir)
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0]["operator_id"], "X")

    def test_non_list_terms_returns_empty(self):
        ir = _minimal_ir()
        ir["hamiltonian"]["terms"] = "not_a_list"
        steps = _build_steps(ir)
        self.assertEqual(steps, [])

    def test_missing_hamiltonian_returns_empty(self):
        steps = _build_steps({"program_id": "x"})
        self.assertEqual(steps, [])

    def test_empty_terms_returns_empty(self):
        steps = _build_steps(_empty_ir())
        self.assertEqual(steps, [])

    def test_step_fields(self):
        ir = _minimal_ir()
        steps = _build_steps(ir)
        step = steps[0]
        self.assertIn("index", step)
        self.assertIn("operator_id", step)
        self.assertIn("cls", step)
        self.assertIn("coefficient", step)


# ---------------------------------------------------------------------------
# plan() — basic status paths (lines 155, 261)
# ---------------------------------------------------------------------------

class PlanStatusTests(unittest.TestCase):
    def test_plan_status_planned_when_no_errors(self):
        p = plan(_minimal_ir(), SchedulerContext())
        self.assertEqual(p.status, "planned")
        self.assertEqual(p.reasons, [])

    def test_plan_status_denied_when_registry_errors(self):
        """Operator registry enforcement with missing operators triggers denied."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            # Create a registry file that has OP_OTHER but not SURF_A/SURF_B
            reg_file = tmp_path / "registry.json"
            reg_file.write_text(
                json.dumps({
                    "sub_hamiltonian": "test_H",
                    "version": "0.1.0",
                    "operators": [
                        {"id": "OP_OTHER", "class": "C", "impl_ref": "hpl.test.op"}
                    ],
                }),
                encoding="utf-8",
            )
            ctx = SchedulerContext(
                operator_registry_enforced=True,
                operator_registry_paths=[reg_file],
                root=tmp_path,
            )
            p = plan(_minimal_ir(), ctx)
        self.assertEqual(p.status, "denied")
        self.assertTrue(any("SURF_A" in r or "SURF_B" in r or "registry" in r for r in p.reasons))

    def test_plan_to_dict_structure(self):
        p = plan(_minimal_ir(), SchedulerContext())
        d = p.to_dict()
        for key in ("plan_id", "program_id", "status", "steps", "reasons",
                    "verification", "witness_records", "execution_token",
                    "operator_registry_enforced", "operator_registry_paths"):
            self.assertIn(key, d)

    def test_execution_token_present(self):
        p = plan(_minimal_ir(), SchedulerContext())
        self.assertIsNotNone(p.execution_token)
        self.assertIn("token_id", p.execution_token)

    def test_witness_records_has_scheduler_plan(self):
        p = plan(_minimal_ir(), SchedulerContext())
        stages = [r.get("stage") for r in p.witness_records]
        self.assertIn("scheduler_plan", stages)


# ---------------------------------------------------------------------------
# _build_effect_steps — emit_effect_steps=True  (lines 222-307)
# ---------------------------------------------------------------------------

class BuildEffectStepsTests(unittest.TestCase):
    def _ctx(self, **kwargs) -> SchedulerContext:
        return SchedulerContext(emit_effect_steps=True, **kwargs)

    def test_default_effect_steps_include_lower_backend_ir(self):
        ctx = self._ctx()
        steps = _build_effect_steps(_minimal_ir(), ctx)
        types = [s["effect_type"] for s in steps]
        self.assertIn("LOWER_BACKEND_IR", types)

    def test_qasm_backend_adds_lower_qasm_step(self):
        ctx = self._ctx(backend_target="QASM")
        steps = _build_effect_steps(_minimal_ir(), ctx)
        types = [s["effect_type"] for s in steps]
        self.assertIn("LOWER_QASM", types)

    def test_classical_backend_no_qasm_step(self):
        ctx = self._ctx(backend_target="classical")
        steps = _build_effect_steps(_minimal_ir(), ctx)
        types = [s["effect_type"] for s in steps]
        self.assertNotIn("LOWER_QASM", types)

    def test_ecmo_input_path_adds_select_measurement_track(self):
        with tempfile.TemporaryDirectory() as tmp:
            ecmo_path = Path(tmp) / "ecmo.json"
            ecmo_path.write_text("{}", encoding="utf-8")
            ctx = self._ctx(ecmo_input_path=ecmo_path)
            steps = _build_effect_steps(_minimal_ir(), ctx)
        types = [s["effect_type"] for s in steps]
        self.assertIn("SELECT_MEASUREMENT_TRACK", types)

    def test_ecmo_path_with_measurement_selection_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            ecmo_path = Path(tmp) / "ecmo.json"
            ecmo_path.write_text("{}", encoding="utf-8")
            sel_path = Path(tmp) / "selection.json"
            ctx = self._ctx(ecmo_input_path=ecmo_path, measurement_selection_path=sel_path)
            steps = _build_effect_steps(_minimal_ir(), ctx)
        sel_step = next(s for s in steps if s["effect_type"] == "SELECT_MEASUREMENT_TRACK")
        self.assertIn("out_path", sel_step["args"])

    def test_require_epoch_with_anchor_adds_verify_epoch_step(self):
        with tempfile.TemporaryDirectory() as tmp:
            anchor_path = Path(tmp) / "anchor.json"
            anchor_path.write_text("{}", encoding="utf-8")
            ctx = self._ctx(
                require_epoch_verification=True,
                anchor_path=anchor_path,
            )
            steps = _build_effect_steps(_minimal_ir(), ctx)
        types = [s["effect_type"] for s in steps]
        self.assertIn("VERIFY_EPOCH", types)

    def test_require_epoch_with_anchor_and_signature_adds_verify_signature_step(self):
        with tempfile.TemporaryDirectory() as tmp:
            anchor_path = Path(tmp) / "anchor.json"
            anchor_path.write_text("{}", encoding="utf-8")
            sig_path = Path(tmp) / "anchor.sig"
            sig_path.write_text("aabbcc", encoding="utf-8")
            ctx = self._ctx(
                require_epoch_verification=True,
                anchor_path=anchor_path,
                signature_path=sig_path,
            )
            steps = _build_effect_steps(_minimal_ir(), ctx)
        types = [s["effect_type"] for s in steps]
        self.assertIn("VERIFY_SIGNATURE", types)

    def test_artifact_backend_ir_path_in_args(self):
        ctx = self._ctx(artifact_paths={"backend_ir": "/tmp/backend.json"})
        steps = _build_effect_steps(_minimal_ir(), ctx)
        lower_step = next(s for s in steps if s["effect_type"] == "LOWER_BACKEND_IR")
        self.assertIn("out_path", lower_step["args"])


# ---------------------------------------------------------------------------
# Track: ci_governance (lines 311-389)
# ---------------------------------------------------------------------------

class CiGovernanceStepsTests(unittest.TestCase):
    def _ctx(self, **kwargs) -> SchedulerContext:
        return SchedulerContext(emit_effect_steps=True, track="ci_governance", **kwargs)

    def test_ci_governance_has_validate_registries(self):
        ctx = self._ctx()
        steps = _build_effect_steps(_minimal_ir(), ctx)
        types = [s["effect_type"] for s in steps]
        self.assertIn("VALIDATE_REGISTRIES", types)

    def test_ci_governance_with_repo_state_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            state_path.write_text("{}", encoding="utf-8")
            ctx = self._ctx(ci_repo_state_path=state_path)
            steps = _build_effect_steps(_minimal_ir(), ctx)
        types = [s["effect_type"] for s in steps]
        self.assertIn("CHECK_REPO_STATE", types)

    def test_ci_governance_with_coupling_registry(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg_path = Path(tmp) / "coupling.json"
            reg_path.write_text("{}", encoding="utf-8")
            ctx = self._ctx(ci_coupling_registry_path=reg_path)
            steps = _build_effect_steps(_minimal_ir(), ctx)
        types = [s["effect_type"] for s in steps]
        self.assertIn("VALIDATE_COUPLING_TOPOLOGY", types)

    def test_ci_governance_epoch_and_signature(self):
        with tempfile.TemporaryDirectory() as tmp:
            anchor_path = Path(tmp) / "anchor.json"
            anchor_path.write_text("{}", encoding="utf-8")
            sig_path = Path(tmp) / "anchor.sig"
            sig_path.write_text("aabbcc", encoding="utf-8")
            ctx = self._ctx(
                require_epoch_verification=True,
                anchor_path=anchor_path,
                signature_path=sig_path,
            )
            steps = _build_effect_steps(_minimal_ir(), ctx)
        types = [s["effect_type"] for s in steps]
        self.assertIn("VERIFY_EPOCH", types)
        self.assertIn("VERIFY_SIGNATURE", types)

    def test_ci_governance_backend_ir_step_present(self):
        ctx = self._ctx()
        steps = _build_effect_steps(_minimal_ir(), ctx)
        types = [s["effect_type"] for s in steps]
        self.assertIn("LOWER_BACKEND_IR", types)

    def test_ci_governance_artifact_backend_ir_path(self):
        ctx = self._ctx(artifact_paths={"backend_ir": "/tmp/out.json"})
        steps = _build_effect_steps(_minimal_ir(), ctx)
        lower = next(s for s in steps if s["effect_type"] == "LOWER_BACKEND_IR")
        self.assertIn("out_path", lower["args"])


# ---------------------------------------------------------------------------
# Track: agent_governance (lines 392-443)
# ---------------------------------------------------------------------------

class AgentGovernanceStepsTests(unittest.TestCase):
    def _ctx(self, **kwargs) -> SchedulerContext:
        return SchedulerContext(emit_effect_steps=True, track="agent_governance", **kwargs)

    def test_agent_governance_has_evaluate_agent_proposal(self):
        ctx = self._ctx()
        steps = _build_effect_steps(_minimal_ir(), ctx)
        types = [s["effect_type"] for s in steps]
        self.assertIn("EVALUATE_AGENT_PROPOSAL", types)

    def test_agent_governance_with_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            proposal = Path(tmp) / "proposal.json"
            proposal.write_text("{}", encoding="utf-8")
            policy = Path(tmp) / "policy.json"
            policy.write_text("{}", encoding="utf-8")
            decision = Path(tmp) / "decision.json"
            ctx = self._ctx(
                agent_proposal_path=proposal,
                agent_policy_path=policy,
                agent_decision_path=decision,
            )
            steps = _build_effect_steps(_minimal_ir(), ctx)
        eval_step = next(s for s in steps if s["effect_type"] == "EVALUATE_AGENT_PROPOSAL")
        self.assertIn("proposal_path", eval_step["args"])
        self.assertIn("policy_path", eval_step["args"])
        self.assertIn("decision_path", eval_step["args"])

    def test_agent_governance_epoch_and_signature(self):
        with tempfile.TemporaryDirectory() as tmp:
            anchor_path = Path(tmp) / "anchor.json"
            anchor_path.write_text("{}", encoding="utf-8")
            sig_path = Path(tmp) / "anchor.sig"
            sig_path.write_text("aabbcc", encoding="utf-8")
            ctx = self._ctx(
                require_epoch_verification=True,
                anchor_path=anchor_path,
                signature_path=sig_path,
            )
            steps = _build_effect_steps(_minimal_ir(), ctx)
        types = [s["effect_type"] for s in steps]
        self.assertIn("VERIFY_EPOCH", types)
        self.assertIn("VERIFY_SIGNATURE", types)


# ---------------------------------------------------------------------------
# Track: trading_paper_mode (lines 446-547)
# ---------------------------------------------------------------------------

class TradingPaperStepsTests(unittest.TestCase):
    def _ctx(self, **kwargs) -> SchedulerContext:
        return SchedulerContext(emit_effect_steps=True, track="trading_paper_mode", **kwargs)

    def test_trading_paper_has_core_steps(self):
        ctx = self._ctx()
        steps = _build_effect_steps(_minimal_ir(), ctx)
        types = [s["effect_type"] for s in steps]
        for expected in ("INGEST_MARKET_FIXTURE", "COMPUTE_SIGNAL", "SIMULATE_ORDER",
                         "UPDATE_RISK_ENVELOPE", "EMIT_TRADE_REPORT"):
            self.assertIn(expected, types, f"Missing step: {expected}")

    def test_trading_paper_report_defaults(self):
        ctx = self._ctx()
        steps = _build_effect_steps(_minimal_ir(), ctx)
        report_step = next(s for s in steps if s["effect_type"] == "EMIT_TRADE_REPORT")
        self.assertEqual(report_step["args"]["report_json_path"], "trade_report.json")
        self.assertEqual(report_step["args"]["report_md_path"], "trade_report.md")

    def test_trading_paper_custom_report_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            rj = Path(tmp) / "custom_report.json"
            rm = Path(tmp) / "custom_report.md"
            ctx = self._ctx(
                trading_report_json_path=rj,
                trading_report_md_path=rm,
            )
            steps = _build_effect_steps(_minimal_ir(), ctx)
        report_step = next(s for s in steps if s["effect_type"] == "EMIT_TRADE_REPORT")
        self.assertIn("custom_report.json", report_step["args"]["report_json_path"])

    def test_trading_paper_epoch_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            anchor_path = Path(tmp) / "anchor.json"
            anchor_path.write_text("{}", encoding="utf-8")
            sig_path = Path(tmp) / "anchor.sig"
            sig_path.write_text("aabbcc", encoding="utf-8")
            ctx = self._ctx(
                require_epoch_verification=True,
                anchor_path=anchor_path,
                signature_path=sig_path,
            )
            steps = _build_effect_steps(_minimal_ir(), ctx)
        types = [s["effect_type"] for s in steps]
        self.assertIn("VERIFY_EPOCH", types)
        self.assertIn("VERIFY_SIGNATURE", types)


# ---------------------------------------------------------------------------
# Track: trading_shadow_mode (lines 550-728)
# ---------------------------------------------------------------------------

class TradingShadowStepsTests(unittest.TestCase):
    def _ctx(self, **kwargs) -> SchedulerContext:
        return SchedulerContext(emit_effect_steps=True, track="trading_shadow_mode", **kwargs)

    def test_trading_shadow_has_core_steps(self):
        ctx = self._ctx()
        steps = _build_effect_steps(_minimal_ir(), ctx)
        types = [s["effect_type"] for s in steps]
        for expected in (
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
        ):
            self.assertIn(expected, types, f"Missing step: {expected}")

    def test_trading_shadow_epoch_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            anchor_path = Path(tmp) / "anchor.json"
            anchor_path.write_text("{}", encoding="utf-8")
            sig_path = Path(tmp) / "anchor.sig"
            sig_path.write_text("aabbcc", encoding="utf-8")
            ctx = self._ctx(
                require_epoch_verification=True,
                anchor_path=anchor_path,
                signature_path=sig_path,
            )
            steps = _build_effect_steps(_minimal_ir(), ctx)
        types = [s["effect_type"] for s in steps]
        self.assertIn("VERIFY_EPOCH", types)
        self.assertIn("VERIFY_SIGNATURE", types)

    def test_trading_shadow_custom_report_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            rj = Path(tmp) / "shadow_report.json"
            rm = Path(tmp) / "shadow_report.md"
            ctx = self._ctx(
                trading_report_json_path=rj,
                trading_report_md_path=rm,
            )
            steps = _build_effect_steps(_minimal_ir(), ctx)
        report_step = next(s for s in steps if s["effect_type"] == "EMIT_TRADE_REPORT")
        self.assertIn("shadow_report.json", report_step["args"]["report_json_path"])


# ---------------------------------------------------------------------------
# Track: trading_io_shadow (lines 731-819)
# ---------------------------------------------------------------------------

class TradingIoShadowStepsTests(unittest.TestCase):
    def _ctx(self, **kwargs) -> SchedulerContext:
        return SchedulerContext(emit_effect_steps=True, track="trading_io_shadow", **kwargs)

    def test_io_shadow_has_io_steps(self):
        ctx = self._ctx()
        steps = _build_effect_steps(_minimal_ir(), ctx)
        types = [s["effect_type"] for s in steps]
        for expected in ("IO_CONNECT", "IO_QUERY_FILLS", "IO_RECONCILE"):
            self.assertIn(expected, types, f"Missing step: {expected}")

    def test_io_shadow_default_endpoint(self):
        ctx = self._ctx()
        steps = _build_effect_steps(_minimal_ir(), ctx)
        connect_step = next(s for s in steps if s["effect_type"] == "IO_CONNECT")
        self.assertEqual(connect_step["args"]["endpoint"], "broker://demo")

    def test_io_shadow_custom_endpoint(self):
        ctx = self._ctx(io_endpoint="broker://real")
        steps = _build_effect_steps(_minimal_ir(), ctx)
        connect_step = next(s for s in steps if s["effect_type"] == "IO_CONNECT")
        self.assertEqual(connect_step["args"]["endpoint"], "broker://real")

    def test_io_shadow_epoch_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            anchor_path = Path(tmp) / "anchor.json"
            anchor_path.write_text("{}", encoding="utf-8")
            sig_path = Path(tmp) / "anchor.sig"
            sig_path.write_text("aabbcc", encoding="utf-8")
            ctx = self._ctx(
                require_epoch_verification=True,
                anchor_path=anchor_path,
                signature_path=sig_path,
            )
            steps = _build_effect_steps(_minimal_ir(), ctx)
        types = [s["effect_type"] for s in steps]
        self.assertIn("VERIFY_EPOCH", types)
        self.assertIn("VERIFY_SIGNATURE", types)


# ---------------------------------------------------------------------------
# Track: trading_io_live_min (lines 822-914)
# ---------------------------------------------------------------------------

class TradingIoLiveMinStepsTests(unittest.TestCase):
    def _ctx(self, **kwargs) -> SchedulerContext:
        return SchedulerContext(emit_effect_steps=True, track="trading_io_live_min", **kwargs)

    def test_io_live_min_has_submit_and_reconcile(self):
        ctx = self._ctx()
        steps = _build_effect_steps(_minimal_ir(), ctx)
        types = [s["effect_type"] for s in steps]
        for expected in ("IO_CONNECT", "IO_SUBMIT_ORDER", "IO_RECONCILE"):
            self.assertIn(expected, types, f"Missing step: {expected}")

    def test_io_live_min_default_order(self):
        ctx = self._ctx()
        steps = _build_effect_steps(_minimal_ir(), ctx)
        submit_step = next(s for s in steps if s["effect_type"] == "IO_SUBMIT_ORDER")
        order = submit_step["args"]["order"]
        self.assertEqual(order["order_id"], "live-min-order")

    def test_io_live_min_custom_order(self):
        custom_order = {"order_id": "custom-order", "symbol": "BTC", "side": "sell", "qty": 5}
        ctx = self._ctx(io_order=custom_order)
        steps = _build_effect_steps(_minimal_ir(), ctx)
        submit_step = next(s for s in steps if s["effect_type"] == "IO_SUBMIT_ORDER")
        self.assertEqual(submit_step["args"]["order"]["order_id"], "custom-order")

    def test_io_live_min_epoch_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            anchor_path = Path(tmp) / "anchor.json"
            anchor_path.write_text("{}", encoding="utf-8")
            sig_path = Path(tmp) / "anchor.sig"
            sig_path.write_text("aabbcc", encoding="utf-8")
            ctx = self._ctx(
                require_epoch_verification=True,
                anchor_path=anchor_path,
                signature_path=sig_path,
            )
            steps = _build_effect_steps(_minimal_ir(), ctx)
        types = [s["effect_type"] for s in steps]
        self.assertIn("VERIFY_EPOCH", types)
        self.assertIn("VERIFY_SIGNATURE", types)


# ---------------------------------------------------------------------------
# Track: net_shadow (lines 917-969)
# ---------------------------------------------------------------------------

class NetShadowStepsTests(unittest.TestCase):
    def _ctx(self, **kwargs) -> SchedulerContext:
        return SchedulerContext(emit_effect_steps=True, track="net_shadow", **kwargs)

    def test_net_shadow_has_all_net_steps(self):
        ctx = self._ctx()
        steps = _build_effect_steps(_minimal_ir(), ctx)
        types = [s["effect_type"] for s in steps]
        for expected in ("NET_CONNECT", "NET_HANDSHAKE", "NET_KEY_EXCHANGE",
                         "NET_SEND", "NET_RECV", "NET_CLOSE"):
            self.assertIn(expected, types, f"Missing step: {expected}")

    def test_net_shadow_default_endpoint(self):
        ctx = self._ctx()
        steps = _build_effect_steps(_minimal_ir(), ctx)
        connect_step = next(s for s in steps if s["effect_type"] == "NET_CONNECT")
        self.assertEqual(connect_step["args"]["endpoint"], "net://demo")

    def test_net_shadow_custom_endpoint(self):
        ctx = self._ctx(net_endpoint="net://prod")
        steps = _build_effect_steps(_minimal_ir(), ctx)
        connect_step = next(s for s in steps if s["effect_type"] == "NET_CONNECT")
        self.assertEqual(connect_step["args"]["endpoint"], "net://prod")

    def test_net_shadow_custom_message(self):
        ctx = self._ctx(net_message={"kind": "data", "payload": "test"})
        steps = _build_effect_steps(_minimal_ir(), ctx)
        send_step = next(s for s in steps if s["effect_type"] == "NET_SEND")
        self.assertEqual(send_step["args"]["payload"]["kind"], "data")


# ---------------------------------------------------------------------------
# Track: navier_stokes (lines 972-1080)
# ---------------------------------------------------------------------------

class NavierStokesStepsTests(unittest.TestCase):
    def _ctx(self, **kwargs) -> SchedulerContext:
        return SchedulerContext(emit_effect_steps=True, track="navier_stokes", **kwargs)

    def test_navier_stokes_has_core_steps(self):
        ctx = self._ctx()
        steps = _build_effect_steps(_minimal_ir(), ctx)
        types = [s["effect_type"] for s in steps]
        for expected in (
            "NS_EVOLVE_LINEAR",
            "NS_APPLY_DUHAMEL",
            "NS_PROJECT_LERAY",
            "NS_PRESSURE_RECOVER",
            "NS_MEASURE_OBSERVABLES",
            "NS_CHECK_BARRIER",
            "NS_EMIT_STATE",
        ):
            self.assertIn(expected, types, f"Missing step: {expected}")

    def test_navier_stokes_default_output_paths(self):
        ctx = self._ctx()
        steps = _build_effect_steps(_minimal_ir(), ctx)
        emit_step = next(s for s in steps if s["effect_type"] == "NS_EMIT_STATE")
        self.assertEqual(emit_step["args"]["out_path"], "ns_state_final.json")

    def test_navier_stokes_custom_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "ns_state.json"
            state_path.write_text("{}", encoding="utf-8")
            policy_path = Path(tmp) / "ns_policy.json"
            policy_path.write_text("{}", encoding="utf-8")
            final_path = Path(tmp) / "ns_final.json"
            obs_path = Path(tmp) / "ns_obs.json"
            pressure_path = Path(tmp) / "ns_pressure.json"
            gate_path = Path(tmp) / "ns_gate.json"
            ctx = self._ctx(
                ns_state_path=state_path,
                ns_policy_path=policy_path,
                ns_state_final_path=final_path,
                ns_observables_path=obs_path,
                ns_pressure_path=pressure_path,
                ns_gate_certificate_path=gate_path,
            )
            steps = _build_effect_steps(_minimal_ir(), ctx)
        emit_step = next(s for s in steps if s["effect_type"] == "NS_EMIT_STATE")
        self.assertIn("ns_final.json", emit_step["args"]["out_path"])

    def test_navier_stokes_epoch_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            anchor_path = Path(tmp) / "anchor.json"
            anchor_path.write_text("{}", encoding="utf-8")
            sig_path = Path(tmp) / "anchor.sig"
            sig_path.write_text("aabbcc", encoding="utf-8")
            ctx = self._ctx(
                require_epoch_verification=True,
                anchor_path=anchor_path,
                signature_path=sig_path,
            )
            steps = _build_effect_steps(_minimal_ir(), ctx)
        types = [s["effect_type"] for s in steps]
        self.assertIn("VERIFY_EPOCH", types)
        self.assertIn("VERIFY_SIGNATURE", types)


# ---------------------------------------------------------------------------
# plan() with emit_effect_steps=True
# ---------------------------------------------------------------------------

class PlanWithEffectStepsTests(unittest.TestCase):
    def test_plan_emit_effect_steps_ci_governance(self):
        ctx = SchedulerContext(emit_effect_steps=True, track="ci_governance")
        p = plan(_minimal_ir(), ctx)
        self.assertEqual(p.status, "planned")
        types = [s["effect_type"] for s in p.steps]
        self.assertIn("VALIDATE_REGISTRIES", types)

    def test_plan_emit_effect_steps_net_shadow(self):
        ctx = SchedulerContext(emit_effect_steps=True, track="net_shadow")
        p = plan(_minimal_ir(), ctx)
        self.assertEqual(p.status, "planned")
        types = [s["effect_type"] for s in p.steps]
        self.assertIn("NET_CONNECT", types)


# ---------------------------------------------------------------------------
# Operator registry enforcement paths (lines 122-132)
# ---------------------------------------------------------------------------

class OperatorRegistryEnforcementTests(unittest.TestCase):
    def test_registry_enforced_no_sources_denied(self):
        """load_operator_registries with no files → registry error → denied."""
        with tempfile.TemporaryDirectory() as tmp:
            ctx = SchedulerContext(
                operator_registry_enforced=True,
                operator_registry_paths=[],
                root=Path(tmp),  # empty dir, no registries
            )
            p = plan(_minimal_ir(), ctx)
        self.assertEqual(p.status, "denied")
        self.assertTrue(p.reasons)

    def test_registry_enforced_valid_registry_planned(self):
        """Registry has matching operators → plan is planned."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            reg_file = tmp_path / "registry.json"
            reg_file.write_text(
                json.dumps({
                    "sub_hamiltonian": "test_H",
                    "version": "0.1.0",
                    "operators": [
                        {"id": "SURF_A", "class": "C", "impl_ref": "hpl.test.a"},
                        {"id": "SURF_B", "class": "C", "impl_ref": "hpl.test.b"},
                    ],
                }),
                encoding="utf-8",
            )
            ctx = SchedulerContext(
                operator_registry_enforced=True,
                operator_registry_paths=[reg_file],
                root=tmp_path,
            )
            p = plan(_minimal_ir(), ctx)
        self.assertEqual(p.status, "planned")
        self.assertEqual(p.operator_registry_enforced, True)
        self.assertTrue(len(p.operator_registry_paths) > 0)

    def test_registry_not_enforced_always_planned(self):
        ctx = SchedulerContext(operator_registry_enforced=False)
        p = plan(_minimal_ir(), ctx)
        self.assertEqual(p.status, "planned")


# ---------------------------------------------------------------------------
# epoch verification edge cases (lines 1083-1130)
# ---------------------------------------------------------------------------

class EpochVerificationEdgeCasesTests(unittest.TestCase):
    def test_epoch_verification_no_anchor_denied(self):
        ctx = SchedulerContext(require_epoch_verification=True, anchor_path=None)
        p = plan(_minimal_ir(), ctx)
        self.assertEqual(p.status, "denied")
        self.assertTrue(any("anchor" in r for r in p.reasons))

    def test_epoch_verification_missing_anchor_file_denied(self):
        ctx = SchedulerContext(
            require_epoch_verification=True,
            anchor_path=Path("/nonexistent/anchor.json"),
        )
        p = plan(_minimal_ir(), ctx)
        self.assertEqual(p.status, "denied")
        self.assertTrue(any("anchor" in r for r in p.reasons))

    def test_epoch_verification_witness_record_added(self):
        ctx = SchedulerContext(require_epoch_verification=True)
        p = plan(_minimal_ir(), ctx)
        stages = [r.get("stage") for r in p.witness_records]
        self.assertIn("epoch_verification", stages)


# ---------------------------------------------------------------------------
# ExecutionPlan.to_dict()
# ---------------------------------------------------------------------------

class ExecutionPlanToDictTests(unittest.TestCase):
    def test_to_dict_round_trip(self):
        p = plan(_minimal_ir(), SchedulerContext())
        d = p.to_dict()
        self.assertIsInstance(d["steps"], list)
        self.assertIsInstance(d["reasons"], list)
        self.assertIsInstance(d["witness_records"], list)
        self.assertIsInstance(d["operator_registry_paths"], list)

    def test_to_dict_with_registry_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            reg_file = tmp_path / "registry.json"
            reg_file.write_text(
                json.dumps({
                    "sub_hamiltonian": "test_H",
                    "version": "0.1.0",
                    "operators": [
                        {"id": "SURF_A", "class": "C", "impl_ref": "hpl.test.a"},
                        {"id": "SURF_B", "class": "C", "impl_ref": "hpl.test.b"},
                    ],
                }),
                encoding="utf-8",
            )
            ctx = SchedulerContext(
                operator_registry_enforced=True,
                operator_registry_paths=[reg_file],
                root=tmp_path,
            )
            p = plan(_minimal_ir(), ctx)
        d = p.to_dict()
        self.assertIsInstance(d["operator_registry_paths"], list)


if __name__ == "__main__":
    unittest.main()
