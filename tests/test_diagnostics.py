import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from hpl.axioms import validator
from hpl.diagnostics import format_error_json, normalize_error
from hpl.dynamics import ir_emitter
from hpl.emergence.dsl import parser
from hpl.emergence.macros import expander
from hpl.errors import MacroExpansionError, ParseError, ValidationError


class DiagnosticsTests(unittest.TestCase):
    def test_category_assignment(self):
        with self.assertRaises(ParseError) as ctx:
            parser.parse_program(")")
        data = normalize_error(ctx.exception)
        self.assertEqual(data["category"], "parse")
        self.assertEqual(data["code"], "PARSE_ERROR")

        with self.assertRaises(MacroExpansionError) as ctx:
            expander.expand_program([])
        data = normalize_error(ctx.exception)
        self.assertEqual(data["category"], "macro")
        self.assertEqual(data["code"], "MACRO_ERROR")

        with self.assertRaises(ValidationError) as ctx:
            validator.validate_program([parser.parse_program("(hamiltonian (term a x))")[0]])
        data = normalize_error(ctx.exception)
        self.assertEqual(data["category"], "validation")
        self.assertEqual(data["code"], "VALIDATION_ERROR")

        with self.assertRaises(ValidationError) as ctx:
            ir_emitter.validate_program_ir("not a dict")
        data = normalize_error(ctx.exception, category_override="ir_schema")
        self.assertEqual(data["category"], "ir_schema")
        self.assertEqual(data["code"], "IR_SCHEMA_ERROR")

    def test_required_fields(self):
        with self.assertRaises(ParseError) as ctx:
            parser.parse_program(")")
        data = normalize_error(ctx.exception)
        for key in ("code", "category", "message", "location", "path", "cause"):
            self.assertIn(key, data)

    def test_behavior_unchanged(self):
        with self.assertRaises(ParseError):
            parser.parse_program(")")
        with self.assertRaises(MacroExpansionError):
            expander.expand_program([])
        with self.assertRaises(ValidationError):
            ir_emitter.validate_program_ir("not a dict")

    def test_json_is_stable(self):
        with self.assertRaises(ParseError) as ctx:
            parser.parse_program(")")
        first = format_error_json(ctx.exception)
        second = format_error_json(ctx.exception)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
