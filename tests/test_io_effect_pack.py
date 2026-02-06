import json
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


class IOEffectPackTests(unittest.TestCase):
    def _ctx(self, io_policy):
        token = ExecutionToken.build(io_policy=io_policy)
        return RuntimeContext(trace_sink=self.tmp, execution_token=token)

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_io_connect_deterministic_and_sanitized(self):
        ctx = self._ctx(
            {
                "io_allowed": True,
                "io_scopes": ["BROKER_CONNECT"],
                "io_endpoints_allowed": ["broker://demo"],
            }
        )
        step = EffectStep(
            step_id="io_connect",
            effect_type=EffectType.IO_CONNECT,
            args={
                "endpoint": "broker://demo",
                "params": {"api_key": "SECRET", "client": "unit"},
            },
        )
        handler = get_handler(step.effect_type)
        result_one = handler(step, ctx)
        result_two = handler(step, ctx)
        self.assertTrue(result_one.ok)
        self.assertEqual(result_one.artifact_digests, result_two.artifact_digests)
        request_path = self.tmp / "io_connect_request.json"
        payload = json.loads(request_path.read_text(encoding="utf-8"))
        self.assertNotIn("api_key", json.dumps(payload))

    def test_io_submit_refuses_without_scope(self):
        ctx = self._ctx({"io_allowed": True, "io_scopes": ["ORDER_QUERY"]})
        step = EffectStep(
            step_id="io_submit",
            effect_type=EffectType.IO_SUBMIT_ORDER,
            args={"endpoint": "broker://demo", "order": {"symbol": "ABC", "qty": 1}},
        )
        result = get_handler(step.effect_type)(step, ctx)
        self.assertFalse(result.ok)
        self.assertEqual(result.refusal_type, "IOPermissionDenied")

    def test_io_endpoint_allowlist(self):
        ctx = self._ctx(
            {
                "io_allowed": True,
                "io_scopes": ["ORDER_CANCEL"],
                "io_endpoints_allowed": ["broker://allowed"],
            }
        )
        step = EffectStep(
            step_id="io_cancel",
            effect_type=EffectType.IO_CANCEL_ORDER,
            args={"endpoint": "broker://other", "order_id": "ord-1"},
        )
        result = get_handler(step.effect_type)(step, ctx)
        self.assertFalse(result.ok)
        self.assertEqual(result.refusal_type, "EndpointNotAllowed")


if __name__ == "__main__":
    unittest.main()
