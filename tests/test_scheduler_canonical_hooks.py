import unittest
from pathlib import Path

from hpl import scheduler


class SchedulerCanonicalHooksTests(unittest.TestCase):
    def test_trading_shadow_plan_contains_canonical_hooks(self):
        program_ir = {
            "program_id": "test_program",
            "hamiltonian": {"terms": []},
            "operators": {},
            "invariants": [],
            "scheduler": {"collapse_policy": "unspecified", "authorized_observers": []},
        }
        ctx = scheduler.SchedulerContext(
            emit_effect_steps=True,
            track="trading_shadow_mode",
            trading_fixture_path=Path("tests/fixtures/trading/price_series_simple.json"),
            trading_policy_path=Path("tests/fixtures/trading/shadow_policy_safe.json"),
            trading_shadow_model_path=Path("tests/fixtures/trading/shadow_model.json"),
            operator_policy={
                "operator_allowlist": ["CANONICAL_EQ09", "CANONICAL_EQ15"],
                "operator_strict": True,
            },
        )
        plan = scheduler.plan(program_ir, ctx)
        effect_types = [str(step.get("effect_type")) for step in plan.steps]
        self.assertIn("CANONICAL_INVOKE_EQ09", effect_types)
        self.assertIn("CANONICAL_INVOKE_EQ15", effect_types)
        self.assertIn("COMPUTE_DELTA_S", effect_types)
        self.assertIn("DELTA_S_GATE", effect_types)


if __name__ == "__main__":
    unittest.main()
