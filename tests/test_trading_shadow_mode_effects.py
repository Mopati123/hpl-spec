import json
import tempfile
import unittest
from pathlib import Path

from hpl.runtime.context import RuntimeContext
from hpl.runtime.effects import EffectStep, get_handler


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "trading"


class TradingShadowModeEffectsTests(unittest.TestCase):
    def _run_shadow_pipeline(self, work_dir: Path, policy_name: str) -> bytes:
        ctx = RuntimeContext(trace_sink=work_dir)
        model_path = FIXTURES / "shadow_model.json"
        policy_path = FIXTURES / policy_name
        fixture_path = FIXTURES / "price_series_simple.json"

        steps = [
            EffectStep(
                step_id="load_model",
                effect_type="SIM_MARKET_MODEL_LOAD",
                args={
                    "model_path": str(model_path),
                    "out_path": "shadow_model.json",
                    "seed_out_path": "shadow_seed.json",
                },
            ),
            EffectStep(
                step_id="ingest_market",
                effect_type="INGEST_MARKET_FIXTURE",
                args={
                    "fixture_path": str(fixture_path),
                    "out_path": "market_snapshot.json",
                },
            ),
            EffectStep(
                step_id="regime_shift",
                effect_type="SIM_REGIME_SHIFT_STEP",
                args={
                    "market_snapshot_path": "market_snapshot.json",
                    "model_path": str(model_path),
                    "out_path": "regime_snapshot.json",
                },
            ),
            EffectStep(
                step_id="latency_apply",
                effect_type="SIM_LATENCY_APPLY",
                args={
                    "market_snapshot_path": "regime_snapshot.json",
                    "model_path": str(model_path),
                    "policy_path": str(policy_path),
                    "out_path": "latency_snapshot.json",
                },
            ),
            EffectStep(
                step_id="compute_signal",
                effect_type="COMPUTE_SIGNAL",
                args={
                    "market_snapshot_path": "latency_snapshot.json",
                    "policy_path": str(policy_path),
                    "out_path": "signal.json",
                },
            ),
            EffectStep(
                step_id="simulate_order",
                effect_type="SIMULATE_ORDER",
                args={
                    "market_snapshot_path": "latency_snapshot.json",
                    "signal_path": "signal.json",
                    "policy_path": str(policy_path),
                    "model_path": str(model_path),
                    "out_path": "trade_fill.json",
                },
            ),
            EffectStep(
                step_id="partial_fill",
                effect_type="SIM_PARTIAL_FILL_MODEL",
                args={
                    "trade_fill_path": "trade_fill.json",
                    "policy_path": str(policy_path),
                    "model_path": str(model_path),
                    "out_path": "shadow_fill.json",
                },
            ),
            EffectStep(
                step_id="update_risk",
                effect_type="UPDATE_RISK_ENVELOPE",
                args={
                    "trade_fill_path": "shadow_fill.json",
                    "policy_path": str(policy_path),
                    "out_path": "risk_envelope.json",
                },
            ),
            EffectStep(
                step_id="order_lifecycle",
                effect_type="SIM_ORDER_LIFECYCLE",
                args={
                    "shadow_fill_path": "shadow_fill.json",
                    "model_path": str(model_path),
                    "out_path": "shadow_execution_log.json",
                },
            ),
            EffectStep(
                step_id="trade_ledger",
                effect_type="SIM_EMIT_TRADE_LEDGER",
                args={
                    "shadow_fill_path": "shadow_fill.json",
                    "risk_envelope_path": "risk_envelope.json",
                    "signal_path": "signal.json",
                    "out_path": "shadow_trade_ledger.json",
                },
            ),
            EffectStep(
                step_id="trade_report",
                effect_type="EMIT_TRADE_REPORT",
                args={
                    "market_snapshot_path": "latency_snapshot.json",
                    "signal_path": "signal.json",
                    "trade_fill_path": "shadow_fill.json",
                    "risk_envelope_path": "risk_envelope.json",
                    "report_json_path": "trade_report.json",
                    "report_md_path": "trade_report.md",
                },
            ),
        ]

        for step in steps:
            handler = get_handler(step.effect_type)
            result = handler(step, ctx)
            self.assertTrue(result.ok, f"{step.effect_type} failed: {result.refusal_type}")

        return (work_dir / "trade_report.json").read_bytes()

    def test_shadow_pipeline_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp_dir_one:
            report_one = self._run_shadow_pipeline(Path(tmp_dir_one), "shadow_policy_safe.json")

        with tempfile.TemporaryDirectory() as tmp_dir_two:
            report_two = self._run_shadow_pipeline(Path(tmp_dir_two), "shadow_policy_safe.json")

        self.assertEqual(report_one, report_two)

    def test_shadow_latency_refusal(self):
        ctx = RuntimeContext(trace_sink=Path(tempfile.mkdtemp()))
        model_path = FIXTURES / "shadow_model.json"
        policy_path = FIXTURES / "shadow_policy_forbidden.json"
        fixture_path = FIXTURES / "price_series_simple.json"

        ingest = EffectStep(
            step_id="ingest",
            effect_type="INGEST_MARKET_FIXTURE",
            args={"fixture_path": str(fixture_path), "out_path": "market_snapshot.json"},
        )
        get_handler(ingest.effect_type)(ingest, ctx)

        regime = EffectStep(
            step_id="regime",
            effect_type="SIM_REGIME_SHIFT_STEP",
            args={
                "market_snapshot_path": "market_snapshot.json",
                "model_path": str(model_path),
                "out_path": "regime_snapshot.json",
            },
        )
        get_handler(regime.effect_type)(regime, ctx)

        latency = EffectStep(
            step_id="latency",
            effect_type="SIM_LATENCY_APPLY",
            args={
                "market_snapshot_path": "regime_snapshot.json",
                "model_path": str(model_path),
                "policy_path": str(policy_path),
                "out_path": "latency_snapshot.json",
            },
        )
        result = get_handler(latency.effect_type)(latency, ctx)
        self.assertFalse(result.ok)
        self.assertEqual(result.refusal_type, "StalenessViolation")

    def test_shadow_partial_fill_refusal(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            ctx = RuntimeContext(trace_sink=Path(tmp_dir))
            model_path = FIXTURES / "shadow_model.json"
            policy_path = FIXTURES / "shadow_policy_safe.json"
            fixture_path = FIXTURES / "price_series_simple.json"

            ingest = EffectStep(
                step_id="ingest",
                effect_type="INGEST_MARKET_FIXTURE",
                args={"fixture_path": str(fixture_path), "out_path": "market_snapshot.json"},
            )
            get_handler(ingest.effect_type)(ingest, ctx)

            signal_step = EffectStep(
                step_id="signal",
                effect_type="COMPUTE_SIGNAL",
                args={
                    "market_snapshot_path": "market_snapshot.json",
                    "policy_path": str(policy_path),
                    "out_path": "signal.json",
                },
            )
            get_handler(signal_step.effect_type)(signal_step, ctx)

            simulate = EffectStep(
                step_id="simulate",
                effect_type="SIMULATE_ORDER",
                args={
                    "market_snapshot_path": "market_snapshot.json",
                    "signal_path": "signal.json",
                    "policy_path": str(policy_path),
                    "model_path": str(model_path),
                    "out_path": "trade_fill.json",
                },
            )
            get_handler(simulate.effect_type)(simulate, ctx)

            partial = EffectStep(
                step_id="partial",
                effect_type="SIM_PARTIAL_FILL_MODEL",
                args={
                    "trade_fill_path": "trade_fill.json",
                    "policy_path": str(FIXTURES / "shadow_policy_forbidden.json"),
                    "model_path": str(model_path),
                    "out_path": "shadow_fill.json",
                },
            )
            result = get_handler(partial.effect_type)(partial, ctx)
            self.assertFalse(result.ok)
            self.assertEqual(result.refusal_type, "PartialFillTooLow")


if __name__ == "__main__":
    unittest.main()
