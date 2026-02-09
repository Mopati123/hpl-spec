import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from hpl.audit.constraint_witness import build_constraint_witness
from hpl.execution_token import ExecutionToken
from hpl.observers import papas
from hpl.runtime.context import RuntimeContext
from hpl.runtime.contracts import ExecutionContract
from hpl.runtime.engine import RuntimeEngine


class PapasObserverReportTests(unittest.TestCase):
    def test_is_enabled_defaults(self):
        self.assertTrue(papas.is_enabled(None))
        self.assertTrue(papas.is_enabled(["papas"]))
        self.assertFalse(papas.is_enabled([]))
        self.assertFalse(papas.is_enabled(["other"]))

    def test_build_papas_report_deterministic(self):
        witness = build_constraint_witness(
            stage="runtime_refusal",
            refusal_reasons=["IOPermissionDenied", "BudgetExceeded"],
            artifact_digests={"plan": "sha256:deadbeef"},
            observer_id="papas",
            timestamp=None,
        )
        report_a = papas.build_papas_report(witness, allow_dual_proposal=True)
        report_b = papas.build_papas_report(witness, allow_dual_proposal=True)
        self.assertEqual(report_a, report_b)
        self.assertIn("dual_proposal", report_a)

        report_c = papas.build_papas_report(witness, allow_dual_proposal=False)
        self.assertNotIn("dual_proposal", report_c)

    def test_runtime_emits_papas_report_on_refusal(self):
        token = ExecutionToken.build()
        plan = {
            "plan_id": "plan_refusal",
            "program_id": "program_refusal",
            "status": "denied",
            "steps": [],
            "execution_token": token.to_dict(),
        }
        ctx = RuntimeContext()
        contract = ExecutionContract()
        result = RuntimeEngine().run(plan, ctx, contract)
        self.assertEqual(result.status, "denied")
        self.assertTrue(result.constraint_witnesses)
        self.assertTrue(result.observer_reports)
        report = result.observer_reports[0]
        self.assertEqual(report.get("observer_id"), "papas")

    def test_runtime_respects_observer_disable(self):
        token = ExecutionToken.build()
        plan = {
            "plan_id": "plan_refusal_disable",
            "program_id": "program_refusal_disable",
            "status": "denied",
            "steps": [],
            "execution_token": token.to_dict(),
        }
        ctx = RuntimeContext(observers=[])
        contract = ExecutionContract()
        result = RuntimeEngine().run(plan, ctx, contract)
        self.assertEqual(result.status, "denied")
        self.assertTrue(result.constraint_witnesses)
        self.assertEqual(result.observer_reports, [])

    def test_runtime_dual_proposal_gate(self):
        token = ExecutionToken.build()
        plan = {
            "plan_id": "plan_refusal_dual",
            "program_id": "program_refusal_dual",
            "status": "denied",
            "steps": [],
            "execution_token": token.to_dict(),
        }
        ctx = RuntimeContext(constraint_inversion_v1=True)
        contract = ExecutionContract()
        result = RuntimeEngine().run(plan, ctx, contract)
        report = result.observer_reports[0]
        self.assertIn("dual_proposal", report)


if __name__ == "__main__":
    unittest.main()
