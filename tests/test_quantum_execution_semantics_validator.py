import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import validate_quantum_execution_semantics as qes


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")), encoding="utf-8")


class QuantumExecutionSemanticsValidatorTests(unittest.TestCase):
    def test_validator_ok_with_required_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            program_ir = tmp / "program.ir.json"
            plan = tmp / "plan.json"
            runtime_result = tmp / "runtime.json"
            backend_ir = tmp / "backend.json"
            manifest = tmp / "bundle_manifest.json"

            _write_json(program_ir, {"program": "ir"})
            _write_json(plan, {"ok": True})
            _write_json(runtime_result, {"ok": True})
            _write_json(backend_ir, {"backend_target": "classical"})
            _write_json(manifest, {"bundle_id": "test"})

            result = qes.validate_quantum_execution_semantics(
                program_ir=program_ir,
                plan=plan,
                runtime_result=runtime_result,
                backend_ir=backend_ir,
                qasm=None,
                bundle_manifest=manifest,
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["errors"], [])

    def test_validator_missing_projection(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            program_ir = tmp / "program.ir.json"
            plan = tmp / "plan.json"
            runtime_result = tmp / "runtime.json"
            manifest = tmp / "bundle_manifest.json"

            _write_json(program_ir, {"program": "ir"})
            _write_json(plan, {"ok": True})
            _write_json(runtime_result, {"ok": True})
            _write_json(manifest, {"bundle_id": "test"})

            result = qes.validate_quantum_execution_semantics(
                program_ir=program_ir,
                plan=plan,
                runtime_result=runtime_result,
                backend_ir=None,
                qasm=None,
                bundle_manifest=manifest,
            )
            self.assertFalse(result["ok"])
            self.assertIn("missing backend projection", " ".join(result["errors"]))


if __name__ == "__main__":
    unittest.main()
