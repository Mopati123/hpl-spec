import importlib.util
import json
import sys
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from hpl.audit.coupling_event import build_coupling_event_from_registry

TOOLS_PATH = ROOT / "tools" / "validate_coupling_topology.py"
SPEC = importlib.util.spec_from_file_location("validate_coupling_topology", TOOLS_PATH)
validate_coupling_topology = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_coupling_topology)

FIXTURE_PATH = ROOT / "tests" / "fixtures" / "coupling_registry_valid.json"


class CouplingEventEmissionTests(unittest.TestCase):
    def _load_registry(self):
        return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_event_required_fields(self):
        bundle = build_coupling_event_from_registry(self._load_registry())
        event = bundle.event
        required = {
            "event_id",
            "timestamp",
            "edge_id",
            "sector_src",
            "sector_dst",
            "operator_name",
            "input_digest",
            "output_digest",
            "invariants_checked",
            "scheduler_authorization_ref",
            "projector_versions",
            "evidence_artifacts",
        }
        self.assertTrue(required.issubset(set(event.keys())))
        self.assertIsInstance(event["evidence_artifacts"], dict)
        for value in event["evidence_artifacts"].values():
            self.assertIsInstance(value, str)

    def test_papas_witness_present_and_deterministic(self):
        bundle1 = build_coupling_event_from_registry(self._load_registry())
        bundle2 = build_coupling_event_from_registry(self._load_registry())
        event1 = bundle1.event
        event2 = bundle2.event
        self.assertEqual(event1, event2)

        witness = json.loads(event1["evidence_artifacts"]["papas_witness_record"])
        self.assertEqual(witness["observer_id"], "papas")
        self.assertIn("coupling_event", witness["artifact_digests"])

    def test_entanglement_metadata_matches_fixture(self):
        bundle = build_coupling_event_from_registry(self._load_registry())
        event = bundle.event
        meta = json.loads(event["evidence_artifacts"]["entanglement_metadata"])
        self.assertEqual(meta["sector_src"], "sector.alpha")
        self.assertEqual(meta["sector_dst"], "sector.beta")
        self.assertEqual(meta["operator_name"], "CoupleAlphaBeta")
        self.assertTrue(meta["symmetric_capable"])

    def test_validator_emit_event_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "event.json"
            argv = [
                "validate_coupling_topology.py",
                "--emit-event",
                str(target),
                str(FIXTURE_PATH),
            ]
            original_argv = sys.argv
            try:
                sys.argv = argv
                result = validate_coupling_topology.main()
            finally:
                sys.argv = original_argv

            self.assertEqual(result, 0)
            self.assertTrue(target.exists())
            data = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(data["edge_id"], "edge.alpha.beta")


if __name__ == "__main__":
    unittest.main()
