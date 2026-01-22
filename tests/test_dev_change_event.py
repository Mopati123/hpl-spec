import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from hpl.audit.dev_change_event import build_dev_change_event


class DevChangeEventTests(unittest.TestCase):
    def test_dev_change_event_deterministic(self):
        bundle1 = build_dev_change_event(
            mode="NEAR_AUTONOMOUS",
            branch="feature/test",
            target_ledger_item="A3",
            files_changed=["src/hpl/audit/dev_change_event.py"],
            test_results="ok",
            tool_outputs="ok",
            policy_version="1.0",
        )
        bundle2 = build_dev_change_event(
            mode="NEAR_AUTONOMOUS",
            branch="feature/test",
            target_ledger_item="A3",
            files_changed=["src/hpl/audit/dev_change_event.py"],
            test_results="ok",
            tool_outputs="ok",
            policy_version="1.0",
        )
        self.assertEqual(bundle1.event, bundle2.event)
        self.assertEqual(bundle1.witness_record, bundle2.witness_record)

    def test_dev_change_event_fields(self):
        bundle = build_dev_change_event(
            mode="PR_BOT",
            branch="feature/pr",
            target_ledger_item="A2",
            files_changed=["tools/papas_runner.py"],
            test_results="",
            tool_outputs="",
            policy_version="1.0",
        )
        event = bundle.event
        self.assertEqual(event["mode"], "PR_BOT")
        self.assertEqual(event["branch"], "feature/pr")
        self.assertEqual(event["target_ledger_item"], "A2")
        self.assertIn("files_changed_digest", event)
        self.assertIn("papas_witness_digest", event)


if __name__ == "__main__":
    unittest.main()
