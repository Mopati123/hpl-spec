import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from hpl.runtime.context import RuntimeContext
from hpl.runtime.effects import EffectStep, EffectType, get_handler


class RedactionGateTests(unittest.TestCase):
    def _run_bundle(self, content: str):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            artifact_path = tmp / "artifact.json"
            artifact_path.write_text(content, encoding="utf-8")
            out_dir = tmp / "bundles"
            ctx = RuntimeContext(trace_sink=tmp)
            step = EffectStep(
                step_id="bundle",
                effect_type=EffectType.BUNDLE_EVIDENCE,
                args={
                    "path": str(out_dir),
                    "artifacts": [{"role": "program_ir", "path": "artifact.json"}],
                },
            )
            handler = get_handler(EffectType.BUNDLE_EVIDENCE)
            result = handler(step, ctx)
            report_path = tmp / "redaction_report.json"
            report_payload = json.loads(report_path.read_text(encoding="utf-8"))
            return result, report_payload

    def test_redaction_refuses_on_secret(self):
        secret_value = "ghp_" + "A" * 40
        payload = json.dumps({"note": secret_value}, sort_keys=True, separators=(",", ":"))
        result, report = self._run_bundle(payload)
        self.assertFalse(result.ok)
        self.assertEqual(result.refusal_type, "SecretDetectedInArtifact")
        self.assertFalse(report.get("ok", True))
        self.assertTrue(report.get("findings"))

    def test_redaction_allows_clean_artifacts(self):
        payload = json.dumps({"note": "safe-value"}, sort_keys=True, separators=(",", ":"))
        result, report = self._run_bundle(payload)
        self.assertTrue(result.ok)
        self.assertTrue(report.get("ok", False))


if __name__ == "__main__":
    unittest.main()
