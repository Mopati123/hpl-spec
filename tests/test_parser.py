import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from hpl.emergence.dsl import parser
from hpl.errors import ParseError


EXAMPLE_PATH = ROOT / "examples" / "momentum_trade.hpl"


class ParserTests(unittest.TestCase):
    def test_parser_surface_sexpr(self):
        program = parser.parse_program("(foo (bar 1) baz)")
        self.assertEqual(len(program), 1)
        self.assertTrue(program[0].is_list)

    def test_parser_momentum_example(self):
        program = parser.parse_file(str(EXAMPLE_PATH))
        self.assertTrue(program)

    def test_parser_structural_errors(self):
        with self.assertRaises(ParseError):
            parser.parse_program("(foo (bar 1)")
        with self.assertRaises(ParseError):
            parser.parse_program(")")


if __name__ == "__main__":
    unittest.main()
