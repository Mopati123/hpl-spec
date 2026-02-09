import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

from tools import bundle_evidence

ROOT = Path(__file__).resolve().parents[1]
CLI = [sys.executable, "-m", "hpl.cli"]
TEST_KEY = ROOT / "tests" / "fixtures" / "keys" / "ci_ed25519_test.sk"
TEST_PUB = ROOT / "tests" / "fixtures" / "keys" / "ci_ed25519_test.pub"
pytestmark = pytest.mark.slow


def _env():
    env = os.environ.copy()
    src_path = str(ROOT / "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")
    env["HPL_IO_ENABLED"] = "1"
    env["HPL_IO_ADAPTER"] = "mock"
    env["HPL_IO_ADAPTER_READY"] = "1"
    return env


def _run_cmd(args):
    return subprocess.run(
        CLI + args,
        cwd=ROOT,
        env=_env(),
        capture_output=True,
        text=True,
    )


class TradingIoDemoTests(unittest.TestCase):
    def test_trading_io_shadow_demo(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "out"
            result = _run_cmd(
                [
                    "demo",
                    "trading-io-shadow",
                    "--out-dir",
                    str(out_dir),
                    "--signing-key",
                    str(TEST_KEY),
                    "--enable-io",
                ]
            )
            self.assertEqual(result.returncode, 0)
            summary = json.loads(result.stdout)
            self.assertTrue(summary["bundle_id"])
            bundle_path = Path(summary["bundle_path"])
            manifest = json.loads((bundle_path / "bundle_manifest.json").read_text(encoding="utf-8"))
            self.assertIn("io_lane_v1", manifest)
            self.assertTrue(manifest["io_lane_v1"]["ok"], manifest["io_lane_v1"])
            ok, errors = bundle_evidence.verify_bundle_manifest_signature(
                bundle_path / "bundle_manifest.json",
                bundle_path / "bundle_manifest.sig",
                TEST_PUB,
            )
            self.assertTrue(ok, errors)

    def test_trading_io_live_min_demo(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "out"
            result = _run_cmd(
                [
                    "demo",
                    "trading-io-live-min",
                    "--out-dir",
                    str(out_dir),
                    "--signing-key",
                    str(TEST_KEY),
                    "--enable-io",
                ]
            )
            self.assertEqual(result.returncode, 0)
            summary = json.loads(result.stdout)
            self.assertTrue(summary["bundle_id"])
            bundle_path = Path(summary["bundle_path"])
            manifest = json.loads((bundle_path / "bundle_manifest.json").read_text(encoding="utf-8"))
            self.assertIn("io_lane_v1", manifest)
            self.assertTrue(manifest["io_lane_v1"]["ok"], manifest["io_lane_v1"])
            ok, errors = bundle_evidence.verify_bundle_manifest_signature(
                bundle_path / "bundle_manifest.json",
                bundle_path / "bundle_manifest.sig",
                TEST_PUB,
            )
            self.assertTrue(ok, errors)

    def test_trading_io_live_min_refuses_without_live_mode(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "out"
            result = _run_cmd(
                [
                    "demo",
                    "trading-io-live-min",
                    "--out-dir",
                    str(out_dir),
                    "--signing-key",
                    str(TEST_KEY),
                    "--enable-io",
                    "--io-mode",
                    "dry_run",
                ]
            )
            self.assertEqual(result.returncode, 0)
            summary = json.loads(result.stdout)
            self.assertFalse(summary["ok"])
            self.assertTrue(any("io_mode not live" in err for err in summary["errors"]))
            bundle_path = Path(summary["bundle_path"])
            manifest_path = bundle_path / "bundle_manifest.json"
            self.assertTrue(manifest_path.exists())
            ok, errors = bundle_evidence.verify_bundle_manifest_signature(
                manifest_path,
                bundle_path / "bundle_manifest.sig",
                TEST_PUB,
            )
            self.assertTrue(ok, errors)


if __name__ == "__main__":
    unittest.main()
