import importlib.util
import shutil
import sys
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

TOOLS_PATH = ROOT / "tools" / "anchor_epoch.py"
SPEC = importlib.util.spec_from_file_location("anchor_epoch", TOOLS_PATH)
anchor_epoch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(anchor_epoch)

VERIFY_PATH = ROOT / "tools" / "verify_epoch.py"
SPEC_VERIFY = importlib.util.spec_from_file_location("verify_epoch", VERIFY_PATH)
verify_epoch = importlib.util.module_from_spec(SPEC_VERIFY)
SPEC_VERIFY.loader.exec_module(verify_epoch)


class EpochAnchorVerificationTests(unittest.TestCase):
    def _copy_required_files(self, dest_root: Path):
        required = anchor_epoch.collect_required_paths(ROOT)
        all_paths = required["schemas"] + required["registries"] + required["tooling"] + required["scheduler_spec"]
        for path in all_paths:
            rel = path.relative_to(ROOT)
            target = dest_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)

    def test_verify_passes_then_fails_on_tamper(self):
        anchor = anchor_epoch.build_epoch_anchor(
            epoch_id="epoch-2",
            timestamp="2026-01-02T00:00:00Z",
            git_commit="deadbeef",
            root=ROOT,
            emit_witness=False,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_root = Path(tmpdir)
            self._copy_required_files(temp_root)

            ok, errors = verify_epoch.verify_epoch_anchor(anchor, root=temp_root, git_commit_override="deadbeef")
            self.assertTrue(ok)
            self.assertEqual(errors, [])

            tampered = temp_root / "docs" / "spec" / "04_ir_schema.json"
            tampered.write_text(tampered.read_text(encoding="utf-8") + "\n", encoding="utf-8")

            ok, errors = verify_epoch.verify_epoch_anchor(anchor, root=temp_root, git_commit_override="deadbeef")
            self.assertFalse(ok)
            self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
