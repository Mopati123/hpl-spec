import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools import bundle_evidence


ROOT = Path(__file__).resolve().parents[1]
CLI = [sys.executable, "-m", "hpl.cli"]
TEST_KEY = ROOT / "tests" / "fixtures" / "keys" / "ci_ed25519_test.sk"
TEST_PUB = ROOT / "tests" / "fixtures" / "keys" / "ci_ed25519_test.pub"


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


class NetSignedBundleProofTests(unittest.TestCase):
    def test_net_shadow_cli_produces_verified_signed_bundle(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "net_shadow_out"
            result = _run_cmd(
                [
                    "demo",
                    "net-shadow",
                    "--out-dir",
                    str(out_dir),
                    "--input",
                    "examples/momentum_trade.hpl",
                    "--endpoint",
                    "net://demo",
                    "--message",
                    "hello",
                    "--enable-net",
                    "--signing-key",
                    str(TEST_KEY),
                    "--pub",
                    str(TEST_PUB),
                ]
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout.strip().splitlines()[-1])
            self.assertTrue(summary["ok"], summary)

            bundle_path = Path(summary["bundle_path"])
            manifest_path = bundle_path / "bundle_manifest.json"
            signature_path = bundle_path / "bundle_manifest.sig"

            self.assertTrue(manifest_path.exists())
            self.assertTrue(signature_path.exists())

            ok, errors = bundle_evidence.verify_bundle_manifest_signature(
                manifest_path,
                signature_path,
                TEST_PUB,
            )
            self.assertTrue(ok, errors)

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertIn("net_lane_v1", manifest)
            self.assertTrue(manifest["net_lane_v1"]["ok"], manifest["net_lane_v1"])
            self.assertEqual(manifest["net_lane_v1"]["missing_required"], [])


if __name__ == "__main__":
    unittest.main()
