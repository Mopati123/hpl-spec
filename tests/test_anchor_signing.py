import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"

SIGN_SPEC = importlib.util.spec_from_file_location("sign_anchor", TOOLS_DIR / "sign_anchor.py")
sign_anchor = importlib.util.module_from_spec(SIGN_SPEC)
SIGN_SPEC.loader.exec_module(sign_anchor)

VERIFY_SPEC = importlib.util.spec_from_file_location(
    "verify_anchor_signature", TOOLS_DIR / "verify_anchor_signature.py"
)
verify_anchor_signature = importlib.util.module_from_spec(VERIFY_SPEC)
VERIFY_SPEC.loader.exec_module(verify_anchor_signature)

FIXTURES = ROOT / "tests" / "fixtures" / "keys"
PRIVATE_KEY = FIXTURES / "ci_ed25519_test.sk"
PUBLIC_KEY = FIXTURES / "ci_ed25519_test.pub"


class AnchorSigningTests(unittest.TestCase):
    def test_sign_and_verify_deterministic(self):
        anchor_payload = b"{\"epoch_id\":\"test\",\"timestamp_utc\":\"1970-01-01T00:00:00Z\"}"

        with tempfile.TemporaryDirectory() as tmp:
            anchor_path = Path(tmp) / "anchor.json"
            anchor_path.write_bytes(anchor_payload)

            signing_key = sign_anchor._load_signing_key(PRIVATE_KEY, "UNUSED")
            verify_key = verify_anchor_signature._load_verify_key(PUBLIC_KEY, "UNUSED")

            signature_one = sign_anchor.sign_anchor_file(anchor_path, signing_key)
            signature_two = sign_anchor.sign_anchor_file(anchor_path, signing_key)

            self.assertEqual(signature_one, signature_two)

            signature_path = Path(tmp) / "anchor.sig"
            signature_path.write_text(signature_one.hex(), encoding="utf-8")

            ok, errors = verify_anchor_signature.verify_anchor_signature(
                anchor_path, signature_path, verify_key
            )
            self.assertTrue(ok)
            self.assertEqual(errors, [])

    def test_invalid_signature_fails(self):
        anchor_payload = b"{\"epoch_id\":\"test\",\"timestamp_utc\":\"1970-01-01T00:00:00Z\"}"

        with tempfile.TemporaryDirectory() as tmp:
            anchor_path = Path(tmp) / "anchor.json"
            anchor_path.write_bytes(anchor_payload)

            verify_key = verify_anchor_signature._load_verify_key(PUBLIC_KEY, "UNUSED")

            signature_path = Path(tmp) / "anchor.sig"
            signature_path.write_text("00" * 64, encoding="utf-8")

            ok, errors = verify_anchor_signature.verify_anchor_signature(
                anchor_path, signature_path, verify_key
            )
            self.assertFalse(ok)
            self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
