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


class EcmoAutoTrackLifecycleTests(unittest.TestCase):
    def test_ecmo_track_publish(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "out"
            result = _run_cmd(
                [
                    "lifecycle",
                    "examples/momentum_trade.hpl",
                    "--backend",
                    "classical",
                    "--out-dir",
                    str(out_dir),
                    "--ecmo",
                    "tests/fixtures/ecmo_boundary_ci.json",
                ]
            )
            self.assertEqual(result.returncode, 0)
            summary = json.loads(result.stdout)
            self.assertTrue(summary["ok"])
            bundle_path = Path(summary["bundle_path"])
            roles = {entry["role"] for entry in json.loads((bundle_path / "bundle_manifest.json").read_text(encoding="utf-8"))["artifacts"]}
            self.assertIn("measurement_selection", roles)

    def test_ecmo_track_regulator_refusal(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "out"
            result = _run_cmd(
                [
                    "lifecycle",
                    "examples/momentum_trade.hpl",
                    "--backend",
                    "classical",
                    "--out-dir",
                    str(out_dir),
                    "--ecmo",
                    "tests/fixtures/ecmo_boundary_regulator.json",
                    "--constraint-inversion-v1",
                ]
            )
            self.assertEqual(result.returncode, 0)
            summary = json.loads(result.stdout)
            self.assertFalse(summary["ok"])
            bundle_path = Path(summary["bundle_path"])
            roles = {entry["role"] for entry in json.loads((bundle_path / "bundle_manifest.json").read_text(encoding="utf-8"))["artifacts"]}
            self.assertIn("constraint_witness", roles)
            self.assertIn("dual_proposal", roles)

    def test_ecmo_track_ambiguous_refusal(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "out"
            result = _run_cmd(
                [
                    "lifecycle",
                    "examples/momentum_trade.hpl",
                    "--backend",
                    "classical",
                    "--out-dir",
                    str(out_dir),
                    "--ecmo",
                    "tests/fixtures/ecmo_boundary_ambiguous.json",
                    "--constraint-inversion-v1",
                ]
            )
            self.assertEqual(result.returncode, 0)
            summary = json.loads(result.stdout)
            self.assertFalse(summary["ok"])
            bundle_path = Path(summary["bundle_path"])
            roles = {entry["role"] for entry in json.loads((bundle_path / "bundle_manifest.json").read_text(encoding="utf-8"))["artifacts"]}
            self.assertIn("constraint_witness", roles)
            self.assertIn("dual_proposal", roles)
