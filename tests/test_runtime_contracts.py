import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from hpl import scheduler
from hpl.runtime.context import RuntimeContext
from hpl.runtime.contracts import ExecutionContract
from hpl.runtime.engine import RuntimeEngine


def _sample_program_ir():
    return {
        "program_id": "test_program",
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


def _build_plan():
    return scheduler.plan(_sample_program_ir(), scheduler.SchedulerContext())


class RuntimeContractTests(unittest.TestCase):
    def test_refuse_if_plan_not_ok(self):
        base_plan = _build_plan()
        plan = scheduler.ExecutionPlan(
            plan_id=base_plan.plan_id,
            program_id=base_plan.program_id,
            status="denied",
            steps=base_plan.steps,
            reasons=[],
            verification=None,
            witness_records=[],
            execution_token=base_plan.execution_token,
        )
        ctx = RuntimeContext()
        contract = ExecutionContract(allowed_steps={"SURF_A", "SURF_B"})
        result = RuntimeEngine().run(plan, ctx, contract)
        self.assertEqual(result.status, "denied")
        self.assertTrue(any("plan not approved" in reason for reason in result.reasons))
        self.assertTrue(result.constraint_witnesses)

    def test_refuse_step_not_in_contract_allowed_steps(self):
        plan = _build_plan()
        ctx = RuntimeContext()
        contract = ExecutionContract(allowed_steps={"SURF_B"})
        result = RuntimeEngine().run(plan, ctx, contract)
        self.assertEqual(result.status, "denied")
        self.assertTrue(any("step not allowed" in reason for reason in result.reasons))
        self.assertTrue(result.constraint_witnesses)

    def test_refuse_epoch_verification_failure(self):
        plan = _build_plan()
        ctx = RuntimeContext()
        contract = ExecutionContract(require_epoch_verification=True)
        with mock.patch("hpl.runtime.engine._verify_epoch_and_signature") as mock_verify:
            mock_verify.return_value = (
                {"anchor_ok": False, "signature_ok": False, "errors": ["epoch failure"]},
                ["epoch failure"],
            )
            result = RuntimeEngine().run(plan, ctx, contract)
        self.assertEqual(result.status, "denied")
        self.assertTrue(any("epoch failure" in reason for reason in result.reasons))
        stages = [record.get("stage") for record in result.witness_records]
        self.assertIn("epoch_verification", stages)
        self.assertTrue(result.constraint_witnesses)

    def test_trace_and_papas_witness_emitted(self):
        plan = _build_plan()
        ctx = RuntimeContext()
        contract = ExecutionContract(allowed_steps={"SURF_B"})
        result = RuntimeEngine().run(plan, ctx, contract)
        stages = [record.get("stage") for record in result.witness_records]
        self.assertIn("runtime_start", stages)
        self.assertIn("runtime_complete", stages)
        self.assertTrue(any(stage == "step_denied" for stage in stages))
        self.assertTrue(
            all(record.get("observer_id") == "papas" for record in result.witness_records)
        )

    def test_determinism_runtime_result(self):
        plan = _build_plan()
        ctx = RuntimeContext()
        contract = ExecutionContract(allowed_steps={"SURF_A", "SURF_B"})
        result_one = RuntimeEngine().run(plan, ctx, contract)
        result_two = RuntimeEngine().run(plan, ctx, contract)
        json_one = json.dumps(result_one.to_dict(), sort_keys=True)
        json_two = json.dumps(result_two.to_dict(), sort_keys=True)
        self.assertEqual(json_one, json_two)
        self.assertEqual(result_one.result_id, result_two.result_id)
        self.assertEqual(result_one.constraint_witnesses, result_two.constraint_witnesses)


if __name__ == "__main__":
    unittest.main()
