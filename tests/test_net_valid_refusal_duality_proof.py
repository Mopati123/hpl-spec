import hashlib
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
COMMITMENT_FIELDS = ("anchor", "commitment", "root", "merkle_root")
CONTRACT_KEYS = {
    "summary_ok",
    "has_bundle_path",
    "manifest_exists",
    "bundle_signature_verified",
    "verification_epoch_ok",
    "verification_signature_ok",
    "commitment_present",
    "net_lane_present",
}


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


def _anchor_ready_commitment(manifest: dict, manifest_bytes: bytes) -> str:
    for field in COMMITMENT_FIELDS:
        value = manifest.get(field)
        if isinstance(value, str) and value:
            return value
    return f"sha256:{hashlib.sha256(manifest_bytes).hexdigest()}"


class NetValidRefusalDualityProofTests(unittest.TestCase):
    def _write_epoch_anchor_and_signature(
        self,
        tmp_path: Path,
        *,
        epoch_id: str,
        corrupt_signature: bool,
    ) -> tuple[Path, Path]:
        anchor_path = tmp_path / f"{epoch_id}.anchor.json"
        anchor_sig_path = tmp_path / f"{epoch_id}.anchor.sig"

        anchor = anchor_epoch.build_epoch_anchor(
            epoch_id=epoch_id,
            timestamp="2026-05-21T00:00:00Z",
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
        signature = sign_anchor.sign_anchor_file(anchor_path, signing_key)
        if corrupt_signature:
            signature = bytes([signature[0] ^ 0x01]) + signature[1:]
        anchor_sig_path.write_text(signature.hex(), encoding="utf-8")

        verify_key = verify_anchor_signature._load_verify_key(TEST_PUB, "UNUSED")
        sig_ok, sig_errors = verify_anchor_signature.verify_anchor_signature(
            anchor_path,
            anchor_sig_path,
            verify_key,
        )
        if corrupt_signature:
            self.assertFalse(sig_ok)
            self.assertIn("signature verification failed", sig_errors)
        else:
            self.assertTrue(sig_ok, sig_errors)

        return anchor_path, anchor_sig_path

    def _run_net_shadow_authority_path(
        self,
        tmp_path: Path,
        *,
        label: str,
        corrupt_signature: bool,
    ) -> dict:
        anchor_path, anchor_sig_path = self._write_epoch_anchor_and_signature(
            tmp_path,
            epoch_id=f"net-n13-{label}-duality-proof",
            corrupt_signature=corrupt_signature,
        )
        out_dir = tmp_path / f"{label}_net_shadow_out"

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

        output = result.stdout.strip().splitlines()
        self.assertTrue(output, result.stderr)
        summary = json.loads(output[-1])

        bundle_path_value = summary.get("bundle_path")
        bundle_path = Path(bundle_path_value) if bundle_path_value else None
        manifest_path = bundle_path / "bundle_manifest.json" if bundle_path else None
        bundle_sig_path = bundle_path / "bundle_manifest.sig" if bundle_path else None

        manifest_exists = bool(manifest_path and manifest_path.exists())
        bundle_signature_verified = False
        manifest = {}
        manifest_bytes = b""
        verification = {}
        commitment = None

        if manifest_exists:
            self.assertTrue(bundle_sig_path.exists(), summary)
            bundle_signature_verified, bundle_sig_errors = (
                bundle_evidence.verify_bundle_manifest_signature(
                    manifest_path,
                    bundle_sig_path,
                    TEST_PUB,
                )
            )
            self.assertTrue(bundle_signature_verified, bundle_sig_errors)

            manifest_bytes = manifest_path.read_bytes()
            manifest = json.loads(manifest_bytes)
            verification = manifest.get("verification", {})
            self.assertIsInstance(verification, dict, manifest)
            commitment = _anchor_ready_commitment(manifest, manifest_bytes)

        runtime = None
        if bundle_path:
            runtime_path = bundle_path / "runtime_result_runtime.json"
            if runtime_path.exists():
                runtime = json.loads(runtime_path.read_text(encoding="utf-8"))

        net_lane = manifest.get("net_lane_v1") if manifest else None
        contract = {
            "summary_ok": summary.get("ok"),
            "has_bundle_path": bool(bundle_path_value),
            "manifest_exists": manifest_exists,
            "bundle_signature_verified": bundle_signature_verified,
            "verification_epoch_ok": verification.get("epoch_ok"),
            "verification_signature_ok": verification.get("signature_ok"),
            "commitment_present": bool(commitment),
            "net_lane_present": isinstance(net_lane, dict),
        }

        return {
            "summary": summary,
            "manifest": manifest,
            "verification": verification,
            "runtime": runtime,
            "net_lane": net_lane,
            "contract": contract,
            "commitment": commitment,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    def test_net_shadow_valid_and_refusal_paths_share_evidence_contract_shape(self):
        with tempfile.TemporaryDirectory() as valid_tmp, tempfile.TemporaryDirectory() as refusal_tmp:
            valid = self._run_net_shadow_authority_path(
                Path(valid_tmp),
                label="valid",
                corrupt_signature=False,
            )
            refusal = self._run_net_shadow_authority_path(
                Path(refusal_tmp),
                label="refusal",
                corrupt_signature=True,
            )

        self.assertEqual(0, valid["returncode"], valid["stderr"])
        self.assertTrue(valid["summary"]["ok"], valid["summary"])
        self.assertIsInstance(valid["runtime"], dict, valid["summary"])
        self.assertEqual("completed", valid["runtime"]["status"], valid["runtime"])
        self.assertTrue(valid["contract"]["manifest_exists"], valid["summary"])
        self.assertTrue(valid["contract"]["bundle_signature_verified"])
        self.assertTrue(valid["verification"]["epoch_ok"], valid["verification"])
        self.assertTrue(valid["verification"]["signature_ok"], valid["verification"])
        self.assertIsInstance(valid["net_lane"], dict, valid["manifest"])
        self.assertTrue(valid["net_lane"]["ok"], valid["net_lane"])
        self.assertEqual([], valid["net_lane"]["missing_required"])

        self.assertFalse(refusal["summary"]["ok"], refusal["summary"])
        self.assertEqual("refusal", refusal["summary"].get("denied_reason"), refusal["summary"])
        self.assertTrue(refusal["contract"]["has_bundle_path"], refusal["summary"])
        self.assertTrue(refusal["contract"]["manifest_exists"], refusal["summary"])
        self.assertTrue(refusal["contract"]["bundle_signature_verified"])
        self.assertTrue(refusal["verification"]["epoch_ok"], refusal["verification"])
        self.assertFalse(refusal["verification"]["signature_ok"], refusal["verification"])
        if refusal["runtime"] is not None:
            self.assertNotEqual("completed", refusal["runtime"]["status"], refusal["runtime"])
        if isinstance(refusal["net_lane"], dict):
            self.assertFalse(
                refusal["summary"]["ok"] and refusal["net_lane"].get("ok") is True,
                refusal["net_lane"],
            )

        self.assertEqual(CONTRACT_KEYS, set(valid["contract"]))
        self.assertEqual(CONTRACT_KEYS, set(refusal["contract"]))
        self.assertEqual(
            {key for key, value in valid["contract"].items() if value is not None},
            {key for key, value in refusal["contract"].items() if value is not None},
        )

        self.assertTrue(valid["contract"]["summary_ok"])
        self.assertFalse(refusal["contract"]["summary_ok"])
        self.assertTrue(valid["contract"]["verification_signature_ok"])
        self.assertFalse(refusal["contract"]["verification_signature_ok"])
        self.assertTrue(valid["contract"]["commitment_present"])
        self.assertTrue(refusal["contract"]["commitment_present"])
        self.assertTrue(valid["commitment"])
        self.assertTrue(refusal["commitment"])


if __name__ == "__main__":
    unittest.main()
