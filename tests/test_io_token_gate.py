import unittest

from hpl.execution_token import ExecutionToken
from hpl.runtime.context import RuntimeContext
from hpl.runtime.contracts import ExecutionContract
from hpl.runtime.engine import RuntimeEngine


class IoTokenGateTests(unittest.TestCase):
    def test_io_token_deterministic(self):
        policy = {
            "io_allowed": True,
            "io_scopes": ["order_submit", "order_cancel"],
            "io_endpoints_allowed": ["demo://broker"],
            "io_budget_calls": 2,
            "io_requires_reconciliation": True,
        }
        token_one = ExecutionToken.build(io_policy=policy)
        token_two = ExecutionToken.build(io_policy=policy)
        self.assertEqual(token_one.token_id, token_two.token_id)

    def test_io_permission_denied(self):
        policy = {"io_allowed": False, "io_scopes": []}
        token = ExecutionToken.build(io_policy=policy)
        plan = {
            "status": "planned",
            "steps": [
                {
                    "step_id": "io_step",
                    "effect_type": "NOOP",
                    "requires": {"io_scope": "ORDER_SUBMIT"},
                }
            ],
            "execution_token": token.to_dict(),
        }
        ctx = RuntimeContext()
        contract = ExecutionContract(allowed_steps={"io_step"})
        result = RuntimeEngine().run(plan, ctx, contract)
        self.assertEqual(result.status, "denied")
        self.assertTrue(any("IOPermissionDenied" in reason for reason in result.reasons))

    def test_io_budget_exceeded(self):
        policy = {"io_allowed": True, "io_scopes": ["ORDER_SUBMIT"], "io_budget_calls": 0}
        token = ExecutionToken.build(io_policy=policy)
        plan = {
            "status": "planned",
            "steps": [
                {
                    "step_id": "io_step",
                    "effect_type": "NOOP",
                    "requires": {"io_scope": "ORDER_SUBMIT"},
                }
            ],
            "execution_token": token.to_dict(),
        }
        ctx = RuntimeContext()
        contract = ExecutionContract(allowed_steps={"io_step"})
        result = RuntimeEngine().run(plan, ctx, contract)
        self.assertEqual(result.status, "denied")
        self.assertTrue(any("IOBudgetExceeded" in reason for reason in result.reasons))


if __name__ == "__main__":
    unittest.main()
