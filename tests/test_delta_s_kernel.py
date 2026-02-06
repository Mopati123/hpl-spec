import json
import tempfile
import unittest
from pathlib import Path

from hpl.execution_token import ExecutionToken
from hpl.runtime.context import RuntimeContext
from hpl.runtime.contracts import ExecutionContract
from hpl.runtime.engine import RuntimeEngine
from hpl.runtime.effects import EffectStep, get_handler


class DeltaSKernelTests(unittest.TestCase):
    def test_delta_s_report_deterministic(self):
        def run_once() -> bytes:
            with tempfile.TemporaryDirectory() as tmp:
                work = Path(tmp)
                prior = work / "prior.json"
                posterior = work / "posterior.json"
                prior.write_text(json.dumps({"state": [1, 2, 3]}, sort_keys=True), encoding="utf-8")
                posterior.write_text(json.dumps({"state": [2, 3, 5]}, sort_keys=True), encoding="utf-8")
                ctx = RuntimeContext(trace_sink=work)
                step = EffectStep(
                    step_id="delta_s",
                    effect_type="COMPUTE_DELTA_S",
                    args={
                        "prior_path": str(prior),
                        "posterior_path": str(posterior),
                        "out_path": "delta_s_report.json",
                    },
                )
                result = get_handler(step.effect_type)(step, ctx)
                self.assertTrue(result.ok)
                return (work / "delta_s_report.json").read_bytes()

        first = run_once()
        second = run_once()
        self.assertEqual(first, second)

    def test_irreversible_requires_delta_s(self):
        token = ExecutionToken.build(
            collapse_requires_delta_s=True,
            delta_s_policy={"threshold": 0.1, "comparator": "gte"},
            measurement_modes_allowed=["MEASURE_CONDITION", "COMPUTE_DELTA_S", "DELTA_S_GATE"],
        )
        plan = {
            "status": "planned",
            "steps": [
                {
                    "step_id": "collapse_step",
                    "effect_type": "NOOP",
                    "requires": {"irreversible": True},
                }
            ],
            "execution_token": token.to_dict(),
        }
        with tempfile.TemporaryDirectory() as tmp:
            ctx = RuntimeContext(trace_sink=Path(tmp))
            contract = ExecutionContract(allowed_steps={"collapse_step"})
            result = RuntimeEngine().run(plan, ctx, contract)
            self.assertEqual(result.status, "denied")
            self.assertTrue(any("delta_s_evidence_missing" in reason for reason in result.reasons))
            self.assertTrue(result.constraint_witnesses)


if __name__ == "__main__":
    unittest.main()
