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


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )


class NetSessionLifecycleTests(unittest.TestCase):
    def setUp(self):
        self._env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def test_full_net_session_emits_correlated_evidence(self):
        endpoint = "net://demo"
        token = ExecutionToken.build(
            net_policy={
                "net_mode": "dry_run",
                "net_caps": [
                    "NET_CONNECT",
                    "NET_HANDSHAKE",
                    "NET_KEY_EXCHANGE",
                    "NET_SEND",
                    "NET_RECV",
                    "NET_CLOSE",
                ],
                "net_endpoints_allowlist": [endpoint],
                "net_budget_calls": 6,
                "net_timeout_ms": 2500,
                "net_nonce_policy": "HPL_DETERMINISTIC_NONCE_V1",
                "net_redaction_policy_id": "R1",
                "net_crypto_policy_id": "QKX1",
            }
        )

        phases = [
            ("connect", EffectType.NET_CONNECT, {}),
            ("handshake", EffectType.NET_HANDSHAKE, {}),
            ("key_exchange", EffectType.NET_KEY_EXCHANGE, {}),
            ("send", EffectType.NET_SEND, {"payload": {"kind": "ping", "payload": "hello"}}),
            ("recv", EffectType.NET_RECV, {}),
            ("close", EffectType.NET_CLOSE, {}),
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            ctx = RuntimeContext(
                trace_sink=tmp,
                execution_token=token,
                net_enabled=True,
            )
            os.environ["HPL_NET_ENABLED"] = "1"

            request_ids = []

            for phase, effect_type, extra_args in phases:
                args = {
                    "endpoint": endpoint,
                    "request_path": f"net_{phase}_request.json",
                    "response_path": f"net_{phase}_response.json",
                    "event_path": f"net_{phase}_event.json",
                    "session_manifest_path": "net_session_manifest.json",
                }
                args.update(extra_args)

                step = EffectStep(
                    step_id=f"net_{phase}",
                    effect_type=effect_type,
                    args=args,
                )

                result = get_handler(step.effect_type)(step, ctx)
                self.assertTrue(result.ok, result.refusal_reasons)

                request_path = tmp / f"net_{phase}_request.json"
                response_path = tmp / f"net_{phase}_response.json"
                event_path = tmp / f"net_{phase}_event.json"

                self.assertTrue(request_path.exists())
                self.assertTrue(response_path.exists())
                self.assertTrue(event_path.exists())

                request = _read_json(request_path)
                response = _read_json(response_path)
                event = _read_json(event_path)

                self.assertEqual(request.get("endpoint"), endpoint)
                self.assertEqual(response.get("endpoint"), endpoint)
                self.assertEqual(event.get("endpoint"), endpoint)

                self.assertEqual(response.get("request_id"), request.get("request_id"))
                self.assertEqual(event.get("request_id"), request.get("request_id"))

                self.assertEqual(response.get("adapter_contract"), "NET_ADAPTER_CONTRACT_V1")
                self.assertEqual(request.get("nonce_policy"), "HPL_DETERMINISTIC_NONCE_V1")

                request_ids.append(request.get("request_id"))

            self.assertEqual(len(request_ids), 6)
            self.assertEqual(len(set(request_ids)), 6)

            session = _read_json(tmp / "net_session_manifest.json")
            self.assertEqual(session.get("endpoint"), endpoint)
            self.assertEqual(session.get("token_id"), token.token_id)
            self.assertEqual(session.get("crypto_policy_id"), "QKX1")
            self.assertEqual(session.get("redaction_policy_id"), "R1")
            self.assertEqual(session.get("nonce_policy"), "HPL_DETERMINISTIC_NONCE_V1")

    def test_full_net_session_bundle_complete(self):
        endpoint = "net://demo"
        token = ExecutionToken.build(
            net_policy={
                "net_mode": "dry_run",
                "net_caps": [
                    "NET_CONNECT",
                    "NET_HANDSHAKE",
                    "NET_KEY_EXCHANGE",
                    "NET_SEND",
                    "NET_RECV",
                    "NET_CLOSE",
                ],
                "net_endpoints_allowlist": [endpoint],
                "net_budget_calls": 6,
            }
        )

        phases = [
            ("connect", EffectType.NET_CONNECT, {}),
            ("handshake", EffectType.NET_HANDSHAKE, {}),
            ("key_exchange", EffectType.NET_KEY_EXCHANGE, {}),
            ("send", EffectType.NET_SEND, {"payload": {"kind": "ping", "payload": "hello"}}),
            ("recv", EffectType.NET_RECV, {}),
            ("close", EffectType.NET_CLOSE, {}),
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            ctx = RuntimeContext(
                trace_sink=tmp,
                execution_token=token,
                net_enabled=True,
            )
            os.environ["HPL_NET_ENABLED"] = "1"

            artifacts = []

            for phase, effect_type, extra_args in phases:
                args = {
                    "endpoint": endpoint,
                    "request_path": f"net_{phase}_request.json",
                    "response_path": f"net_{phase}_response.json",
                    "event_path": f"net_{phase}_event.json",
                    "session_manifest_path": "net_session_manifest.json",
                }
                args.update(extra_args)

                step = EffectStep(
                    step_id=f"net_{phase}",
                    effect_type=effect_type,
                    args=args,
                )

                result = get_handler(step.effect_type)(step, ctx)
                self.assertTrue(result.ok, result.refusal_reasons)

                artifacts.extend(
                    [
                        bundle_evidence._artifact(
                            "net_request_log", tmp / f"net_{phase}_request.json"
                        ),
                        bundle_evidence._artifact(
                            "net_response_log", tmp / f"net_{phase}_response.json"
                        ),
                        bundle_evidence._artifact(
                            "net_event_log", tmp / f"net_{phase}_event.json"
                        ),
                    ]
                )

            redaction = tmp / "redaction_report.json"
            _write_json(redaction, {"ok": True, "findings": []})

            artifacts.append(
                bundle_evidence._artifact(
                    "net_session_manifest", tmp / "net_session_manifest.json"
                )
            )
            artifacts.append(bundle_evidence._artifact("redaction_report", redaction))

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


if __name__ == "__main__":
    unittest.main()