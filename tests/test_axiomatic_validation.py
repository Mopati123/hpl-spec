import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from hpl.emergence.dsl import parser
from hpl.emergence.macros import expander
from hpl.axioms import validator
from hpl.errors import ValidationError


EXAMPLE_PATH = ROOT / "examples" / "momentum_trade.hpl"


class AxiomaticValidationTests(unittest.TestCase):
    def test_validator_bnf_conformance(self):
        program = parser.parse_file(str(EXAMPLE_PATH))
        expanded = expander.expand_program(program)
        validator.validate_program(expanded)

    def test_validator_no_surface_forms(self):
        with self.assertRaises(ValidationError):
            validator.validate_program([parser.parse_program("(defstrategy x)")[0]])

    def test_validator_error_reporting(self):
        try:
            validator.validate_program([parser.parse_program("(hamiltonian (term a x))")[0]])
        except ValidationError as exc:
            self.assertIsNotNone(exc.path)
            return
        self.fail("Expected ValidationError")


if __name__ == "__main__":
    unittest.main()
