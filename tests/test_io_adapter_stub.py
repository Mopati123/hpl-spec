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


class IOAdapterStubTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self.tmp_dir.name)
        self._env = dict(os.environ)

    def tearDown(self):
        self.tmp_dir.cleanup()
        os.environ.clear()
        os.environ.update(self._env)

    def _ctx(self):
        token = ExecutionToken.build(
            io_policy={"io_allowed": True, "io_scopes": ["BROKER_CONNECT"]}
        )
        return RuntimeContext(trace_sink=self.tmp, execution_token=token, io_enabled=True)

    def test_stub_requires_ready_flag(self):
        os.environ["HPL_IO_ADAPTER"] = "mt5"
        os.environ["HPL_IO_ENABLED"] = "1"
        if "HPL_IO_ADAPTER_READY" in os.environ:
            del os.environ["HPL_IO_ADAPTER_READY"]
        step = EffectStep(
            step_id="io_connect",
            effect_type=EffectType.IO_CONNECT,
            args={"endpoint": "broker://demo"},
        )
        result = get_handler(step.effect_type)(step, self._ctx())
        self.assertFalse(result.ok)
        self.assertEqual(result.refusal_type, "IOAdapterUnavailable")

    def test_stub_connect_success_when_ready(self):
        os.environ["HPL_IO_ADAPTER"] = "mt5"
        os.environ["HPL_IO_ENABLED"] = "1"
        os.environ["HPL_IO_ADAPTER_READY"] = "1"
        step = EffectStep(
            step_id="io_connect",
            effect_type=EffectType.IO_CONNECT,
            args={
                "endpoint": "broker://demo",
                "request_path": "io_req.json",
                "response_path": "io_resp.json",
            },
        )
        result = get_handler(step.effect_type)(step, self._ctx())
        self.assertTrue(result.ok)
        response_payload = json.loads((self.tmp / "io_resp.json").read_text(encoding="utf-8"))
        self.assertEqual(response_payload.get("adapter"), "mt5")


if __name__ == "__main__":
    unittest.main()
