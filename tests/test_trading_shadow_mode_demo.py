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
FIXTURES = ROOT / "tests" / "fixtures" / "trading"
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


class TradingShadowDemoTests(unittest.TestCase):
    def test_trading_shadow_demo_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp_one:
            out_one = Path(tmp_one) / "out"
            result_one = _run_cmd(
                [
                    "demo",
                    "trading-shadow",
                    "--out-dir",
                    str(out_one),
                    "--market-fixture",
                    str(FIXTURES / "price_series_simple.json"),
                    "--policy",
                    str(FIXTURES / "shadow_policy_safe.json"),
                    "--shadow-model",
                    str(FIXTURES / "shadow_model.json"),
                    "--signing-key",
                    str(TEST_KEY),
                ]
            )
            self.assertEqual(result_one.returncode, 0)
            summary_one = json.loads(result_one.stdout)
            self.assertTrue(summary_one["bundle_id"])
            bundle_path_one = Path(summary_one["bundle_path"])
            manifest_one = (bundle_path_one / "bundle_manifest.json").read_bytes()
            sig_path = bundle_path_one / "bundle_manifest.sig"
            self.assertTrue(sig_path.exists())
            ok, errors = bundle_evidence.verify_bundle_manifest_signature(
                bundle_path_one / "bundle_manifest.json",
                sig_path,
                TEST_PUB,
            )
            self.assertTrue(ok, errors)

        with tempfile.TemporaryDirectory() as tmp_two:
            out_two = Path(tmp_two) / "out"
            result_two = _run_cmd(
                [
                    "demo",
                    "trading-shadow",
                    "--out-dir",
                    str(out_two),
                    "--market-fixture",
                    str(FIXTURES / "price_series_simple.json"),
                    "--policy",
                    str(FIXTURES / "shadow_policy_safe.json"),
                    "--shadow-model",
                    str(FIXTURES / "shadow_model.json"),
                    "--signing-key",
                    str(TEST_KEY),
                ]
            )
            self.assertEqual(result_two.returncode, 0)
            summary_two = json.loads(result_two.stdout)
            bundle_path_two = Path(summary_two["bundle_path"])
            manifest_two = (bundle_path_two / "bundle_manifest.json").read_bytes()
            self.assertEqual(manifest_one, manifest_two)

    def test_trading_shadow_demo_refusal(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "out"
            result = _run_cmd(
                [
                    "demo",
                    "trading-shadow",
                    "--out-dir",
                    str(out_dir),
                    "--market-fixture",
                    str(FIXTURES / "price_series_simple.json"),
                    "--policy",
                    str(FIXTURES / "shadow_policy_forbidden.json"),
                    "--shadow-model",
                    str(FIXTURES / "shadow_model.json"),
                    "--signing-key",
                    str(TEST_KEY),
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
