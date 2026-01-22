import importlib.util
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

TOOLS_PATH = ROOT / "tools" / "anchor_epoch.py"
SPEC = importlib.util.spec_from_file_location("anchor_epoch", TOOLS_PATH)
anchor_epoch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(anchor_epoch)


class EpochAnchorGenerationTests(unittest.TestCase):
    def test_anchor_deterministic(self):
        anchor1 = anchor_epoch.build_epoch_anchor(
            epoch_id="epoch-1",
            timestamp="2026-01-01T00:00:00Z",
            git_commit="deadbeef",
            root=ROOT,
            emit_witness=True,
        )
        anchor2 = anchor_epoch.build_epoch_anchor(
            epoch_id="epoch-1",
            timestamp="2026-01-01T00:00:00Z",
            git_commit="deadbeef",
            root=ROOT,
            emit_witness=True,
        )
        self.assertEqual(anchor1, anchor2)
        self.assertIn("papas_witness_digest", anchor1)


if __name__ == "__main__":
    unittest.main()
