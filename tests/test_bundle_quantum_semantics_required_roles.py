import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")), encoding="utf-8")


class QuantumEvidenceBundleTests(unittest.TestCase):
    def test_bundle_quantum_semantics_requires_roles(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            out_dir = tmp / "out"
            program_ir = tmp / "program.ir.json"
            _write_json(program_ir, {"program": "ir"})

            result = subprocess.run(
                [
                    PYTHON,
                    str(ROOT / "tools" / "bundle_evidence.py"),
                    "--out-dir",
                    str(out_dir),
                    "--program-ir",
                    str(program_ir),
                    "--quantum-semantics-v1",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            bundles = list(out_dir.glob("bundle_*"))
            self.assertEqual(len(bundles), 1)
            manifest = bundles[0] / "bundle_manifest.json"
            data = json.loads(manifest.read_text(encoding="utf-8"))
            quantum = data["quantum_semantics_v1"]
            self.assertFalse(quantum["ok"])
            self.assertIn("plan", quantum["missing_required"])

    def test_bundle_quantum_semantics_ok(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            out_dir = tmp / "out"
            program_ir = tmp / "program.ir.json"
            plan = tmp / "plan.json"
            runtime_result = tmp / "runtime.json"
            backend_ir = tmp / "backend.json"

            _write_json(program_ir, {"program": "ir"})
            _write_json(plan, {"ok": True})
            _write_json(runtime_result, {"ok": True})
            _write_json(backend_ir, {"backend_target": "classical"})

            result = subprocess.run(
                [
                    PYTHON,
                    str(ROOT / "tools" / "bundle_evidence.py"),
                    "--out-dir",
                    str(out_dir),
                    "--program-ir",
                    str(program_ir),
                    "--plan",
                    str(plan),
                    "--runtime-result",
                    str(runtime_result),
                    "--backend-ir",
                    str(backend_ir),
                    "--quantum-semantics-v1",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0)
            bundles = list(out_dir.glob("bundle_*"))
            self.assertEqual(len(bundles), 1)
            manifest = bundles[0] / "bundle_manifest.json"
            data = json.loads(manifest.read_text(encoding="utf-8"))
            quantum = data["quantum_semantics_v1"]
            self.assertTrue(quantum["ok"])
            self.assertIn("backend_ir", quantum["present_roles"])


if __name__ == "__main__":
    unittest.main()
