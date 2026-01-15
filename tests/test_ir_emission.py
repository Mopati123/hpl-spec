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
from hpl.dynamics import ir_emitter
from hpl.errors import ValidationError


EXAMPLE_PATH = ROOT / "examples" / "momentum_trade.hpl"


class IREmissionTests(unittest.TestCase):
    def _emit_ir(self):
        program = parser.parse_file(str(EXAMPLE_PATH))
        expanded = expander.expand_program(program)
        validator.validate_program(expanded)
        return ir_emitter.emit_program_ir(expanded, program_id="momentum_trade")

    def test_ir_emission_schema(self):
        ir = self._emit_ir()
        self.assertIn("program_id", ir)

    def test_ir_no_unknown_fields(self):
        ir = self._emit_ir()
        ir["unknown_field"] = "nope"
        with self.assertRaises(ValidationError):
            ir_emitter.validate_program_ir(ir)

    def test_ir_operator_class_enum(self):
        ir = self._emit_ir()
        classes = {term["cls"] for term in ir["hamiltonian"]["terms"]}
        allowed = {"U", "M", "Ω", "C", "I", "A"}
        self.assertTrue(classes.issubset(allowed))

    def test_ir_bootstrap_class_default(self):
        ir = self._emit_ir()
        for term in ir["hamiltonian"]["terms"]:
            self.assertEqual(term["cls"], "C")

    def test_ir_schema_validation_executed(self):
        ir = self._emit_ir()
        with self.assertRaises(ValidationError):
            ir_emitter.validate_program_ir("not a dict")


if __name__ == "__main__":
    unittest.main()
