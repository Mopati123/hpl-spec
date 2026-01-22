import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS_PATH = ROOT / "tools" / "papas_runner.py"
SPEC = __import__("importlib.util").util.spec_from_file_location("papas_runner", TOOLS_PATH)
papas_runner = __import__("importlib.util").util.module_from_spec(SPEC)
SPEC.loader.exec_module(papas_runner)

POLICY_PATH = ROOT / "config" / "papas_policy.yaml"


class PapasRunnerTests(unittest.TestCase):
    def _load_policy(self):
        return papas_runner.load_policy(POLICY_PATH)

    def test_non_whitelisted_command_denied(self):
        policy = self._load_policy()
        with self.assertRaises(ValueError):
            papas_runner.resolve_command(policy, "rm_rf")

    def test_pr_bot_cannot_execute(self):
        policy = self._load_policy()
        with self.assertRaises(ValueError):
            papas_runner.run_named_command(policy, "PR_BOT", "pytest_full", dry_run=True)

    def test_forbidden_path_blocked(self):
        policy = self._load_policy()
        with self.assertRaises(ValueError):
            papas_runner.check_paths_allowed(policy, ["axioms_H/README.md"])

    def test_allowed_path_passes(self):
        policy = self._load_policy()
        papas_runner.check_paths_allowed(policy, ["src/hpl/trace.py"])

    def test_policy_json_compatible_yaml(self):
        data = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        self.assertIn("policy_version", data)


if __name__ == "__main__":
    unittest.main()
