import importlib.util
import io
from pathlib import Path
import unittest
import contextlib
import sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS_PATH = ROOT / "tools" / "validate_coupling_topology.py"
SPEC = importlib.util.spec_from_file_location("validate_coupling_topology", TOOLS_PATH)
validate_coupling_topology = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_coupling_topology)

FIXTURES = ROOT / "tests" / "fixtures"


class CouplingTopologyValidatorTests(unittest.TestCase):
    def test_valid_registry(self):
        path = FIXTURES / "coupling_registry_valid.json"
        errors = validate_coupling_topology.validate_coupling_registry_file(path)
        self.assertEqual(errors, [])

    def test_undeclared_edge_invocation(self):
        path = FIXTURES / "coupling_registry_invalid_undeclared_edge.json"
        errors = validate_coupling_topology.validate_coupling_registry_file(path)
        self.assertTrue(errors)

    def test_projector_mismatch(self):
        path = FIXTURES / "coupling_registry_invalid_projector_mismatch.json"
        errors = validate_coupling_topology.validate_coupling_registry_file(path)
        self.assertTrue(errors)

    def test_missing_audit_obligation(self):
        path = FIXTURES / "coupling_registry_invalid_missing_audit_obligation.json"
        errors = validate_coupling_topology.validate_coupling_registry_file(path)
        self.assertTrue(errors)

    def test_deferred_bypass_rule_notice(self):
        notes = validate_coupling_topology.DEFERRED_NOTES
        self.assertTrue(any("deferred" in note.lower() for note in notes))

    def test_summary_notes_in_main_output(self):
        path = FIXTURES / "coupling_registry_valid.json"
        buf = io.StringIO()
        original_argv = sys.argv
        try:
            sys.argv = ["validate_coupling_topology.py", str(path)]
            with contextlib.redirect_stdout(buf):
                result = validate_coupling_topology.main()
        finally:
            sys.argv = original_argv

        self.assertEqual(result, 0)
        self.assertIn("deferred", buf.getvalue().lower())


if __name__ == "__main__":
    unittest.main()
