import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

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
            ]
        },
        "operators": {
            "SURF_A": {"type": "unspecified", "commutes_with": [], "backend_map": []},
        },
        "invariants": [],
        "scheduler": {"collapse_policy": "unspecified", "authorized_observers": []},
    }


class RuntimeBackendTokenGateTests(unittest.TestCase):
    def test_backend_not_permitted_refusal(self):
        plan = scheduler.plan(_sample_program_ir(), scheduler.SchedulerContext())
        token = ExecutionToken.build(allowed_backends=["CLASSICAL"])
        ctx = RuntimeContext(execution_token=token, requested_backend="QASM")
        contract = ExecutionContract(
            allowed_steps={"SURF_A"},
            required_backend="QASM",
        )
        result = RuntimeEngine().run(plan, ctx, contract)
        self.assertEqual(result.status, "denied")
        self.assertTrue(any("backend not permitted" in reason for reason in result.reasons))
        self.assertTrue(result.constraint_witnesses)

    def test_backend_permitted(self):
        plan = scheduler.plan(_sample_program_ir(), scheduler.SchedulerContext())
        token = ExecutionToken.build(allowed_backends=["CLASSICAL", "QASM"])
        ctx = RuntimeContext(execution_token=token, requested_backend="QASM")
        contract = ExecutionContract(
            allowed_steps={"SURF_A"},
            required_backend="QASM",
        )
        result = RuntimeEngine().run(plan, ctx, contract)
        self.assertEqual(result.status, "completed")


if __name__ == "__main__":
    unittest.main()
