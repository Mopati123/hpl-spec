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


class CliLifecycleTests(unittest.TestCase):
    def test_lifecycle_classical_determinism(self):
        with tempfile.TemporaryDirectory() as tmp_dir_one:
            out_one = Path(tmp_dir_one) / "out"
            result_one = _run_cmd(
                [
                    "lifecycle",
                    "examples/momentum_trade.hpl",
                    "--backend",
                    "classical",
                    "--out-dir",
                    str(out_one),
                ]
            )
            self.assertEqual(result_one.returncode, 0)
            summary_one = json.loads(result_one.stdout)
            self.assertTrue(summary_one["bundle_id"])

        with tempfile.TemporaryDirectory() as tmp_dir_two:
            out_two = Path(tmp_dir_two) / "out"
            result_two = _run_cmd(
                [
                    "lifecycle",
                    "examples/momentum_trade.hpl",
                    "--backend",
                    "classical",
                    "--out-dir",
                    str(out_two),
                ]
            )
            self.assertEqual(result_two.returncode, 0)
            summary_two = json.loads(result_two.stdout)
            self.assertEqual(summary_one["bundle_id"], summary_two["bundle_id"])

    def test_lifecycle_qasm_bundle_contains_qasm(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "out"
            result = _run_cmd(
                [
                    "lifecycle",
                    "examples/momentum_trade.hpl",
                    "--backend",
                    "qasm",
                    "--out-dir",
                    str(out_dir),
                ]
            )
            self.assertEqual(result.returncode, 0)
            summary = json.loads(result.stdout)
            bundle_path = Path(summary["bundle_path"])
            manifest = json.loads((bundle_path / "bundle_manifest.json").read_text(encoding="utf-8"))
            roles = {entry["role"] for entry in manifest["artifacts"]}
            self.assertIn("qasm", roles)

    def test_lifecycle_refusal_with_missing_anchor(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "out"
            missing_anchor = out_dir / "missing.anchor.json"
            result = _run_cmd(
                [
                    "lifecycle",
                    "examples/momentum_trade.hpl",
                    "--backend",
                    "classical",
                    "--out-dir",
                    str(out_dir),
                    "--require-epoch",
                    "--anchor",
                    str(missing_anchor),
                ]
            )
            self.assertEqual(result.returncode, 0)
            summary = json.loads(result.stdout)
            self.assertFalse(summary["ok"])
            self.assertTrue(Path(summary["bundle_path"]).exists())

    def test_bundle_quantum_semantics_refusal(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "out"
            program_ir = out_dir / "program.ir.json"
            out_dir.mkdir(parents=True, exist_ok=True)
            program_ir.write_text("{}", encoding="utf-8")

            result = _run_cmd(
                [
                    "bundle",
                    "--out-dir",
                    str(out_dir),
                    "--program-ir",
                    str(program_ir),
                    "--quantum-semantics-v1",
                ]
            )
            self.assertEqual(result.returncode, 0)
            summary = json.loads(result.stdout)
            self.assertFalse(summary["ok"])
            self.assertTrue(summary["errors"])


if __name__ == "__main__":
    unittest.main()
