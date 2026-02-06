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


class DerivAdapterGateTests(unittest.TestCase):
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

    def test_deriv_missing_env_refuses(self):
        os.environ["HPL_IO_ADAPTER"] = "deriv"
        os.environ["HPL_IO_ENABLED"] = "1"
        os.environ["HPL_IO_ADAPTER_READY"] = "1"
        for key in ("HPL_DERIV_ENDPOINT", "HPL_DERIV_TOKEN"):
            if key in os.environ:
                del os.environ[key]
        step = EffectStep(
            step_id="io_connect",
            effect_type=EffectType.IO_CONNECT,
            args={"endpoint": "broker://demo"},
        )
        result = get_handler(step.effect_type)(step, self._ctx())
        self.assertFalse(result.ok)
        self.assertEqual(result.refusal_type, "IOAdapterUnavailable")


if __name__ == "__main__":
    unittest.main()
