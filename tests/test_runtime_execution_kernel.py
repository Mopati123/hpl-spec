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
from hpl.runtime.contracts import ExecutionContract
from hpl.runtime.context import RuntimeContext
from hpl.runtime.engine import RuntimeEngine
from hpl.runtime.effects.effect_types import EffectType


class ExecutionKernelTests(unittest.TestCase):
    def test_transcript_determinism_for_effect_steps(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            artifact_path = tmp / "artifact.json"
            plan = {
                "plan_id": "plan_kernel",
                "program_id": "program_kernel",
                "status": "planned",
                "steps": [
                    {
                        "step_id": "step_noop",
                        "effect_type": EffectType.NOOP,
                        "args": {},
                        "requires": {},
                    },
                    {
                        "step_id": "step_emit",
                        "effect_type": EffectType.EMIT_ARTIFACT,
                        "args": {
                            "path": str(artifact_path),
                            "payload": {"value": 42},
                            "format": "json",
                        },
                        "requires": {},
                    },
                ],
            }
            token = ExecutionToken.build(allowed_backends=["CLASSICAL"])
            plan["execution_token"] = token.to_dict()
            contract = ExecutionContract(allowed_steps={"step_noop", "step_emit"})
            ctx = RuntimeContext(execution_token=token)

            result_one = RuntimeEngine().run(plan, ctx, contract)
            result_two = RuntimeEngine().run(plan, ctx, contract)

            json_one = json.dumps(result_one.to_dict(), sort_keys=True)
            json_two = json.dumps(result_two.to_dict(), sort_keys=True)
            self.assertEqual(json_one, json_two)
            self.assertEqual(result_one.result_id, result_two.result_id)
            self.assertEqual(result_one.transcript, result_two.transcript)

    def test_refuse_on_backend_not_permitted(self):
        plan = {
            "plan_id": "plan_backend",
            "program_id": "program_backend",
            "status": "planned",
            "steps": [
                {
                    "step_id": "step_qasm",
                    "effect_type": EffectType.NOOP,
                    "args": {},
                    "requires": {"backend": "QASM"},
                }
            ],
        }
        token = ExecutionToken.build(allowed_backends=["CLASSICAL"])
        plan["execution_token"] = token.to_dict()
        contract = ExecutionContract(allowed_steps={"step_qasm"})
        ctx = RuntimeContext(execution_token=token)

        result = RuntimeEngine().run(plan, ctx, contract)
        self.assertEqual(result.status, "denied")
        self.assertTrue(any("backend not permitted" in reason for reason in result.reasons))
        self.assertTrue(result.constraint_witnesses)


if __name__ == "__main__":
    unittest.main()
