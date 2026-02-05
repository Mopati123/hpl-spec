import json
import tempfile
import unittest
from pathlib import Path

import pytest

from hpl.runtime.context import RuntimeContext
from hpl.runtime.effects import EffectStep, get_handler


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "pde"
pytestmark = pytest.mark.slow


class NavierStokesEffectsTests(unittest.TestCase):
    def _run_pipeline(self, work_dir: Path, policy_name: str) -> bytes:
        ctx = RuntimeContext(trace_sink=work_dir)
        state_path = FIXTURES / "ns_state_initial.json"
        policy_path = FIXTURES / policy_name

        steps = [
            EffectStep(
                step_id="evolve_linear",
                effect_type="NS_EVOLVE_LINEAR",
                args={"state_path": str(state_path), "out_path": "ns_state_linear.json"},
            ),
            EffectStep(
                step_id="apply_duhamel",
                effect_type="NS_APPLY_DUHAMEL",
                args={
                    "state_path": "ns_state_linear.json",
                    "policy_path": str(policy_path),
                    "out_path": "ns_state_nonlinear.json",
                },
            ),
            EffectStep(
                step_id="project_leray",
                effect_type="NS_PROJECT_LERAY",
                args={"state_path": "ns_state_nonlinear.json", "out_path": "ns_state_projected.json"},
            ),
            EffectStep(
                step_id="recover_pressure",
                effect_type="NS_PRESSURE_RECOVER",
                args={"state_path": "ns_state_projected.json", "out_path": "ns_pressure.json"},
            ),
            EffectStep(
                step_id="measure_obs",
                effect_type="NS_MEASURE_OBSERVABLES",
                args={
                    "state_path": "ns_state_projected.json",
                    "policy_path": str(policy_path),
                    "out_path": "ns_observables.json",
                },
            ),
            EffectStep(
                step_id="check_barrier",
                effect_type="NS_CHECK_BARRIER",
                args={
                    "observables_path": "ns_observables.json",
                    "policy_path": str(policy_path),
                    "out_path": "ns_gate_certificate.json",
                },
            ),
            EffectStep(
                step_id="emit_state",
                effect_type="NS_EMIT_STATE",
                args={"state_path": "ns_state_projected.json", "out_path": "ns_state_final.json"},
            ),
        ]

        for step in steps:
            handler = get_handler(step.effect_type)
            result = handler(step, ctx)
            self.assertTrue(result.ok, f"{step.effect_type} failed: {result.refusal_type}")

        return (work_dir / "ns_observables.json").read_bytes()

    def test_ns_effects_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp_one:
            obs_one = self._run_pipeline(Path(tmp_one), "ns_policy_safe.json")
        with tempfile.TemporaryDirectory() as tmp_two:
            obs_two = self._run_pipeline(Path(tmp_two), "ns_policy_safe.json")
        self.assertEqual(obs_one, obs_two)

    def test_ns_barrier_refusal(self):
        ctx = RuntimeContext(trace_sink=Path(tempfile.mkdtemp()))
        state_path = FIXTURES / "ns_state_initial.json"
        policy_path = FIXTURES / "ns_policy_forbidden.json"

        evolve = EffectStep(
            step_id="evolve_linear",
            effect_type="NS_EVOLVE_LINEAR",
            args={"state_path": str(state_path), "out_path": "ns_state_linear.json"},
        )
        get_handler(evolve.effect_type)(evolve, ctx)

        project = EffectStep(
            step_id="project_leray",
            effect_type="NS_PROJECT_LERAY",
            args={"state_path": "ns_state_linear.json", "out_path": "ns_state_projected.json"},
        )
        get_handler(project.effect_type)(project, ctx)

        measure = EffectStep(
            step_id="measure_obs",
            effect_type="NS_MEASURE_OBSERVABLES",
            args={
                "state_path": "ns_state_projected.json",
                "policy_path": str(policy_path),
                "out_path": "ns_observables.json",
            },
        )
        get_handler(measure.effect_type)(measure, ctx)

        barrier = EffectStep(
            step_id="check_barrier",
            effect_type="NS_CHECK_BARRIER",
            args={
                "observables_path": "ns_observables.json",
                "policy_path": str(policy_path),
                "out_path": "ns_gate_certificate.json",
            },
        )
        result = get_handler(barrier.effect_type)(barrier, ctx)
        self.assertFalse(result.ok)
        self.assertEqual(result.refusal_type, "EnergyBarrierViolated")


if __name__ == "__main__":
    unittest.main()
