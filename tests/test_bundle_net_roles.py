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


class BundleNetRolesTests(unittest.TestCase):
    def test_net_roles_required(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            request = tmp / "net_request.json"
            response = tmp / "net_response.json"
            event = tmp / "net_event.json"
            session = tmp / "net_session_manifest.json"
            redaction = tmp / "redaction_report.json"
            _write_json(request, {"request_id": "req-1"})
            _write_json(response, {"status": "ok"})
            _write_json(event, {"event_type": "send"})
            _write_json(session, {"endpoint": "net://demo"})
            _write_json(redaction, {"ok": True, "findings": []})

            artifacts = [
                bundle_evidence._artifact("net_request_log", request),
                bundle_evidence._artifact("net_response_log", response),
                bundle_evidence._artifact("net_event_log", event),
                bundle_evidence._artifact("net_session_manifest", session),
                bundle_evidence._artifact("redaction_report", redaction),
            ]
            _, manifest = bundle_evidence.build_bundle(
                out_dir=tmp,
                artifacts=artifacts,
                epoch_anchor=None,
                epoch_sig=None,
                public_key=None,
            )
            self.assertIn("net_lane_v1", manifest)
            self.assertTrue(manifest["net_lane_v1"]["ok"])

            artifacts_missing = [
                bundle_evidence._artifact("net_request_log", request),
                bundle_evidence._artifact("net_response_log", response),
                bundle_evidence._artifact("net_session_manifest", session),
                bundle_evidence._artifact("redaction_report", redaction),
            ]
            _, manifest_missing = bundle_evidence.build_bundle(
                out_dir=tmp,
                artifacts=artifacts_missing,
                epoch_anchor=None,
                epoch_sig=None,
                public_key=None,
            )
            self.assertIn("net_lane_v1", manifest_missing)
            self.assertFalse(manifest_missing["net_lane_v1"]["ok"])
            self.assertIn("net_event_log", manifest_missing["net_lane_v1"]["missing_required"])


if __name__ == "__main__":
    unittest.main()
