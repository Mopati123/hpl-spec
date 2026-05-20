import hashlib
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
DIGEST_FIELDS = ("digest", "hash", "sha256", "leaf_hash")
ANCHOR_FIELDS = (
    "anchor",
    "anchor_commitment",
    "bundle_commitment",
    "commitment",
    "merkle_root",
    "root",
    "root_commitment",
)


def _env():
    env = os.environ.copy()
    src_path = str(ROOT / "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")
    return env


def _run_cli(args):
    return subprocess.run(
        CLI + args,
        cwd=ROOT,
        env=_env(),
        capture_output=True,
        text=True,
    )


def _run_net_shadow(out_dir: Path) -> tuple[dict, Path, bytes]:
    result = _run_cli(
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
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)

    summary = json.loads(result.stdout.strip().splitlines()[-1])
    if not summary.get("ok"):
        raise AssertionError(summary)

    bundle_path = Path(summary["bundle_path"])
    manifest_path = bundle_path / "bundle_manifest.json"
    signature_path = bundle_path / "bundle_manifest.sig"

    if not manifest_path.exists():
        raise AssertionError(f"missing manifest: {manifest_path}")
    if not signature_path.exists():
        raise AssertionError(f"missing manifest signature: {signature_path}")

    ok, errors = bundle_evidence.verify_bundle_manifest_signature(
        manifest_path,
        signature_path,
        TEST_PUB,
    )
    if not ok:
        raise AssertionError(errors)

    manifest_bytes = manifest_path.read_bytes()
    return json.loads(manifest_bytes), bundle_path, manifest_bytes


def _anchor_ready_commitment(manifest: dict, manifest_bytes: bytes) -> str:
    for field in ANCHOR_FIELDS:
        value = manifest.get(field)
        if isinstance(value, str) and value:
            return value
    return "sha256:" + hashlib.sha256(manifest_bytes).hexdigest()


class NetAnchorReadyProofTests(unittest.TestCase):
    def test_net_shadow_signed_bundle_is_anchor_ready_and_stable(self):
        with tempfile.TemporaryDirectory() as tmp_one, tempfile.TemporaryDirectory() as tmp_two:
            manifest_one, bundle_one, bytes_one = _run_net_shadow(Path(tmp_one) / "out")
            manifest_two, _bundle_two, bytes_two = _run_net_shadow(Path(tmp_two) / "out")

            for manifest, bundle_path in ((manifest_one, bundle_one), (manifest_two, _bundle_two)):
                net_lane = manifest.get("net_lane_v1")
                self.assertIsInstance(net_lane, dict)
                self.assertTrue(net_lane["ok"], net_lane)
                self.assertEqual(net_lane["missing_required"], [])

                artifacts = manifest.get("artifacts")
                self.assertIsInstance(artifacts, list)
                self.assertTrue(artifacts)

                manifest_digest_fields = {
                    field
                    for artifact in artifacts
                    if isinstance(artifact, dict)
                    for field in DIGEST_FIELDS
                    if field in artifact
                }
                self.assertTrue(manifest_digest_fields)

                for artifact in artifacts:
                    self.assertIsInstance(artifact, dict)
                    self.assertTrue(artifact.get("role"), artifact)
                    self.assertTrue(
                        any(artifact.get(field) for field in manifest_digest_fields),
                        artifact,
                    )
                    filename = artifact.get("filename")
                    self.assertIsInstance(filename, str)
                    self.assertTrue((bundle_path / filename).exists(), artifact)

                if "bundle_id" in manifest:
                    self.assertTrue(manifest["bundle_id"])

            if "bundle_id" in manifest_one and "bundle_id" in manifest_two:
                self.assertEqual(manifest_one["bundle_id"], manifest_two["bundle_id"])

            self.assertEqual(
                _anchor_ready_commitment(manifest_one, bytes_one),
                _anchor_ready_commitment(manifest_two, bytes_two),
            )


if __name__ == "__main__":
    unittest.main()
