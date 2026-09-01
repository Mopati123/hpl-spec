import copy
import sys
import unittest
from dataclasses import replace
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


def _program_ir():
    return {
        "program_id": "runtime_plan_integrity",
        "hamiltonian": {
            "terms": [
                {"operator_id": "SURF_A", "cls": "C", "coefficient": 1.0},
            ]
        },
        "operators": {
            "SURF_A": {"type": "unspecified", "commutes_with": [], "backend_map": []},
        },
        "invariants": [],
        "scheduler": {"collapse_policy": "unspecified", "authorized_observers": []},
    }


def _plan():
    return scheduler.plan(_program_ir(), scheduler.SchedulerContext())


class RuntimePlanIntegrityTests(unittest.TestCase):
    def test_valid_scheduler_plan_passes_integrity_gate(self):
        plan = _plan()
        result = RuntimeEngine().run(
            plan,
            RuntimeContext(),
            ExecutionContract(allowed_steps={"SURF_A"}),
        )

        self.assertEqual(result.status, "completed")
        self.assertNotIn("plan_integrity_mismatch", result.reasons)
        self.assertNotIn(
            "plan_integrity_denied",
            [record.get("stage") for record in result.witness_records],
        )

    def test_mutated_steps_are_denied_before_effect_dispatch(self):
        plan = _plan()
        mutated = replace(plan, steps=[])

        with mock.patch("hpl.runtime.engine._execute_effect_with_context") as execute:
            result = RuntimeEngine().run(
                mutated,
                RuntimeContext(),
                ExecutionContract(allowed_steps={"SURF_A"}),
            )

        self.assertEqual(result.status, "denied")
        self.assertIn("plan_integrity_mismatch", result.reasons)
        self.assertEqual(result.transcript, [])
        execute.assert_not_called()
        self.assertIn(
            "plan_integrity_denied",
            [record.get("stage") for record in result.witness_records],
        )

    def test_mutated_completion_requirements_are_denied_before_effect_dispatch(self):
        plan = _plan()
        mutated = replace(
            plan,
            completion_requirements={"required_successful_effects": ["NOOP"]},
        )

        with mock.patch("hpl.runtime.engine._execute_effect_with_context") as execute:
            result = RuntimeEngine().run(
                mutated,
                RuntimeContext(),
                ExecutionContract(allowed_steps={"SURF_A"}),
            )

        self.assertEqual(result.status, "denied")
        self.assertIn("plan_integrity_mismatch", result.reasons)
        self.assertEqual(result.transcript, [])
        execute.assert_not_called()

    def test_mutated_execution_token_is_denied_before_plan_token_is_consumed(self):
        plan = _plan()
        token = copy.deepcopy(plan.execution_token)
        self.assertIsInstance(token, dict)
        token["budget_steps"] = int(token["budget_steps"]) + 1
        mutated = replace(plan, execution_token=token)

        with mock.patch("hpl.runtime.engine._execute_effect_with_context") as execute:
            result = RuntimeEngine().run(
                mutated,
                RuntimeContext(),
                ExecutionContract(allowed_steps={"SURF_A"}),
            )

        self.assertEqual(result.status, "denied")
        self.assertEqual(result.reasons, ["plan_integrity_mismatch"])
        self.assertEqual(result.transcript, [])
        execute.assert_not_called()

    def test_mutated_registry_binding_is_denied_before_effect_dispatch(self):
        plan = _plan()
        mutated = replace(
            plan,
            operator_registry_enforced=True,
            operator_registry_paths=[],
        )

        with mock.patch("hpl.runtime.engine._execute_effect_with_context") as execute:
            result = RuntimeEngine().run(
                mutated,
                RuntimeContext(),
                ExecutionContract(allowed_steps={"SURF_A"}),
            )

        self.assertEqual(result.status, "denied")
        self.assertIn("plan_integrity_mismatch", result.reasons)
        self.assertEqual(result.transcript, [])
        execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
