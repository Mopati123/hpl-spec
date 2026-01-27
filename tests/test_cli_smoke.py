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


class CliSmokeTests(unittest.TestCase):
    def test_cli_end_to_end_and_determinism(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            ir_path = tmp / "program.ir.json"
            plan_path = tmp / "plan.json"
            run_path = tmp / "run.json"
            lower_path = tmp / "lower.json"
            qasm_path = tmp / "program.qasm"

            # IR
            subprocess.check_call(
                CLI + ["ir", "examples/momentum_trade.hpl", "--out", str(ir_path)],
                cwd=ROOT,
                env=_env(),
            )
            ir_evidence = ir_path.with_name("ir_evidence.json")
            self.assertTrue(ir_path.exists())
            self.assertTrue(ir_evidence.exists())

            ir_first = ir_path.read_bytes()
            ev_first = ir_evidence.read_bytes()

            subprocess.check_call(
                CLI + ["ir", "examples/momentum_trade.hpl", "--out", str(ir_path)],
                cwd=ROOT,
                env=_env(),
            )
            self.assertEqual(ir_first, ir_path.read_bytes())
            self.assertEqual(ev_first, ir_evidence.read_bytes())

            # Plan (refusal path with missing anchor)
            subprocess.check_call(
                CLI
                + [
                    "plan",
                    str(ir_path),
                    "--out",
                    str(plan_path),
                    "--require-epoch",
                    "--anchor",
                    str(tmp / "missing.anchor.json"),
                ],
                cwd=ROOT,
                env=_env(),
            )
            plan_evidence = plan_path.with_name("plan_evidence.json")
            self.assertTrue(plan_path.exists())
            self.assertTrue(plan_evidence.exists())
            evidence = json.loads(plan_evidence.read_text(encoding="utf-8"))
            self.assertFalse(evidence["ok"])

            # Plan success
            subprocess.check_call(
                CLI + ["plan", str(ir_path), "--out", str(plan_path)],
                cwd=ROOT,
                env=_env(),
            )
            plan_first = plan_path.read_bytes()
            ev_plan_first = plan_evidence.read_bytes()
            subprocess.check_call(
                CLI + ["plan", str(ir_path), "--out", str(plan_path)],
                cwd=ROOT,
                env=_env(),
            )
            self.assertEqual(plan_first, plan_path.read_bytes())
            self.assertEqual(ev_plan_first, plan_evidence.read_bytes())

            # Run
            subprocess.check_call(
                CLI + ["run", str(plan_path), "--out", str(run_path)],
                cwd=ROOT,
                env=_env(),
            )
            run_evidence = run_path.with_name("run_evidence.json")
            self.assertTrue(run_path.exists())
            self.assertTrue(run_evidence.exists())

            run_first = run_path.read_bytes()
            ev_run_first = run_evidence.read_bytes()
            subprocess.check_call(
                CLI + ["run", str(plan_path), "--out", str(run_path)],
                cwd=ROOT,
                env=_env(),
            )
            self.assertEqual(run_first, run_path.read_bytes())
            self.assertEqual(ev_run_first, run_evidence.read_bytes())

            # Lower - classical
            subprocess.check_call(
                CLI + ["lower", "--backend", "classical", "--ir", str(ir_path), "--out", str(lower_path)],
                cwd=ROOT,
                env=_env(),
            )
            lower_evidence = lower_path.with_name("lower_evidence.json")
            self.assertTrue(lower_path.exists())
            self.assertTrue(lower_evidence.exists())

            lower_first = lower_path.read_bytes()
            ev_lower_first = lower_evidence.read_bytes()
            subprocess.check_call(
                CLI + ["lower", "--backend", "classical", "--ir", str(ir_path), "--out", str(lower_path)],
                cwd=ROOT,
                env=_env(),
            )
            self.assertEqual(lower_first, lower_path.read_bytes())
            self.assertEqual(ev_lower_first, lower_evidence.read_bytes())

            # Lower - qasm
            subprocess.check_call(
                CLI + ["lower", "--backend", "qasm", "--ir", str(ir_path), "--out", str(qasm_path)],
                cwd=ROOT,
                env=_env(),
            )
            qasm_evidence = qasm_path.with_name("lower_evidence.json")
            self.assertTrue(qasm_path.exists())
            self.assertTrue(qasm_evidence.exists())


if __name__ == "__main__":
    unittest.main()
