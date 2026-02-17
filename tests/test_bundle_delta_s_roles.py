import json
import tempfile
import unittest
from pathlib import Path

from hpl.execution_token import ExecutionToken
from tools import bundle_evidence


class BundleDeltaSRolesTests(unittest.TestCase):
    def _write_json(self, path: Path, payload: dict) -> None:
        path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")), encoding="utf-8")

    def test_delta_s_roles_deterministic(self):
        def run_once() -> bytes:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                token = ExecutionToken.build(collapse_requires_delta_s=True)
                token_path = root / "execution_token.json"
                self._write_json(token_path, token.to_dict())

                delta_s_path = root / "delta_s_report.json"
                admissibility_path = root / "admissibility_certificate.json"
                collapse_path = root / "collapse_decision.json"
                canonical_eq09_path = root / "canonical_eq09_report.json"
                canonical_eq15_path = root / "canonical_eq15_report.json"
                self._write_json(delta_s_path, {"delta_s": 0.5})
                self._write_json(admissibility_path, {"ok": True})
                self._write_json(collapse_path, {"ok": True})
                self._write_json(canonical_eq09_path, {"spectral_energy": 0.2})
                self._write_json(canonical_eq15_path, {"entropy_proxy": 0.3})

                artifacts = [
                    bundle_evidence._artifact("execution_token", token_path),
                    bundle_evidence._artifact("delta_s_report", delta_s_path),
                    bundle_evidence._artifact("admissibility_certificate", admissibility_path),
                    bundle_evidence._artifact("collapse_decision", collapse_path),
                    bundle_evidence._artifact("canonical_eq09_report", canonical_eq09_path),
                    bundle_evidence._artifact("canonical_eq15_report", canonical_eq15_path),
                ]
                bundle_dir, manifest = bundle_evidence.build_bundle(
                    out_dir=root,
                    artifacts=artifacts,
                    epoch_anchor=None,
                    epoch_sig=None,
                    public_key=None,
                )
                manifest_bytes = bundle_evidence._canonical_json(manifest).encode("utf-8")
                self.assertTrue(manifest.get("delta_s_v1", {}).get("ok"))
                self.assertTrue(manifest.get("canonical_invoke_v1", {}).get("ok"))
                return manifest_bytes

        first = run_once()
        second = run_once()
        self.assertEqual(first, second)

    def test_delta_s_roles_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            token = ExecutionToken.build(collapse_requires_delta_s=True)
            token_path = root / "execution_token.json"
            self._write_json(token_path, token.to_dict())

            delta_s_path = root / "delta_s_report.json"
            admissibility_path = root / "admissibility_certificate.json"
            self._write_json(delta_s_path, {"delta_s": 0.5})
            self._write_json(admissibility_path, {"ok": True})

            artifacts = [
                bundle_evidence._artifact("execution_token", token_path),
                bundle_evidence._artifact("delta_s_report", delta_s_path),
                bundle_evidence._artifact("admissibility_certificate", admissibility_path),
            ]
            _, manifest = bundle_evidence.build_bundle(
                out_dir=root,
                artifacts=artifacts,
                epoch_anchor=None,
                epoch_sig=None,
                public_key=None,
            )
            delta_section = manifest.get("delta_s_v1", {})
            self.assertFalse(delta_section.get("ok", True))
            self.assertIn("collapse_decision", delta_section.get("missing_required", []))


if __name__ == "__main__":
    unittest.main()
