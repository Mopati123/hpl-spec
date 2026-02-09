from __future__ import annotations

import unittest

from hpl import scheduler
from hpl.execution_token import ExecutionToken
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


class OperatorRegistryEnforcementTests(unittest.TestCase):
    def test_plan_denied_when_registry_enforced(self):
        program_ir = _sample_program_ir()
        ctx = scheduler.SchedulerContext(operator_registry_enforced=True)
        plan = scheduler.plan(program_ir, ctx)
        self.assertEqual(plan.status, "denied")
        self.assertTrue(
            any("operator registry missing" in reason for reason in plan.reasons)
        )

    def test_plan_allowed_when_registry_not_enforced(self):
        program_ir = _sample_program_ir()
        ctx = scheduler.SchedulerContext()
        plan = scheduler.plan(program_ir, ctx)
        self.assertEqual(plan.status, "planned")

    def test_runtime_denied_when_registry_enforced(self):
        token = ExecutionToken.build(
            allowed_backends=["CLASSICAL"],
            budget_steps=10,
            determinism_mode="deterministic",
        )
        plan = {
            "status": "planned",
            "steps": [{"operator_id": "SURF_A"}],
            "execution_token": token.to_dict(),
            "operator_registry_enforced": True,
        }
        ctx = RuntimeContext(execution_token=token)
        contract = ExecutionContract(allowed_steps={"SURF_A"})
        result = RuntimeEngine().run(plan, ctx, contract)
        self.assertEqual(result.status, "denied")
        self.assertTrue(
            any("operator registry missing" in reason for reason in result.reasons)
        )


if __name__ == "__main__":
    unittest.main()
