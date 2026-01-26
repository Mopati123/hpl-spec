import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from hpl.backends.classical_lowering import lower_program_ir_to_backend_ir

FIXTURE = ROOT / "tests" / "fixtures" / "program_ir_minimal.json"


class ClassicalLoweringTests(unittest.TestCase):
    def _load_program_ir(self):
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_backend_ir_determinism(self):
        program_ir = self._load_program_ir()
        ir_one = lower_program_ir_to_backend_ir(program_ir)
        ir_two = lower_program_ir_to_backend_ir(program_ir)
        self.assertEqual(ir_one.to_dict(), ir_two.to_dict())
        self.assertEqual(ir_one.program_digest, ir_two.program_digest)
        self.assertEqual(ir_one.backend_target, "classical")

    def test_backend_ir_witness_present(self):
        program_ir = self._load_program_ir()
        backend_ir = lower_program_ir_to_backend_ir(program_ir)
        evidence = backend_ir.evidence
        self.assertIn("papas_witness_record", evidence)
        witness = json.loads(evidence["papas_witness_record"])
        self.assertEqual(witness["observer_id"], "papas")


if __name__ == "__main__":
    unittest.main()
