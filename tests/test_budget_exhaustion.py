import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from hpl import scheduler
from hpl.execution_token import ExecutionToken
from hpl.runtime.contracts import ExecutionContract
from hpl.runtime.context import RuntimeContext
from hpl.runtime.engine import RuntimeEngine


FIXTURE = ROOT / "tests" / "fixtures" / "program_ir_minimal.json"


class BudgetExhaustionTests(unittest.TestCase):
    def test_budget_exhaustion_refusal(self):
        program_ir = json.loads(FIXTURE.read_text(encoding="utf-8"))
        ctx = scheduler.SchedulerContext(budget_steps=1)
        plan = scheduler.plan(program_ir, ctx)
        token = ExecutionToken.from_dict(plan.execution_token or {})

        contract = ExecutionContract(allowed_steps={step["operator_id"] for step in plan.steps})
        runtime_ctx = RuntimeContext(execution_token=token)
        result = RuntimeEngine().run(plan, runtime_ctx, contract)

        self.assertEqual(result.status, "denied")
        self.assertIn("budget_steps_exceeded", result.reasons)
        self.assertTrue(result.constraint_witnesses)
        witness = result.constraint_witnesses[0]
        self.assertIn("budget_steps_exceeded", witness.get("refusal_reasons", []))


if __name__ == "__main__":
    unittest.main()
