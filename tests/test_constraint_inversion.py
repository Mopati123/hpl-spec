import sys
import unittest

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from hpl.audit.constraint_inversion import invert_constraints


class ConstraintInversionTests(unittest.TestCase):
    def test_inversion_deterministic(self):
        witness = {
            "witness_id": "sha256:test",
            "stage": "runtime_refusal",
            "refusal_reasons": ["reason_b", "reason_a"],
            "artifact_digests": {"plan": "sha256:abc"},
        }
        first = invert_constraints(witness)
        second = invert_constraints(witness)
        self.assertEqual(first, second)
        self.assertEqual(first["dual_proposal_id"], second["dual_proposal_id"])


if __name__ == "__main__":
    unittest.main()
