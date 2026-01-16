import json
import sys
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from hpl.emergence.dsl import parser
from hpl.emergence.macros import expander
from hpl.axioms import validator
from hpl.dynamics import ir_emitter
from hpl.trace import TraceCollector


EXAMPLE_PATH = ROOT / "examples" / "momentum_trade.hpl"


class TraceabilityTests(unittest.TestCase):
    def _run_pipeline(self):
        program = parser.parse_file(str(EXAMPLE_PATH))
        trace = TraceCollector(program_id="momentum_trade")
        expanded = expander.expand_program(program, trace=trace)
        validator.validate_program(expanded, trace=trace)
        ir = ir_emitter.emit_program_ir(expanded, program_id="momentum_trade", trace=trace)
        return ir, trace

    def test_trace_presence(self):
        _ir, trace = self._run_pipeline()
        data = trace.to_dict()
        self.assertTrue(data["nodes"])
        self.assertTrue(data["mappings"])

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "momentum.trace.json"
            trace.write_json(path)
            loaded = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["program_id"], "momentum_trade")

    def test_trace_determinism(self):
        _ir1, trace1 = self._run_pipeline()
        _ir2, trace2 = self._run_pipeline()
        self.assertEqual(trace1.to_dict(), trace2.to_dict())

    def test_trace_ir_unchanged(self):
        program = parser.parse_file(str(EXAMPLE_PATH))
        expanded = expander.expand_program(program)
        validator.validate_program(expanded)
        ir_plain = ir_emitter.emit_program_ir(expanded, program_id="momentum_trade")

        ir_traced, _trace = self._run_pipeline()
        self.assertEqual(ir_plain, ir_traced)


if __name__ == "__main__":
    unittest.main()
