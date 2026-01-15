import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from hpl.ast import iter_nodes
from hpl.emergence.dsl import parser
from hpl.emergence.macros import expander
from hpl.axioms import validator
from hpl.dynamics import ir_emitter

EXAMPLE_PATH = ROOT / "examples" / "momentum_trade.hpl"


class PipelineTests(unittest.TestCase):
    def test_parse_surface(self):
        program = parser.parse_file(str(EXAMPLE_PATH))
        self.assertTrue(program)

    def test_macro_expand(self):
        program = parser.parse_file(str(EXAMPLE_PATH))
        expanded = expander.expand_program(program)
        surface_symbols = {
            "defstrategy",
            "params",
            "let",
            "if",
            ">",
            "buy",
            "sell",
            "signal",
            "ma-diff",
            "price",
            "window",
            "threshold",
            "size",
        }
        for node in iter_nodes(expanded[0]):
            if node.is_atom and isinstance(node.value, str):
                self.assertNotIn(node.value, surface_symbols)

    def test_validate_axiomatic(self):
        program = parser.parse_file(str(EXAMPLE_PATH))
        expanded = expander.expand_program(program)
        validator.validate_program(expanded)

    def test_emit_ir(self):
        program = parser.parse_file(str(EXAMPLE_PATH))
        expanded = expander.expand_program(program)
        validator.validate_program(expanded)
        ir = ir_emitter.emit_program_ir(expanded, program_id="momentum_trade")
        self.assertEqual(ir["program_id"], "momentum_trade")


if __name__ == "__main__":
    unittest.main()
