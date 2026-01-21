import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_PATH = ROOT / "tools" / "validate_observer_registry.py"
SPEC = importlib.util.spec_from_file_location("validate_observer_registry", TOOLS_PATH)
validate_observer_registry = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_observer_registry)

FIXTURES = ROOT / "tests" / "fixtures"


class PapasObserverContractTests(unittest.TestCase):
    def test_valid_registry_and_schema(self):
        registry = FIXTURES / "observers_registry_v2_1.json"
        schema = FIXTURES / "trace_schema_with_witness.json"
        errors = []
        errors.extend(validate_observer_registry._validate_observers_registry(registry))
        errors.extend(validate_observer_registry._validate_trace_schema(schema))
        self.assertEqual(errors, [])

    def test_missing_papas_fails(self):
        registry = FIXTURES / "observers_registry_missing_papas.json"
        errors = validate_observer_registry._validate_observers_registry(registry)
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
