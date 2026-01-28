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


class BundleConstraintInversionTests(unittest.TestCase):
    def test_bundle_requires_constraint_roles(self):
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
                    "--constraint-inversion-v1",
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
            section = data["constraint_inversion_v1"]
            self.assertFalse(section["ok"])
            self.assertIn("constraint_witness", section["missing_required"])

    def test_bundle_constraint_roles_ok(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            out_dir = tmp / "out"
            program_ir = tmp / "program.ir.json"
            constraint_witness = tmp / "constraint_witness.json"
            dual_proposal = tmp / "dual_proposal.json"

            _write_json(program_ir, {"program": "ir"})
            _write_json(constraint_witness, {"witness_id": "sha256:test"})
            _write_json(dual_proposal, {"dual_proposal_id": "sha256:test"})

            result = subprocess.run(
                [
                    PYTHON,
                    str(ROOT / "tools" / "bundle_evidence.py"),
                    "--out-dir",
                    str(out_dir),
                    "--program-ir",
                    str(program_ir),
                    "--constraint-witness",
                    str(constraint_witness),
                    "--dual-proposal",
                    str(dual_proposal),
                    "--constraint-inversion-v1",
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
            section = data["constraint_inversion_v1"]
            self.assertTrue(section["ok"])


if __name__ == "__main__":
    unittest.main()
