import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from hpl.backends.classical_lowering import lower_program_ir_to_backend_ir
from hpl.backends.qasm_lowering import lower_backend_ir_to_qasm
from hpl.runtime.contracts import ExecutionContract
from hpl.runtime.context import RuntimeContext
from hpl.runtime.engine import RuntimeEngine
from hpl import scheduler
from tools import anchor_epoch
from tools import sign_anchor
from tools import bundle_evidence


FIXTURE = ROOT / "tests" / "fixtures" / "program_ir_minimal.json"
KEY_FIXTURES = ROOT / "tests" / "fixtures" / "keys"
TEST_PRIVATE_KEY = KEY_FIXTURES / "ci_ed25519_test.sk"
TEST_PUBLIC_KEY = KEY_FIXTURES / "ci_ed25519_test.pub"


def _git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")), encoding="utf-8")


class EvidenceBundleTests(unittest.TestCase):
    def test_bundle_determinism_and_verification(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)

            program_ir = json.loads(FIXTURE.read_text(encoding="utf-8"))
            program_ir_path = tmp / "program.ir.json"
            _write_json(program_ir_path, program_ir)

            plan = scheduler.plan(program_ir, scheduler.SchedulerContext())
            plan_path = tmp / "plan.json"
            _write_json(plan_path, plan.to_dict())
            token_path = tmp / "execution_token.json"
            _write_json(token_path, plan.to_dict().get("execution_token", {}))

            contract = ExecutionContract(allowed_steps={step["operator_id"] for step in plan.steps})
            runtime_result = RuntimeEngine().run(plan.to_dict(), RuntimeContext(), contract)
            runtime_path = tmp / "runtime.json"
            _write_json(runtime_path, runtime_result.to_dict())

            backend_ir = lower_program_ir_to_backend_ir(program_ir).to_dict()
            backend_ir_path = tmp / "backend.json"
            _write_json(backend_ir_path, backend_ir)

            qasm_path = tmp / "program.qasm"
            qasm_path.write_text(lower_backend_ir_to_qasm(backend_ir), encoding="utf-8")

            git_commit = _git_commit()
            anchor = anchor_epoch.build_epoch_anchor(
                epoch_id="bundle-test",
                timestamp="1970-01-01T00:00:00Z",
                git_commit=git_commit,
                root=ROOT,
                emit_witness=False,
            )
            anchor_path = tmp / "epoch.anchor.json"
            _write_json(anchor_path, anchor)

            signing_key = sign_anchor._load_signing_key(TEST_PRIVATE_KEY, "UNUSED")
            signature_bytes = sign_anchor.sign_anchor_file(anchor_path, signing_key)
            sig_path = tmp / "epoch.anchor.sig"
            sig_path.write_text(signature_bytes.hex(), encoding="utf-8")

            artifacts = [
                bundle_evidence._artifact("program_ir", program_ir_path),
                bundle_evidence._artifact("plan", plan_path),
                bundle_evidence._artifact("runtime_result", runtime_path),
                bundle_evidence._artifact("backend_ir", backend_ir_path),
                bundle_evidence._artifact("qasm", qasm_path),
                bundle_evidence._artifact("epoch_anchor", anchor_path),
                bundle_evidence._artifact("epoch_sig", sig_path),
                bundle_evidence._artifact("execution_token", token_path),
            ]

            bundle_dir_one, manifest_one = bundle_evidence.build_bundle(
                out_dir=tmp,
                artifacts=artifacts,
                epoch_anchor=anchor_path,
                epoch_sig=sig_path,
                public_key=TEST_PUBLIC_KEY,
            )
            manifest_one_bytes = json.dumps(manifest_one, sort_keys=True, separators=(",", ":")).encode("utf-8")

            bundle_dir_two, manifest_two = bundle_evidence.build_bundle(
                out_dir=tmp,
                artifacts=artifacts,
                epoch_anchor=anchor_path,
                epoch_sig=sig_path,
                public_key=TEST_PUBLIC_KEY,
            )
            manifest_two_bytes = json.dumps(manifest_two, sort_keys=True, separators=(",", ":")).encode("utf-8")

            self.assertEqual(bundle_dir_one, bundle_dir_two)
            self.assertEqual(manifest_one_bytes, manifest_two_bytes)
            self.assertEqual(manifest_one["bundle_id"], manifest_two["bundle_id"])
            self.assertTrue(manifest_one["verification"]["epoch_ok"])
            self.assertTrue(manifest_one["verification"]["signature_ok"])
            self.assertIn("execution_token", [entry["role"] for entry in manifest_one["artifacts"]])

            for entry in manifest_one["artifacts"]:
                copied = bundle_dir_one / entry["filename"]
                digest = bundle_evidence._digest_bytes(copied.read_bytes())
                self.assertEqual(digest, entry["digest"])


if __name__ == "__main__":
    unittest.main()
