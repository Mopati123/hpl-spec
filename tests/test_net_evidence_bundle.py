import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from hpl.execution_token import ExecutionToken
from hpl.runtime.context import RuntimeContext
from hpl.runtime.effects import EffectStep, EffectType, get_handler
from tools import bundle_evidence


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )


class NetEvidenceBundleTests(unittest.TestCase):
    def setUp(self):
        self._env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def test_net_connect_emits_bundle_complete_evidence(self):
        token = ExecutionToken.build(
            net_policy={
                "net_mode": "dry_run",
                "net_caps": ["NET_CONNECT"],
                "net_endpoints_allowlist": ["net://demo"],
                "net_budget_calls": 1,
                "net_timeout_ms": 2500,
                "net_nonce_policy": "HPL_DETERMINISTIC_NONCE_V1",
                "net_redaction_policy_id": "R1",
                "net_crypto_policy_id": "QKX1",
            }
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            ctx = RuntimeContext(
                trace_sink=tmp,
                execution_token=token,
                net_enabled=True,
            )
            os.environ["HPL_NET_ENABLED"] = "1"

            step = EffectStep(
                step_id="net_connect",
                effect_type=EffectType.NET_CONNECT,
                args={
                    "endpoint": "net://demo",
                    "request_path": "net_connect_request.json",
                    "response_path": "net_connect_response.json",
                    "event_path": "net_connect_event.json",
                    "session_manifest_path": "net_session_manifest.json",
                },
            )

            result = get_handler(step.effect_type)(step, ctx)

            self.assertTrue(result.ok)

            request = tmp / "net_connect_request.json"
            response = tmp / "net_connect_response.json"
            event = tmp / "net_connect_event.json"
            session = tmp / "net_session_manifest.json"
            redaction = tmp / "redaction_report.json"

            _write_json(redaction, {"ok": True, "findings": []})

            self.assertTrue(request.exists())
            self.assertTrue(response.exists())
            self.assertTrue(event.exists())
            self.assertTrue(session.exists())

            request_payload = json.loads(request.read_text(encoding="utf-8"))
            response_payload = json.loads(response.read_text(encoding="utf-8"))
            event_payload = json.loads(event.read_text(encoding="utf-8"))
            session_payload = json.loads(session.read_text(encoding="utf-8"))

            self.assertEqual(request_payload.get("endpoint"), "net://demo")
            self.assertEqual(request_payload.get("nonce_policy"), "HPL_DETERMINISTIC_NONCE_V1")
            self.assertEqual(response_payload.get("status"), "connected")
            self.assertEqual(event_payload.get("event_type"), "connect")
            self.assertEqual(event_payload.get("endpoint"), "net://demo")
            self.assertEqual(session_payload.get("endpoint"), "net://demo")
            self.assertEqual(session_payload.get("crypto_policy_id"), "QKX1")
            self.assertEqual(session_payload.get("redaction_policy_id"), "R1")

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
            self.assertEqual(manifest["net_lane_v1"]["missing_required"], [])

    def test_net_bundle_refuses_missing_response_log(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)

            request = tmp / "net_connect_request.json"
            event = tmp / "net_connect_event.json"
            session = tmp / "net_session_manifest.json"
            redaction = tmp / "redaction_report.json"

            _write_json(request, {"request_id": "req-1", "endpoint": "net://demo"})
            _write_json(event, {"event_type": "connect", "endpoint": "net://demo"})
            _write_json(session, {"endpoint": "net://demo"})
            _write_json(redaction, {"ok": True, "findings": []})

            artifacts = [
                bundle_evidence._artifact("net_request_log", request),
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
            self.assertFalse(manifest["net_lane_v1"]["ok"])
            self.assertIn(
                "net_response_log",
                manifest["net_lane_v1"]["missing_required"],
            )


if __name__ == "__main__":
    unittest.main()