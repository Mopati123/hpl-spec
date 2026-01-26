import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from hpl.backends.classical_lowering import lower_program_ir_to_backend_ir
from hpl.backends.qasm_lowering import build_qasm_artifact, lower_backend_ir_to_qasm

FIXTURE = ROOT / "tests" / "fixtures" / "program_ir_minimal.json"


class QasmLoweringTests(unittest.TestCase):
    def _load_program_ir(self):
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def _backend_ir(self):
        program_ir = self._load_program_ir()
        return lower_program_ir_to_backend_ir(program_ir).to_dict()

    def test_qasm_determinism(self):
        backend_ir = self._backend_ir()
        qasm_one = lower_backend_ir_to_qasm(backend_ir)
        qasm_two = lower_backend_ir_to_qasm(backend_ir)
        self.assertEqual(qasm_one, qasm_two)

    def test_qasm_structure(self):
        backend_ir = self._backend_ir()
        qasm = lower_backend_ir_to_qasm(backend_ir)
        self.assertIn("OPENQASM 2.0;", qasm)
        self.assertIn("qreg q[1];", qasm)
        self.assertIn("creg c[1];", qasm)
        self.assertIn("ry(", qasm)
        self.assertIn("measure q[0] -> c[0];", qasm)

    def test_qasm_witness_present(self):
        backend_ir = self._backend_ir()
        artifact = build_qasm_artifact(backend_ir)
        evidence = artifact["evidence"]
        witness = json.loads(evidence["papas_witness_record"])
        self.assertEqual(witness["observer_id"], "papas")


if __name__ == "__main__":
    unittest.main()
