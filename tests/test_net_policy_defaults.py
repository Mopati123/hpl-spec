import os
import sys
import tempfile
import unittest
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from hpl.execution_token import ExecutionToken
from hpl.runtime.context import RuntimeContext
from hpl.runtime.effects import EffectStep, EffectType, get_handler


class NetPolicyDefaultsTests(unittest.TestCase):
    def setUp(self):
        self._env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def test_net_policy_defaults_applied(self):
        token = ExecutionToken.build(net_policy={"net_caps": ["NET_CONNECT"]})
        policy = token.net_policy or {}
        self.assertEqual(policy.get("net_mode"), "dry_run")
        self.assertEqual(policy.get("net_timeout_ms"), 2500)
        self.assertEqual(policy.get("net_nonce_policy"), "HPL_DETERMINISTIC_NONCE_V1")
        self.assertEqual(policy.get("net_redaction_policy_id"), "R1")
        self.assertEqual(policy.get("net_crypto_policy_id"), "QKX1")

    def test_net_timeout_refusal_deterministic(self):
        token = ExecutionToken.build(
            net_policy={
                "net_caps": ["NET_CONNECT"],
                "net_endpoints_allowlist": ["net://demo"],
                "net_timeout_ms": 100,
            }
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            ctx = RuntimeContext(trace_sink=tmp, execution_token=token, net_enabled=True)
            os.environ["HPL_NET_ENABLED"] = "1"
            step = EffectStep(
                step_id="net_connect",
                effect_type=EffectType.NET_CONNECT,
                args={
                    "endpoint": "net://demo",
                    "params": {"timeout_ms": 200},
                },
            )
            result = get_handler(step.effect_type)(step, ctx)
            self.assertFalse(result.ok)
            self.assertEqual(result.refusal_type, "NetTimeout")
            self.assertIn("timeout_bucket=T100ms", result.refusal_reasons)

    def test_net_nonce_deterministic(self):
        token = ExecutionToken.build(
            net_policy={
                "net_caps": ["NET_CONNECT"],
                "net_endpoints_allowlist": ["net://demo"],
            }
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            ctx = RuntimeContext(trace_sink=tmp, execution_token=token, net_enabled=True)
            os.environ["HPL_NET_ENABLED"] = "1"
            step_one = EffectStep(
                step_id="net_connect",
                effect_type=EffectType.NET_CONNECT,
                args={
                    "endpoint": "net://demo",
                    "request_path": "net_req_one.json",
                },
            )
            step_two = EffectStep(
                step_id="net_connect",
                effect_type=EffectType.NET_CONNECT,
                args={
                    "endpoint": "net://demo",
                    "request_path": "net_req_two.json",
                },
            )
            result_one = get_handler(step_one.effect_type)(step_one, ctx)
            result_two = get_handler(step_two.effect_type)(step_two, ctx)
            self.assertTrue(result_one.ok)
            self.assertTrue(result_two.ok)
            req_one = json.loads((tmp / "net_req_one.json").read_text(encoding="utf-8"))
            req_two = json.loads((tmp / "net_req_two.json").read_text(encoding="utf-8"))
            self.assertEqual(req_one.get("nonce"), req_two.get("nonce"))
            self.assertEqual(req_one.get("nonce_policy"), "HPL_DETERMINISTIC_NONCE_V1")


if __name__ == "__main__":
    unittest.main()
