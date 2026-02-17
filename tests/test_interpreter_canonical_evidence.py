import json
import tempfile
import unittest
from pathlib import Path

from hpl.execution_token import ExecutionToken
from hpl.runtime.context import RuntimeContext
from hpl.runtime.contracts import ExecutionContract
from hpl.runtime.engine import RuntimeEngine


class InterpreterCanonicalEvidenceTests(unittest.TestCase):
    def test_transcript_surfaces_canonical_evidence(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            input_path = root / "market_snapshot.json"
            input_path.write_text(
                json.dumps({"prices": [1.0, 1.2, 1.4], "symbol": "DEMO"}, sort_keys=True),
                encoding="utf-8",
            )

            token = ExecutionToken.build(
                allowed_backends=["CLASSICAL"],
                operator_policy={
                    "operator_allowlist": ["CANONICAL_EQ09", "CANONICAL_EQ15"],
                    "operator_strict": True,
                },
            )
            plan = {
                "status": "planned",
                "steps": [
                    {
                        "step_id": "canonical_eq09",
                        "effect_type": "CANONICAL_INVOKE_EQ09",
                        "args": {
                            "input_path": str(input_path),
                            "out_path": "canonical_eq09_report.json",
                        },
                        "requires": {
                            "backend": "CLASSICAL",
                            "operator_id": "CANONICAL_EQ09",
                        },
                    }
                ],
                "execution_token": token.to_dict(),
            }
            ctx = RuntimeContext(execution_token=token, trace_sink=root)
            contract = ExecutionContract(allowed_steps={"canonical_eq09"})
            result = RuntimeEngine().run(plan, ctx, contract)
            self.assertEqual(result.status, "completed")
            self.assertTrue(result.transcript)
            transcript_entry = result.transcript[0]
            self.assertIn("canonical_eq09_report", transcript_entry.get("canonical_evidence", []))
            self.assertIn("canonical_eq09_report", transcript_entry.get("artifact_digests", {}))


if __name__ == "__main__":
    unittest.main()
