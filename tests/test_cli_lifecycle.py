import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = [sys.executable, "-m", "hpl.cli"]


def _env():
    env = os.environ.copy()
    src_path = str(ROOT / "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")
    return env


def _run_cmd(args):
    return subprocess.run(
        CLI + args,
        cwd=ROOT,
        env=_env(),
        capture_output=True,
        text=True,
    )


class CliLifecycleTests(unittest.TestCase):
    def test_lifecycle_classical_determinism(self):
        with tempfile.TemporaryDirectory() as tmp_dir_one:
            out_one = Path(tmp_dir_one) / "out"
            result_one = _run_cmd(
                [
                    "lifecycle",
                    "examples/momentum_trade.hpl",
                    "--backend",
                    "classical",
                    "--out-dir",
                    str(out_one),
                ]
            )
            self.assertEqual(result_one.returncode, 0)
            summary_one = json.loads(result_one.stdout)
            self.assertTrue(summary_one["bundle_id"])
            plan_one = json.loads((out_one / "work" / "plan.json").read_text(encoding="utf-8"))
            self.assertTrue(any("effect_type" in step for step in plan_one.get("steps", [])))

        with tempfile.TemporaryDirectory() as tmp_dir_two:
            out_two = Path(tmp_dir_two) / "out"
            result_two = _run_cmd(
                [
                    "lifecycle",
                    "examples/momentum_trade.hpl",
                    "--backend",
                    "classical",
                    "--out-dir",
                    str(out_two),
                ]
            )
            self.assertEqual(result_two.returncode, 0)
            summary_two = json.loads(result_two.stdout)
            self.assertEqual(summary_one["bundle_id"], summary_two["bundle_id"])

    def test_lifecycle_qasm_bundle_contains_qasm(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "out"
            result = _run_cmd(
                [
                    "lifecycle",
                    "examples/momentum_trade.hpl",
                    "--backend",
                    "qasm",
                    "--out-dir",
                    str(out_dir),
                ]
            )
            self.assertEqual(result.returncode, 0)
            summary = json.loads(result.stdout)
            bundle_path = Path(summary["bundle_path"])
            manifest = json.loads((bundle_path / "bundle_manifest.json").read_text(encoding="utf-8"))
            roles = {entry["role"] for entry in manifest["artifacts"]}
            self.assertIn("qasm", roles)

    def test_lifecycle_refusal_with_missing_anchor(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "out"
            missing_anchor = out_dir / "missing.anchor.json"
            result = _run_cmd(
                [
                    "lifecycle",
                    "examples/momentum_trade.hpl",
                    "--backend",
                    "classical",
                    "--out-dir",
                    str(out_dir),
                    "--require-epoch",
                    "--anchor",
                    str(missing_anchor),
                ]
            )
            self.assertEqual(result.returncode, 0)
            summary = json.loads(result.stdout)
            self.assertFalse(summary["ok"])
            self.assertTrue(Path(summary["bundle_path"]).exists())

    def test_lifecycle_refusal_emits_constraint_inversion(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "out"
            missing_anchor = out_dir / "missing.anchor.json"

            first = _run_cmd(
                [
                    "lifecycle",
                    "examples/momentum_trade.hpl",
                    "--backend",
                    "classical",
                    "--out-dir",
                    str(out_dir),
                    "--require-epoch",
                    "--anchor",
                    str(missing_anchor),
                    "--constraint-inversion-v1",
                ]
            )
            self.assertEqual(first.returncode, 0)
            first_summary = json.loads(first.stdout)
            self.assertFalse(first_summary["ok"])
            first_bundle = Path(first_summary["bundle_path"])
            first_manifest = (first_bundle / "bundle_manifest.json").read_bytes()
            roles = {entry["role"] for entry in json.loads(first_manifest)["artifacts"]}
            self.assertIn("constraint_witness", roles)
            self.assertIn("dual_proposal", roles)

            second = _run_cmd(
                [
                    "lifecycle",
                    "examples/momentum_trade.hpl",
                    "--backend",
                    "classical",
                    "--out-dir",
                    str(out_dir),
                    "--require-epoch",
                    "--anchor",
                    str(missing_anchor),
                    "--constraint-inversion-v1",
                ]
            )
            self.assertEqual(second.returncode, 0)
            second_summary = json.loads(second.stdout)
            second_bundle = Path(second_summary["bundle_path"])
            second_manifest = (second_bundle / "bundle_manifest.json").read_bytes()
            self.assertEqual(first_manifest, second_manifest)

    def test_bundle_quantum_semantics_refusal(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "out"
            program_ir = out_dir / "program.ir.json"
            out_dir.mkdir(parents=True, exist_ok=True)
            program_ir.write_text("{}", encoding="utf-8")

            result = _run_cmd(
                [
                    "bundle",
                    "--out-dir",
                    str(out_dir),
                    "--program-ir",
                    str(program_ir),
                    "--quantum-semantics-v1",
                ]
            )
            self.assertEqual(result.returncode, 0)
            summary = json.loads(result.stdout)
            self.assertFalse(summary["ok"])
            self.assertTrue(summary["errors"])

    def test_lifecycle_backend_token_refusal(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "out"
            result = _run_cmd(
                [
                    "lifecycle",
                    "examples/momentum_trade.hpl",
                    "--backend",
                    "qasm",
                    "--out-dir",
                    str(out_dir),
                    "--allowed-backends",
                    "CLASSICAL",
                    "--constraint-inversion-v1",
                ]
            )
            self.assertEqual(result.returncode, 0)
            summary = json.loads(result.stdout)
            self.assertFalse(summary["ok"])
            bundle = Path(summary["bundle_path"]) / "bundle_manifest.json"
            manifest = json.loads(bundle.read_text(encoding="utf-8"))
            roles = {entry["role"] for entry in manifest["artifacts"]}
            self.assertIn("constraint_witness", roles)
            self.assertIn("dual_proposal", roles)

    def test_lifecycle_legacy_path(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "out"
            result = _run_cmd(
                [
                    "lifecycle",
                    "examples/momentum_trade.hpl",
                    "--backend",
                    "classical",
                    "--out-dir",
                    str(out_dir),
                    "--legacy",
                ]
            )
            self.assertEqual(result.returncode, 0)
            plan = json.loads((out_dir / "work" / "plan.json").read_text(encoding="utf-8"))
            self.assertFalse(any("effect_type" in step for step in plan.get("steps", [])))


if __name__ == "__main__":
    unittest.main()
