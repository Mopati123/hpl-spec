import importlib.util
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

TOOLS_PATH = ROOT / "tools" / "validate_operator_registries.py"
SPEC = importlib.util.spec_from_file_location("validate_operator_registries", TOOLS_PATH)
validate_operator_registries = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_operator_registries)


FIXTURES = ROOT / "tests" / "fixtures"


class RegistryValidatorTests(unittest.TestCase):
    def test_valid_fixture(self):
        schema = validate_operator_registries._load_schema()
        path = FIXTURES / "registry_valid.json"
        errors = validate_operator_registries.validate_registry_file(path, schema)
        self.assertEqual(errors, [])

    def test_invalid_fixture(self):
        schema = validate_operator_registries._load_schema()
        path = FIXTURES / "registry_invalid.json"
        errors = validate_operator_registries.validate_registry_file(path, schema)
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
