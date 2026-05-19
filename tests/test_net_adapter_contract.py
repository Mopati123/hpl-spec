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


class NetAdapterContractTests(unittest.TestCase):
    def setUp(self):
        self._env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def test_live_mock_adapter_response_includes_request_id(self):
        token = ExecutionToken.build(
            net_policy={
                "net_mode": "live",
                "net_caps": ["NET_CONNECT"],
                "net_endpoints_allowlist": ["net://demo"],
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
            os.environ["HPL_NET_ADAPTER"] = "mock"

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

            request = json.loads(
                (tmp / "net_connect_request.json").read_text(encoding="utf-8")
            )
            response = json.loads(
                (tmp / "net_connect_response.json").read_text(encoding="utf-8")
            )
            event = json.loads(
                (tmp / "net_connect_event.json").read_text(encoding="utf-8")
            )

            self.assertEqual(response.get("request_id"), request.get("request_id"))
            self.assertEqual(response.get("endpoint"), "net://demo")
            self.assertEqual(response.get("status"), "connected")
            self.assertTrue(response.get("mock"))
            self.assertEqual(event.get("request_id"), request.get("request_id"))

    def test_net_send_redacts_secret_payload_before_evidence(self):
        token = ExecutionToken.build(
            net_policy={
                "net_mode": "dry_run",
                "net_caps": ["NET_SEND"],
                "net_endpoints_allowlist": ["net://demo"],
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
                step_id="net_send",
                effect_type=EffectType.NET_SEND,
                args={
                    "endpoint": "net://demo",
                    "payload": {
                        "message": "hello",
                        "api_key": "sk_live_123456",
                        "nested": {"password": "secret-password"},
                    },
                    "request_path": "net_send_request.json",
                    "response_path": "net_send_response.json",
                    "event_path": "net_send_event.json",
                    "session_manifest_path": "net_session_manifest.json",
                },
            )

            result = get_handler(step.effect_type)(step, ctx)

            self.assertTrue(result.ok)

            request = json.loads(
                (tmp / "net_send_request.json").read_text(encoding="utf-8")
            )
            serialized = json.dumps(request, sort_keys=True)

            self.assertIn("hello", serialized)
            self.assertNotIn("sk_live_123456", serialized)
            self.assertNotIn("secret-password", serialized)
            self.assertNotIn("api_key", serialized)
            self.assertNotIn("password", serialized)

    def test_live_adapter_unavailable_refuses_deterministically(self):
        token = ExecutionToken.build(
            net_policy={
                "net_mode": "live",
                "net_caps": ["NET_CONNECT"],
                "net_endpoints_allowlist": ["net://demo"],
                "net_timeout_ms": 2500,
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
            os.environ["HPL_NET_ADAPTER"] = "unsupported"

            step = EffectStep(
                step_id="net_connect",
                effect_type=EffectType.NET_CONNECT,
                args={"endpoint": "net://demo"},
            )

            result = get_handler(step.effect_type)(step, ctx)

            self.assertFalse(result.ok)
            self.assertEqual(result.refusal_type, "NetAdapterUnavailable")
            self.assertTrue(
                any("unsupported net adapter" in reason for reason in result.refusal_reasons)
            )


if __name__ == "__main__":
    unittest.main()