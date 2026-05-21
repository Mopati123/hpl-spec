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


def _assert_repo_paths_clean(testcase: unittest.TestCase):
    result = subprocess.run(
        ["git", "diff", "--name-only", "--", "src/hpl/runtime", "docs", "AGENTS.md"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    testcase.assertEqual("", result.stdout.strip(), result.stdout)


class NetRefusalBundleSignatureProofTests(unittest.TestCase):
    def _run_bad_signature_refusal(self, tmp_path: Path, run_name: str) -> dict:
        anchor_path = tmp_path / f"{run_name}.epoch.anchor.json"
        valid_anchor_sig_path = tmp_path / f"{run_name}.epoch.anchor.valid.sig"
        bad_anchor_sig_path = tmp_path / f"{run_name}.epoch.anchor.bad.sig"
        out_dir = tmp_path / f"{run_name}_net_shadow_out"

        anchor = anchor_epoch.build_epoch_anchor(
            epoch_id="net-n11-refusal-bundle-signature-proof",
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
        valid_signature = sign_anchor.sign_anchor_file(anchor_path, signing_key)
        valid_anchor_sig_path.write_text(valid_signature.hex(), encoding="utf-8")

        bad_signature = bytearray(valid_signature)
        bad_signature[0] ^= 0x01
        bad_anchor_sig_path.write_text(bytes(bad_signature).hex(), encoding="utf-8")

        verify_key = verify_anchor_signature._load_verify_key(TEST_PUB, "UNUSED")
        sig_ok, sig_errors = verify_anchor_signature.verify_anchor_signature(
            anchor_path,
            bad_anchor_sig_path,
            verify_key,
        )
        self.assertFalse(sig_ok)
        self.assertIn("signature verification failed", sig_errors)

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
                str(bad_anchor_sig_path),
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

        self.assertFalse(summary["ok"], summary)
        self.assertEqual("refusal", summary.get("denied_reason"), summary)

        error_text = " ".join(
            [result.stdout, result.stderr, _canonical_json(summary.get("errors", []))]
        ).lower()
        self.assertIn("signature", error_text)
        self.assertIn("verification", error_text)

        bundle_path = summary.get("bundle_path")
        self.assertTrue(bundle_path, summary)
        bundle_dir = Path(bundle_path)
        manifest_path = bundle_dir / "bundle_manifest.json"
        bundle_sig_path = bundle_dir / "bundle_manifest.sig"
        self.assertTrue(manifest_path.exists(), summary)
        self.assertTrue(bundle_sig_path.exists(), summary)

        bundle_sig_ok, bundle_sig_errors = bundle_evidence.verify_bundle_manifest_signature(
            manifest_path,
            bundle_sig_path,
            TEST_PUB,
        )
        self.assertTrue(bundle_sig_ok, bundle_sig_errors)

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        verification = manifest.get("verification")
        self.assertIsInstance(verification, dict, manifest)
        self.assertTrue(verification["epoch_ok"], verification)
        self.assertFalse(verification["signature_ok"], verification)
        self.assertIn(
            "signature verification failed",
            " ".join(verification.get("signature_errors", [])),
        )

        plan_path = bundle_dir / "plan_plan.json"
        runtime_path = bundle_dir / "runtime_result_runtime.json"
        if plan_path.exists():
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            self.assertNotEqual("completed", plan.get("status"), plan)
            self.assertFalse(plan["verification"]["signature_ok"], plan)

        if runtime_path.exists():
            runtime_result = json.loads(runtime_path.read_text(encoding="utf-8"))
            self.assertNotEqual("completed", runtime_result["status"], runtime_result)

        net_lane = manifest.get("net_lane_v1")
        if isinstance(net_lane, dict) and net_lane.get("ok") is True:
            self.assertFalse(summary["ok"], summary)
            self.assertFalse(verification["signature_ok"], verification)
        else:
            self.assertFalse(summary["ok"], summary)
            self.assertFalse(
                bool(net_lane.get("ok")) if isinstance(net_lane, dict) else False
            )

        return {
            "summary": summary,
            "manifest": manifest,
            "verification": verification,
            "bundle_signature_verified": bundle_sig_ok,
        }

    @staticmethod
    def _stable_refusal_shape(run: dict) -> dict:
        summary = run["summary"]
        verification = run["verification"]
        manifest = run["manifest"]
        net_lane = manifest.get("net_lane_v1")
        return {
            "summary_ok": summary.get("ok"),
            "summary_denied_reason": summary.get("denied_reason"),
            "summary_errors": summary.get("errors", []),
            "has_bundle_path": bool(summary.get("bundle_path")),
            "verification_epoch_ok": verification.get("epoch_ok"),
            "verification_signature_ok": verification.get("signature_ok"),
            "verification_signature_errors": verification.get("signature_errors", []),
            "bundle_signature_verified": run["bundle_signature_verified"],
            "net_lane_present": isinstance(net_lane, dict),
            "net_lane_ok": net_lane.get("ok") if isinstance(net_lane, dict) else None,
            "net_lane_missing_required": (
                net_lane.get("missing_required") if isinstance(net_lane, dict) else None
            ),
        }

    def test_net_shadow_refusal_bundle_signature_is_verifiable_and_deterministic(self):
        _assert_repo_paths_clean(self)

        with tempfile.TemporaryDirectory() as first_tmp, tempfile.TemporaryDirectory() as second_tmp:
            first = self._run_bad_signature_refusal(Path(first_tmp), "first")
            second = self._run_bad_signature_refusal(Path(second_tmp), "second")

        self.assertFalse(first["summary"]["ok"], first["summary"])
        self.assertFalse(second["summary"]["ok"], second["summary"])
        self.assertTrue(first["verification"]["epoch_ok"], first["verification"])
        self.assertTrue(second["verification"]["epoch_ok"], second["verification"])
        self.assertFalse(first["verification"]["signature_ok"], first["verification"])
        self.assertFalse(second["verification"]["signature_ok"], second["verification"])
        self.assertTrue(first["bundle_signature_verified"])
        self.assertTrue(second["bundle_signature_verified"])
        self.assertEqual(
            self._stable_refusal_shape(first),
            self._stable_refusal_shape(second),
        )

        _assert_repo_paths_clean(self)


if __name__ == "__main__":
    unittest.main()
