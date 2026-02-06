import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from tools import bundle_evidence


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")), encoding="utf-8")


class BundleIORolesTests(unittest.TestCase):
    def test_io_roles_required(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            request = tmp / "io_request.json"
            response = tmp / "io_response.json"
            outcome = tmp / "io_outcome.json"
            reconciliation = tmp / "reconciliation_report.json"
            redaction = tmp / "redaction_report.json"
            _write_json(request, {"request_id": "req-1"})
            _write_json(response, {"status": "accepted"})
            _write_json(outcome, {"action": "commit"})
            _write_json(reconciliation, {"ok": True})
            _write_json(redaction, {"ok": True, "findings": []})

            artifacts = [
                bundle_evidence._artifact("io_request_log", request),
                bundle_evidence._artifact("io_response_log", response),
                bundle_evidence._artifact("io_outcome", outcome),
                bundle_evidence._artifact("reconciliation_report", reconciliation),
                bundle_evidence._artifact("redaction_report", redaction),
            ]
            bundle_dir, manifest = bundle_evidence.build_bundle(
                out_dir=tmp,
                artifacts=artifacts,
                epoch_anchor=None,
                epoch_sig=None,
                public_key=None,
            )
            self.assertIn("io_lane_v1", manifest)
            self.assertTrue(manifest["io_lane_v1"]["ok"])

            # Missing io_response_log should fail
            artifacts_missing = [
                bundle_evidence._artifact("io_request_log", request),
                bundle_evidence._artifact("io_outcome", outcome),
                bundle_evidence._artifact("reconciliation_report", reconciliation),
                bundle_evidence._artifact("redaction_report", redaction),
            ]
            _, manifest_missing = bundle_evidence.build_bundle(
                out_dir=tmp,
                artifacts=artifacts_missing,
                epoch_anchor=None,
                epoch_sig=None,
                public_key=None,
            )
            self.assertIn("io_lane_v1", manifest_missing)
            self.assertFalse(manifest_missing["io_lane_v1"]["ok"])

    def test_rollback_requires_record(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            request = tmp / "io_request.json"
            response = tmp / "io_response.json"
            outcome = tmp / "io_outcome.json"
            reconciliation = tmp / "reconciliation_report.json"
            redaction = tmp / "redaction_report.json"
            _write_json(request, {"request_id": "req-2"})
            _write_json(response, {"status": "rejected"})
            _write_json(outcome, {"action": "rollback"})
            _write_json(reconciliation, {"ok": False})
            _write_json(redaction, {"ok": True, "findings": []})

            artifacts = [
                bundle_evidence._artifact("io_request_log", request),
                bundle_evidence._artifact("io_response_log", response),
                bundle_evidence._artifact("io_outcome", outcome),
                bundle_evidence._artifact("reconciliation_report", reconciliation),
                bundle_evidence._artifact("redaction_report", redaction),
            ]
            _, manifest = bundle_evidence.build_bundle(
                out_dir=tmp,
                artifacts=artifacts,
                epoch_anchor=None,
                epoch_sig=None,
                public_key=None,
            )
            self.assertFalse(manifest["io_lane_v1"]["ok"])
            self.assertIn("rollback_record", manifest["io_lane_v1"]["missing_required"])


if __name__ == "__main__":
    unittest.main()
