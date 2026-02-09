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


class IOPolicyDefaultsTests(unittest.TestCase):
    def setUp(self):
        self._env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def test_io_policy_defaults_applied(self):
        token = ExecutionToken.build(io_policy={"io_allowed": True})
        policy = token.io_policy or {}
        self.assertEqual(policy.get("io_mode"), "dry_run")
        self.assertEqual(policy.get("io_timeout_ms"), 2500)
        self.assertEqual(policy.get("io_nonce_policy"), "HPL_DETERMINISTIC_NONCE_V1")
        self.assertEqual(policy.get("io_redaction_policy_id"), "R1")

    def test_io_timeout_refusal_deterministic(self):
        token = ExecutionToken.build(
            io_policy={
                "io_allowed": True,
                "io_scopes": ["BROKER_CONNECT"],
                "io_timeout_ms": 100,
            }
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            ctx = RuntimeContext(trace_sink=tmp, execution_token=token, io_enabled=True)
            os.environ["HPL_IO_ENABLED"] = "1"
            step = EffectStep(
                step_id="io_connect",
                effect_type=EffectType.IO_CONNECT,
                args={
                    "endpoint": "broker://demo",
                    "params": {"timeout_ms": 200},
                },
            )
            result = get_handler(step.effect_type)(step, ctx)
            self.assertFalse(result.ok)
            self.assertEqual(result.refusal_type, "IOTimeout")
            self.assertIn("timeout_bucket=T100ms", result.refusal_reasons)

    def test_io_nonce_deterministic(self):
        token = ExecutionToken.build(io_policy={"io_allowed": True, "io_scopes": ["BROKER_CONNECT"]})
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            ctx = RuntimeContext(trace_sink=tmp, execution_token=token, io_enabled=False)
            step_one = EffectStep(
                step_id="io_connect",
                effect_type=EffectType.IO_CONNECT,
                args={
                    "endpoint": "broker://demo",
                    "request_path": "io_req_one.json",
                },
            )
            step_two = EffectStep(
                step_id="io_connect",
                effect_type=EffectType.IO_CONNECT,
                args={
                    "endpoint": "broker://demo",
                    "request_path": "io_req_two.json",
                },
            )
            result_one = get_handler(step_one.effect_type)(step_one, ctx)
            result_two = get_handler(step_two.effect_type)(step_two, ctx)
            self.assertTrue(result_one.ok)
            self.assertTrue(result_two.ok)
            req_one = json.loads((tmp / "io_req_one.json").read_text(encoding="utf-8"))
            req_two = json.loads((tmp / "io_req_two.json").read_text(encoding="utf-8"))
            self.assertEqual(req_one.get("nonce"), req_two.get("nonce"))
            self.assertEqual(req_one.get("nonce_policy"), "HPL_DETERMINISTIC_NONCE_V1")


if __name__ == "__main__":
    unittest.main()
