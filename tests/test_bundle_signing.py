import json
import tempfile
import unittest
from pathlib import Path

from tools import bundle_evidence


ROOT = Path(__file__).resolve().parents[1]
TEST_KEYS = ROOT / "tests" / "fixtures" / "keys"
TEST_PRIVATE_KEY = TEST_KEYS / "ci_ed25519_test.sk"
TEST_PUBLIC_KEY = TEST_KEYS / "ci_ed25519_test.pub"
CI_PUBLIC_KEY = ROOT / "config" / "keys" / "ci_ed25519.pub"


class BundleSigningTests(unittest.TestCase):
    def _create_manifest(self, tmp: Path) -> Path:
        artifact_path = tmp / "artifact.txt"
        artifact_path.write_text("payload", encoding="utf-8")
        artifacts = [bundle_evidence._artifact("program_ir", artifact_path)]
        bundle_dir, manifest = bundle_evidence.build_bundle(
            out_dir=tmp,
            artifacts=artifacts,
            epoch_anchor=None,
            epoch_sig=None,
            public_key=TEST_PUBLIC_KEY,
        )
        manifest_path = bundle_dir / "bundle_manifest.json"
        manifest_path.write_text(bundle_evidence._canonical_json(manifest), encoding="utf-8")
        return manifest_path

    def test_signature_determinism(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            manifest_path = self._create_manifest(tmp)
            sig_one = bundle_evidence.sign_bundle_manifest(manifest_path, TEST_PRIVATE_KEY)
            sig_one_bytes = sig_one.read_text(encoding="utf-8")
            sig_two = bundle_evidence.sign_bundle_manifest(manifest_path, TEST_PRIVATE_KEY)
            sig_two_bytes = sig_two.read_text(encoding="utf-8")
            self.assertEqual(sig_one_bytes, sig_two_bytes)

    def test_tamper_detection(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            manifest_path = self._create_manifest(tmp)
            sig_path = bundle_evidence.sign_bundle_manifest(manifest_path, TEST_PRIVATE_KEY)
            original = manifest_path.read_text(encoding="utf-8")
            manifest_path.write_text(original + " ", encoding="utf-8")
            ok, errors = bundle_evidence.verify_bundle_manifest_signature(
                manifest_path,
                sig_path,
                TEST_PUBLIC_KEY,
            )
            self.assertFalse(ok)
            self.assertTrue(errors)

    def test_wrong_public_key(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            manifest_path = self._create_manifest(tmp)
            sig_path = bundle_evidence.sign_bundle_manifest(manifest_path, TEST_PRIVATE_KEY)
            ok, errors = bundle_evidence.verify_bundle_manifest_signature(
                manifest_path,
                sig_path,
                CI_PUBLIC_KEY,
            )
            self.assertFalse(ok)
            self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
