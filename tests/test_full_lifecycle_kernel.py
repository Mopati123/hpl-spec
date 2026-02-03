import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CLI = [sys.executable, "-m", "hpl.cli"]
pytestmark = pytest.mark.slow


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


class FullLifecycleKernelTests(unittest.TestCase):
    def test_lifecycle_kernel_qasm_bundle_roles(self):
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
                    "--quantum-semantics-v1",
                ]
            )
            self.assertEqual(result.returncode, 0)
            summary = json.loads(result.stdout)
            self.assertTrue(summary["bundle_id"])
            bundle_path = Path(summary["bundle_path"])
            manifest = json.loads((bundle_path / "bundle_manifest.json").read_text(encoding="utf-8"))
            roles = {entry["role"] for entry in manifest["artifacts"]}
            self.assertIn("qasm", roles)
            self.assertIn("execution_token", roles)

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
                    "--quantum-semantics-v1",
                ]
            )
            self.assertEqual(result.returncode, 0)
            summary_two = json.loads(result.stdout)
            self.assertEqual(summary["bundle_id"], summary_two["bundle_id"])

    def test_kernel_refusal_on_backend_disallowed(self):
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
                    "--allowed-backends",
                    "CLASSICAL",
                    "--constraint-inversion-v1",
                ]
            )
            self.assertEqual(result.returncode, 0)
            summary = json.loads(result.stdout)
            self.assertFalse(summary["ok"])
            bundle_path = Path(summary["bundle_path"])
            manifest = json.loads((bundle_path / "bundle_manifest.json").read_text(encoding="utf-8"))
            roles = {entry["role"] for entry in manifest["artifacts"]}
            self.assertIn("constraint_witness", roles)
            self.assertIn("dual_proposal", roles)


if __name__ == "__main__":
    unittest.main()
