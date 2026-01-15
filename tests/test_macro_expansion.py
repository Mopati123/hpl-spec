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
from hpl.errors import MacroExpansionError


EXAMPLE_PATH = ROOT / "examples" / "momentum_trade.hpl"
SURFACE_SYMBOLS = {
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


class MacroExpansionTests(unittest.TestCase):
    def _expand_example(self):
        program = parser.parse_file(str(EXAMPLE_PATH))
        return expander.expand_program(program)

    def test_macro_determinism(self):
        first = self._expand_example()
        second = self._expand_example()
        self.assertEqual(first[0].to_data(), second[0].to_data())

    def test_macro_totality(self):
        with self.assertRaises(MacroExpansionError):
            expander.expand_program([])

    def test_macro_no_leakage_and_namespacing(self):
        expanded = self._expand_example()
        for node in iter_nodes(expanded[0]):
            if node.is_atom and isinstance(node.value, str):
                self.assertNotIn(node.value, SURFACE_SYMBOLS)
                if node.value.startswith("SURF_"):
                    self.assertTrue(node.value[5:])

    def test_macro_bootstrap_canonicalization(self):
        expanded = self._expand_example()
        self.assertEqual(len(expanded), 1)
        head = expanded[0].as_list()[0].as_atom()
        self.assertEqual(head, "hamiltonian")


if __name__ == "__main__":
    unittest.main()
