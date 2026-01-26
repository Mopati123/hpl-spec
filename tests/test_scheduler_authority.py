import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from hpl import scheduler

TOOLS_DIR = ROOT / "tools"
ANCHOR_SPEC = importlib.util.spec_from_file_location("anchor_epoch", TOOLS_DIR / "anchor_epoch.py")
anchor_epoch = importlib.util.module_from_spec(ANCHOR_SPEC)
ANCHOR_SPEC.loader.exec_module(anchor_epoch)

SIGN_SPEC = importlib.util.spec_from_file_location("sign_anchor", TOOLS_DIR / "sign_anchor.py")
sign_anchor = importlib.util.module_from_spec(SIGN_SPEC)
SIGN_SPEC.loader.exec_module(sign_anchor)

FIXTURES = ROOT / "tests" / "fixtures" / "keys"
TEST_PRIVATE_KEY = FIXTURES / "ci_ed25519_test.sk"
TEST_PUBLIC_KEY = FIXTURES / "ci_ed25519_test.pub"


def _sample_program_ir():
    return {
        "program_id": "test_program",
        "hamiltonian": {
            "terms": [
                {"operator_id": "SURF_A", "cls": "C", "coefficient": 1.0},
                {"operator_id": "SURF_B", "cls": "C", "coefficient": 2.0},
            ]
        },
        "operators": {
            "SURF_A": {"type": "unspecified", "commutes_with": [], "backend_map": []},
            "SURF_B": {"type": "unspecified", "commutes_with": [], "backend_map": []},
        },
        "invariants": [],
        "scheduler": {"collapse_policy": "unspecified", "authorized_observers": []},
    }


class SchedulerAuthorityTests(unittest.TestCase):
    def test_plan_determinism(self):
        program_ir = _sample_program_ir()
        ctx = scheduler.SchedulerContext()
        plan_one = scheduler.plan(program_ir, ctx)
        plan_two = scheduler.plan(program_ir, ctx)
        self.assertEqual(plan_one.to_dict(), plan_two.to_dict())
        self.assertEqual(plan_one.plan_id, plan_two.plan_id)

    def test_epoch_verification_denied(self):
        program_ir = _sample_program_ir()
        ctx = scheduler.SchedulerContext(require_epoch_verification=True)
        with mock.patch("hpl.scheduler._verify_epoch_and_signature") as mock_verify:
            mock_verify.return_value = ({"anchor_ok": False, "signature_ok": False}, ["epoch fail"])
            plan = scheduler.plan(program_ir, ctx)

        self.assertEqual(plan.status, "denied")
        self.assertTrue(any("epoch fail" in reason for reason in plan.reasons))

    def test_epoch_verification_success(self):
        program_ir = _sample_program_ir()
        anchor = anchor_epoch.build_epoch_anchor(
            epoch_id="test-epoch",
            timestamp="1970-01-01T00:00:00Z",
            git_commit="test",
            root=ROOT,
            emit_witness=False,
        )

        with tempfile.TemporaryDirectory() as tmp:
            anchor_path = Path(tmp) / "anchor.json"
            anchor_path.write_text(json.dumps(anchor, sort_keys=True), encoding="utf-8")

            signing_key = sign_anchor._load_signing_key(TEST_PRIVATE_KEY, "UNUSED")
            signature_bytes = sign_anchor.sign_anchor_file(anchor_path, signing_key)
            signature_path = Path(tmp) / "anchor.sig"
            signature_path.write_text(signature_bytes.hex(), encoding="utf-8")

            ctx = scheduler.SchedulerContext(
                require_epoch_verification=True,
                anchor_path=anchor_path,
                signature_path=signature_path,
                public_key_path=TEST_PUBLIC_KEY,
                git_commit_override="test",
            )
            plan = scheduler.plan(program_ir, ctx)

        self.assertEqual(plan.status, "planned")
        self.assertEqual(plan.reasons, [])
        self.assertIsNotNone(plan.verification)
        self.assertTrue(plan.verification.get("anchor_ok"))
        self.assertTrue(plan.verification.get("signature_ok"))

    def test_witness_records_present(self):
        program_ir = _sample_program_ir()
        ctx = scheduler.SchedulerContext()
        plan = scheduler.plan(program_ir, ctx)
        self.assertTrue(plan.witness_records)


if __name__ == "__main__":
    unittest.main()
