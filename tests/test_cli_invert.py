import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = [sys.executable, "-m", "hpl.cli"]


def _env():
    env = os.environ.copy()
    src_path = str(ROOT / "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")
    return env


def _run_cmd(args):
    return subprocess.run(
        CLI + args,
        cwd=ROOT,
        env=_env(),
        capture_output=True,
        text=True,
    )


class CliInvertTests(unittest.TestCase):
    def test_invert_determinism(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            witness_path = tmp / "witness.json"
            out_path = tmp / "proposal.json"
            witness = {
                "witness_id": "sha256:test",
                "stage": "runtime_refusal",
                "refusal_reasons": ["reason_b", "reason_a"],
                "artifact_digests": {"plan": "sha256:abc"},
            }
            witness_path.write_text(
                json.dumps(witness, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )

            first = _run_cmd(["invert", "--witness", str(witness_path), "--out", str(out_path)])
            self.assertEqual(first.returncode, 0)
            first_bytes = out_path.read_bytes()

            second = _run_cmd(["invert", "--witness", str(witness_path), "--out", str(out_path)])
            self.assertEqual(second.returncode, 0)
            second_bytes = out_path.read_bytes()

            self.assertEqual(first_bytes, second_bytes)
            data = json.loads(first_bytes.decode("utf-8"))
            self.assertIn("dual_proposal_id", data)

    def test_invert_invalid_witness(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            witness_path = tmp / "witness.json"
            out_path = tmp / "proposal.json"
            witness_path.write_text("{}", encoding="utf-8")

            result = _run_cmd(["invert", "--witness", str(witness_path), "--out", str(out_path)])
            self.assertEqual(result.returncode, 0)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertFalse(data.get("ok", True))
            self.assertTrue(data.get("errors"))


if __name__ == "__main__":
    unittest.main()
