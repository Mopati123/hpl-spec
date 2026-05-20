import importlib.util
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


def _load_tool(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


anchor_epoch = _load_tool("anchor_epoch", ROOT / "tools" / "anchor_epoch.py")
sign_anchor = _load_tool("sign_anchor", ROOT / "tools" / "sign_anchor.py")
verify_anchor_signature = _load_tool(
    "verify_anchor_signature",
    ROOT / "tools" / "verify_anchor_signature.py",
)
verify_epoch = _load_tool("verify_epoch", ROOT / "tools" / "verify_epoch.py")


def _env():
    env = os.environ.copy()
    src_path = str(ROOT / "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")
    return env


def _canonical_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


class NetEpochAnchorVerificationProofTests(unittest.TestCase):
    def test_net_shadow_requires_verified_epoch_anchor_and_signed_bundle(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            anchor_path = tmp_path / "epoch.anchor.json"
            anchor_sig_path = tmp_path / "epoch.anchor.sig"
            out_dir = tmp_path / "net_shadow_out"

            anchor = anchor_epoch.build_epoch_anchor(
                epoch_id="net-n8-epoch-anchor-verification-proof",
                timestamp="2026-05-20T00:00:00Z",
                git_commit=None,
                root=ROOT,
                emit_witness=False,
            )
            anchor_path.write_text(_canonical_json(anchor), encoding="utf-8")

            epoch_ok, epoch_errors = verify_epoch.verify_epoch_anchor(
                anchor,
                root=ROOT,
                git_commit_override=str(anchor["git_commit"]),
            )
            self.assertTrue(epoch_ok, epoch_errors)

            signing_key = sign_anchor._load_signing_key(TEST_KEY, "UNUSED")
            anchor_sig_path.write_text(
                sign_anchor.sign_anchor_file(anchor_path, signing_key).hex(),
                encoding="utf-8",
            )

            verify_key = verify_anchor_signature._load_verify_key(TEST_PUB, "UNUSED")
            sig_ok, sig_errors = verify_anchor_signature.verify_anchor_signature(
                anchor_path,
                anchor_sig_path,
                verify_key,
            )
            self.assertTrue(sig_ok, sig_errors)

            result = subprocess.run(
                CLI
                + [
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
                    "--require-epoch",
                    "--anchor",
                    str(anchor_path),
                    "--sig",
                    str(anchor_sig_path),
                    "--pub",
                    str(TEST_PUB),
                    "--signing-key",
                    str(TEST_KEY),
                    "--enable-net",
                ],
                cwd=ROOT,
                env=_env(),
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout.strip().splitlines()[-1])
            self.assertTrue(summary["ok"], summary)

            bundle_path = Path(summary["bundle_path"])
            manifest_path = bundle_path / "bundle_manifest.json"
            bundle_sig_path = bundle_path / "bundle_manifest.sig"
            plan_path = bundle_path / "plan_plan.json"
            runtime_path = bundle_path / "runtime_result_runtime.json"

            self.assertTrue(manifest_path.exists())
            self.assertTrue(bundle_sig_path.exists())

            bundle_sig_ok, bundle_sig_errors = bundle_evidence.verify_bundle_manifest_signature(
                manifest_path,
                bundle_sig_path,
                TEST_PUB,
            )
            self.assertTrue(bundle_sig_ok, bundle_sig_errors)

            runtime_result = json.loads(runtime_path.read_text(encoding="utf-8"))
            self.assertEqual(runtime_result["status"], "completed", runtime_result)

            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            self.assertEqual(plan["status"], "planned", plan)
            self.assertTrue(plan["verification"]["anchor_ok"], plan)
            self.assertTrue(plan["verification"]["signature_ok"], plan)

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertTrue(manifest["verification"]["epoch_ok"], manifest)
            self.assertTrue(manifest["verification"]["signature_ok"], manifest)

            net_lane = manifest.get("net_lane_v1")
            self.assertIsInstance(net_lane, dict)
            self.assertTrue(net_lane["ok"], net_lane)
            self.assertEqual(net_lane["missing_required"], [])


if __name__ == "__main__":
    unittest.main()
