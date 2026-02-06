import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from hpl.execution_token import ExecutionToken
from hpl.runtime.context import RuntimeContext
from hpl.runtime.effects import EffectStep, EffectType, get_handler


class IOReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self.tmp_dir.name)
        self.request_path = self.tmp / "request.json"
        self.response_path = self.tmp / "response.json"
        self.request_path.write_text(
            json.dumps({"request_id": "req-1", "action": "submit_order"}, sort_keys=True),
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp_dir.cleanup()

    def _ctx(self):
        token = ExecutionToken.build(
            io_policy={
                "io_allowed": True,
                "io_scopes": ["RECONCILE", "ROLLBACK"],
                "io_requires_reconciliation": True,
            }
        )
        return RuntimeContext(trace_sink=self.tmp, execution_token=token)

    def test_reconcile_commit(self):
        self.response_path.write_text(
            json.dumps({"status": "accepted"}, sort_keys=True),
            encoding="utf-8",
        )
        step = EffectStep(
            step_id="reconcile",
            effect_type=EffectType.IO_RECONCILE,
            args={
                "request_path": "request.json",
                "response_path": "response.json",
                "expected_status": "accepted",
            },
        )
        result = get_handler(step.effect_type)(step, self._ctx())
        self.assertTrue(result.ok)
        outcome = json.loads((self.tmp / "io_outcome.json").read_text(encoding="utf-8"))
        self.assertEqual(outcome["action"], "commit")

    def test_reconcile_rollback_and_record(self):
        self.response_path.write_text(
            json.dumps({"status": "rejected", "ambiguous": True}, sort_keys=True),
            encoding="utf-8",
        )
        reconcile = EffectStep(
            step_id="reconcile",
            effect_type=EffectType.IO_RECONCILE,
            args={
                "request_path": "request.json",
                "response_path": "response.json",
                "expected_status": "accepted",
            },
        )
        reconcile_result = get_handler(reconcile.effect_type)(reconcile, self._ctx())
        self.assertFalse(reconcile_result.ok)
        outcome = json.loads((self.tmp / "io_outcome.json").read_text(encoding="utf-8"))
        self.assertEqual(outcome["action"], "rollback")
        rollback = EffectStep(
            step_id="rollback",
            effect_type=EffectType.IO_ROLLBACK,
            args={"outcome_path": "io_outcome.json"},
        )
        rollback_result = get_handler(rollback.effect_type)(rollback, self._ctx())
        self.assertTrue(rollback_result.ok)
        record_path = self.tmp / "rollback_record.json"
        self.assertTrue(record_path.exists())


if __name__ == "__main__":
    unittest.main()
