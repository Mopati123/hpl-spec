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
        self.assertTrue(any("not declared" in error for error in errors))

    def test_projector_mismatch(self):
        path = FIXTURES / "coupling_registry_invalid_projector_mismatch.json"
        errors = validate_coupling_topology.validate_coupling_registry_file(path)
        self.assertTrue(errors)

    def test_missing_audit_obligation(self):
        path = FIXTURES / "coupling_registry_invalid_missing_audit_obligation.json"
        errors = validate_coupling_topology.validate_coupling_registry_file(path)
        self.assertTrue(errors)

    def test_cross_sector_invocation_without_projector_is_refused(self):
        path = FIXTURES / "coupling_registry_invalid_cross_sector_bypass.json"
        errors = validate_coupling_topology.validate_coupling_registry_file(path)
        self.assertEqual(len(errors), 1)
        self.assertIn("illegal cross-sector bypass", errors[0])
        self.assertIn("must declare projector 'sector.alpha.projector'", errors[0])

    def test_cross_sector_invocation_with_wrong_projector_is_refused(self):
        path = FIXTURES / "coupling_registry_invalid_invocation_projector.json"
        errors = validate_coupling_topology.validate_coupling_registry_file(path)
        self.assertEqual(len(errors), 1)
        self.assertIn("illegal cross-sector bypass", errors[0])
        self.assertIn("does not match edge 'edge.alpha.beta'", errors[0])

    def test_same_sector_invocation_does_not_require_projector_binding(self):
        registry = {
            "projectors": [
                {
                    "id": "sector.alpha.projector",
                    "domain": ["AlphaIn"],
                    "codomain": ["AlphaOut"],
                }
            ],
            "edges": [
                {
                    "id": "edge.alpha.internal",
                    "sector_src": "sector.alpha",
                    "sector_dst": "sector.alpha",
                    "projector": "sector.alpha.projector",
                    "domain": ["AlphaIn"],
                    "codomain": ["AlphaOut"],
                    "audit": {"requires": ["CouplingEvent"]},
                }
            ],
            "invocations": [{"edge_id": "edge.alpha.internal"}],
        }
        self.assertEqual(validate_coupling_topology.validate_coupling_registry_data(registry), [])

    def test_no_deferred_topology_rules_remain(self):
        self.assertEqual(validate_coupling_topology.DEFERRED_NOTES, [])

    def test_summary_has_no_deferred_v1_notice(self):
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
        self.assertNotIn("deferred", buf.getvalue().lower())
        self.assertIn('"notes": []', buf.getvalue())


if __name__ == "__main__":
    unittest.main()
