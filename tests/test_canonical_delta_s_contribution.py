import json
import tempfile
import unittest
from pathlib import Path

from hpl.runtime.context import RuntimeContext
from hpl.runtime.effects import EffectStep, get_handler


class CanonicalDeltaSContributionTests(unittest.TestCase):
    def test_compute_delta_s_includes_canonical_contribution(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            prior = root / "prior.json"
            posterior = root / "posterior.json"
            eq09 = root / "canonical_eq09_report.json"
            eq15 = root / "canonical_eq15_report.json"
            out = root / "delta_s_report.json"

            prior.write_text(json.dumps({"x": 1}, sort_keys=True), encoding="utf-8")
            posterior.write_text(json.dumps({"x": 2}, sort_keys=True), encoding="utf-8")
            eq09.write_text(json.dumps({"spectral_energy": 0.7}, sort_keys=True), encoding="utf-8")
            eq15.write_text(json.dumps({"entropy_proxy": 0.4}, sort_keys=True), encoding="utf-8")

            step = EffectStep(
                step_id="delta_s",
                effect_type="COMPUTE_DELTA_S",
                args={
                    "prior_path": str(prior),
                    "posterior_path": str(posterior),
                    "canonical_eq09_path": str(eq09),
                    "canonical_eq15_path": str(eq15),
                    "out_path": str(out),
                    "method": "hash_diff_plus_canonical",
                },
            )
            ctx = RuntimeContext(trace_sink=root)
            result = get_handler(step.effect_type)(step, ctx)
            self.assertTrue(result.ok)

            report = json.loads(out.read_text(encoding="utf-8"))
            self.assertIn("delta_s_base", report)
            self.assertIn("canonical_contribution", report)
            self.assertIn("delta_s_canonical", report)
            self.assertGreater(report["canonical_contribution"], 0.0)
            self.assertEqual(report["delta_s_canonical"], report["canonical_contribution"])
            self.assertGreaterEqual(report["delta_s"], report["delta_s_base"])


if __name__ == "__main__":
    unittest.main()
