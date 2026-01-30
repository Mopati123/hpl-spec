import json
import tempfile
import unittest
from pathlib import Path

from src.hpl.runtime.context import RuntimeContext
from src.hpl.runtime.engine import RuntimeEngine
from src.hpl.runtime.contracts import ExecutionContract
from src.hpl.runtime.effects import EffectType, EffectStep, get_handler
from src.hpl.execution_token import ExecutionToken
from src.hpl.audit.constraint_inversion import invert_constraints


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "trading"


class TradingPaperModeEffectsTests(unittest.TestCase):
    def _run_effects(self, work_dir: Path, policy_name: str) -> Path:
        ctx = RuntimeContext(trace_sink=work_dir)
        fixture_path = FIXTURES / "price_series_simple.json"
        policy_path = FIXTURES / policy_name

        ingest = EffectStep(
            step_id="ingest_market",
            effect_type=EffectType.INGEST_MARKET_FIXTURE,
            args={
                "fixture_path": str(fixture_path),
                "out_path": "market_snapshot.json",
            },
        )
        signal = EffectStep(
            step_id="compute_signal",
            effect_type=EffectType.COMPUTE_SIGNAL,
            args={
                "market_snapshot_path": "market_snapshot.json",
                "policy_path": str(policy_path),
                "out_path": "signal.json",
            },
        )
        simulate = EffectStep(
            step_id="simulate_order",
            effect_type=EffectType.SIMULATE_ORDER,
            args={
                "market_snapshot_path": "market_snapshot.json",
                "signal_path": "signal.json",
                "policy_path": str(policy_path),
                "out_path": "trade_fill.json",
            },
        )
        update = EffectStep(
            step_id="update_risk",
            effect_type=EffectType.UPDATE_RISK_ENVELOPE,
            args={
                "trade_fill_path": "trade_fill.json",
                "policy_path": str(policy_path),
                "out_path": "risk_envelope.json",
            },
        )
        report = EffectStep(
            step_id="emit_report",
            effect_type=EffectType.EMIT_TRADE_REPORT,
            args={
                "market_snapshot_path": "market_snapshot.json",
                "signal_path": "signal.json",
                "trade_fill_path": "trade_fill.json",
                "risk_envelope_path": "risk_envelope.json",
                "report_json_path": "trade_report.json",
                "report_md_path": "trade_report.md",
            },
        )

        for step in [ingest, signal, simulate, update, report]:
            handler = get_handler(step.effect_type)
            result = handler(step, ctx)
            if not result.ok:
                return Path("refused")
        return work_dir / "trade_report.json"

    def test_trading_effects_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp_one:
            report_one = self._run_effects(Path(tmp_one), "policy_safe.json")
            content_one = report_one.read_bytes()

        with tempfile.TemporaryDirectory() as tmp_two:
            report_two = self._run_effects(Path(tmp_two), "policy_safe.json")
            content_two = report_two.read_bytes()

        self.assertEqual(content_one, content_two)

    def test_trading_refusal_and_inversion(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            work_dir = Path(tmp_dir)
            ctx = RuntimeContext(trace_sink=work_dir)
            fixture_path = FIXTURES / "price_series_simple.json"
            policy_path = FIXTURES / "policy_forbidden.json"

            steps = [
                {
                    "step_id": "ingest_market",
                    "effect_type": EffectType.INGEST_MARKET_FIXTURE,
                    "args": {"fixture_path": str(fixture_path), "out_path": "market_snapshot.json"},
                },
                {
                    "step_id": "compute_signal",
                    "effect_type": EffectType.COMPUTE_SIGNAL,
                    "args": {
                        "market_snapshot_path": "market_snapshot.json",
                        "policy_path": str(policy_path),
                        "out_path": "signal.json",
                    },
                },
                {
                    "step_id": "simulate_order",
                    "effect_type": EffectType.SIMULATE_ORDER,
                    "args": {
                        "market_snapshot_path": "market_snapshot.json",
                        "signal_path": "signal.json",
                        "policy_path": str(policy_path),
                        "out_path": "trade_fill.json",
                    },
                },
                {
                    "step_id": "update_risk",
                    "effect_type": EffectType.UPDATE_RISK_ENVELOPE,
                    "args": {
                        "trade_fill_path": "trade_fill.json",
                        "policy_path": str(policy_path),
                        "out_path": "risk_envelope.json",
                    },
                },
            ]
            token = ExecutionToken.build(
                allowed_backends=["CLASSICAL"],
                budget_steps=10,
                determinism_mode="deterministic",
            )
            plan = {
                "plan_id": "trade_plan",
                "program_id": "trade",
                "status": "planned",
                "steps": steps,
                "reasons": [],
                "verification": None,
                "witness_records": [],
                "execution_token": token.to_dict(),
            }
            contract = ExecutionContract(allowed_steps={step["step_id"] for step in steps})
            result = RuntimeEngine().run(plan, ctx, contract)
            self.assertEqual(result.status, "denied")
            self.assertTrue(result.constraint_witnesses)
            witness = result.constraint_witnesses[0]
            proposal = invert_constraints(witness)
            proposal_two = invert_constraints(witness)
            self.assertEqual(
                json.dumps(proposal, sort_keys=True),
                json.dumps(proposal_two, sort_keys=True),
            )

    def test_budget_exhaustion(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            ctx = RuntimeContext(trace_sink=Path(tmp_dir))
            steps = [
                {
                    "step_id": "step_one",
                    "effect_type": EffectType.NOOP,
                    "args": {},
                },
                {
                    "step_id": "step_two",
                    "effect_type": EffectType.NOOP,
                    "args": {},
                },
            ]
            token = ExecutionToken.build(
                allowed_backends=["CLASSICAL"],
                budget_steps=1,
                determinism_mode="deterministic",
            )
            plan = {
                "plan_id": "budget_plan",
                "program_id": "budget",
                "status": "planned",
                "steps": steps,
                "reasons": [],
                "verification": None,
                "witness_records": [],
                "execution_token": token.to_dict(),
            }
            contract = ExecutionContract(allowed_steps={step["step_id"] for step in steps})
            result = RuntimeEngine().run(plan, ctx, contract)
            self.assertEqual(result.status, "denied")
            self.assertIn("budget_steps_exceeded", result.reasons)
            self.assertTrue(result.constraint_witnesses)


if __name__ == "__main__":
    unittest.main()