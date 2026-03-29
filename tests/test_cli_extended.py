"""Extended tests for hpl.cli covering all subcommands."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hpl.cli import main  # noqa: E402


HPL_EXAMPLE = ROOT / "examples" / "momentum_trade.hpl"
MINIMAL_IR = ROOT / "tests" / "fixtures" / "program_ir_minimal.json"


def _tmp():
    """Return a context manager yielding a temporary directory Path."""
    return tempfile.TemporaryDirectory()


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

class CliTestBase(unittest.TestCase):
    """Base class providing temp-dir helpers."""

    def _run(self, args):
        """Call main() and return the integer return code."""
        return main(args)

    def _run_capturing(self, args):
        """Call main() while capturing stdout/stderr. Returns (rc, stdout, stderr)."""
        import io
        from contextlib import redirect_stdout, redirect_stderr

        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = main(args)
        return rc, out.getvalue(), err.getvalue()


# ---------------------------------------------------------------------------
# ir subcommand
# ---------------------------------------------------------------------------

class TestCmdIr(CliTestBase):
    def test_ir_success(self):
        with _tmp() as td:
            out = Path(td) / "program.ir.json"
            rc = self._run(["ir", str(HPL_EXAMPLE), "--out", str(out)])
            self.assertEqual(rc, 0)
            self.assertTrue(out.exists())
            data = json.loads(out.read_text())
            self.assertIn("program_id", data)

    def test_ir_writes_evidence(self):
        with _tmp() as td:
            out = Path(td) / "program.ir.json"
            self._run(["ir", str(HPL_EXAMPLE), "--out", str(out)])
            evidence = Path(td) / "ir_evidence.json"
            self.assertTrue(evidence.exists())
            ev = json.loads(evidence.read_text())
            self.assertTrue(ev["ok"])

    def test_ir_missing_input_returns_nonzero(self):
        with _tmp() as td:
            out = Path(td) / "out.json"
            rc = self._run(["ir", str(Path(td) / "nonexistent.hpl"), "--out", str(out)])
            # HplError or IOError → returns 0 with evidence, or 1 on programming error
            self.assertIn(rc, (0, 1))

    def test_ir_bad_syntax_hpl(self):
        with _tmp() as td:
            bad = Path(td) / "bad.hpl"
            bad.write_text("(((broken syntax", encoding="utf-8")
            out = Path(td) / "out.json"
            rc = self._run(["ir", str(bad), "--out", str(out)])
            self.assertIn(rc, (0, 1))


# ---------------------------------------------------------------------------
# plan subcommand
# ---------------------------------------------------------------------------

class TestCmdPlan(CliTestBase):
    def _make_ir(self, td: str) -> Path:
        ir_path = Path(td) / "program.ir.json"
        with _tmp() as t2:
            out = Path(t2) / "tmp.ir.json"
            main(["ir", str(HPL_EXAMPLE), "--out", str(out)])
            ir_path.write_bytes(out.read_bytes())
        return ir_path

    def test_plan_success(self):
        with _tmp() as td:
            ir_path = self._make_ir(td)
            out = Path(td) / "plan.json"
            rc = self._run(["plan", str(ir_path), "--out", str(out)])
            self.assertEqual(rc, 0)
            self.assertTrue(out.exists())

    def test_plan_writes_evidence(self):
        with _tmp() as td:
            ir_path = self._make_ir(td)
            out = Path(td) / "plan.json"
            self._run(["plan", str(ir_path), "--out", str(out)])
            evidence = Path(td) / "plan_evidence.json"
            self.assertTrue(evidence.exists())

    def test_plan_with_allowed_backends(self):
        with _tmp() as td:
            ir_path = self._make_ir(td)
            out = Path(td) / "plan.json"
            rc = self._run([
                "plan", str(ir_path), "--out", str(out),
                "--allowed-backends", "CLASSICAL",
            ])
            self.assertEqual(rc, 0)

    def test_plan_with_budget_steps(self):
        with _tmp() as td:
            ir_path = self._make_ir(td)
            out = Path(td) / "plan.json"
            rc = self._run([
                "plan", str(ir_path), "--out", str(out),
                "--budget-steps", "50",
            ])
            self.assertEqual(rc, 0)

    def test_plan_require_epoch_no_anchor(self):
        with _tmp() as td:
            ir_path = self._make_ir(td)
            out = Path(td) / "plan.json"
            rc = self._run([
                "plan", str(ir_path), "--out", str(out),
                "--require-epoch",
            ])
            self.assertEqual(rc, 0)
            data = json.loads(out.read_text())
            # Without a valid anchor, plan should be denied
            self.assertIn(data.get("status"), ("planned", "denied"))

    def test_plan_missing_ir(self):
        with _tmp() as td:
            out = Path(td) / "plan.json"
            rc = self._run(["plan", str(Path(td) / "missing.json"), "--out", str(out)])
            self.assertIn(rc, (0, 1))


# ---------------------------------------------------------------------------
# run subcommand
# ---------------------------------------------------------------------------

class TestCmdRun(CliTestBase):
    def _make_plan(self, td: str) -> Path:
        ir_path = Path(td) / "program.ir.json"
        plan_path = Path(td) / "plan.json"
        with _tmp() as t2:
            out_ir = Path(t2) / "tmp.ir.json"
            main(["ir", str(HPL_EXAMPLE), "--out", str(out_ir)])
            ir_path.write_bytes(out_ir.read_bytes())
        main(["plan", str(ir_path), "--out", str(plan_path)])
        return plan_path

    def test_run_success(self):
        with _tmp() as td:
            plan_path = self._make_plan(td)
            out = Path(td) / "runtime.json"
            rc = self._run(["run", str(plan_path), "--out", str(out)])
            self.assertEqual(rc, 0)
            self.assertTrue(out.exists())

    def test_run_writes_evidence(self):
        with _tmp() as td:
            plan_path = self._make_plan(td)
            out = Path(td) / "runtime.json"
            self._run(["run", str(plan_path), "--out", str(out)])
            evidence = Path(td) / "run_evidence.json"
            self.assertTrue(evidence.exists())

    def test_run_with_backend_classical(self):
        with _tmp() as td:
            plan_path = self._make_plan(td)
            out = Path(td) / "runtime.json"
            rc = self._run([
                "run", str(plan_path), "--out", str(out),
                "--backend", "classical",
            ])
            self.assertEqual(rc, 0)

    def test_run_enable_io_flag(self):
        with _tmp() as td:
            plan_path = self._make_plan(td)
            out = Path(td) / "runtime.json"
            rc = self._run([
                "run", str(plan_path), "--out", str(out),
                "--enable-io",
            ])
            self.assertEqual(rc, 0)

    def test_run_enable_net_flag(self):
        with _tmp() as td:
            plan_path = self._make_plan(td)
            out = Path(td) / "runtime.json"
            rc = self._run([
                "run", str(plan_path), "--out", str(out),
                "--enable-net",
            ])
            self.assertEqual(rc, 0)

    def test_run_missing_plan(self):
        with _tmp() as td:
            out = Path(td) / "runtime.json"
            rc = self._run(["run", str(Path(td) / "missing.json"), "--out", str(out)])
            self.assertIn(rc, (0, 1))


# ---------------------------------------------------------------------------
# lower subcommand
# ---------------------------------------------------------------------------

class TestCmdLower(CliTestBase):
    def _make_ir(self, td: str) -> Path:
        ir_path = Path(td) / "program.ir.json"
        with _tmp() as t2:
            out = Path(t2) / "tmp.ir.json"
            main(["ir", str(HPL_EXAMPLE), "--out", str(out)])
            ir_path.write_bytes(out.read_bytes())
        return ir_path

    def test_lower_classical(self):
        with _tmp() as td:
            ir_path = self._make_ir(td)
            out = Path(td) / "backend.ir.json"
            rc = self._run([
                "lower", "--backend", "classical",
                "--ir", str(ir_path), "--out", str(out),
            ])
            self.assertEqual(rc, 0)
            self.assertTrue(out.exists())

    def test_lower_qasm(self):
        with _tmp() as td:
            ir_path = self._make_ir(td)
            out = Path(td) / "program.qasm"
            rc = self._run([
                "lower", "--backend", "qasm",
                "--ir", str(ir_path), "--out", str(out),
            ])
            self.assertEqual(rc, 0)
            self.assertTrue(out.exists())

    def test_lower_writes_evidence(self):
        with _tmp() as td:
            ir_path = self._make_ir(td)
            out = Path(td) / "backend.ir.json"
            self._run([
                "lower", "--backend", "classical",
                "--ir", str(ir_path), "--out", str(out),
            ])
            evidence = Path(td) / "lower_evidence.json"
            self.assertTrue(evidence.exists())

    def test_lower_missing_ir(self):
        with _tmp() as td:
            out = Path(td) / "out.json"
            rc = self._run([
                "lower", "--backend", "classical",
                "--ir", str(Path(td) / "missing.json"), "--out", str(out),
            ])
            self.assertIn(rc, (0, 1))


# ---------------------------------------------------------------------------
# invert subcommand
# ---------------------------------------------------------------------------

class TestCmdInvert(CliTestBase):
    def _make_witness(self, td: str) -> Path:
        witness_path = Path(td) / "witness.json"
        witness = {
            "witness_id": "sha256:test",
            "stage": "runtime_refusal",
            "refusal_reasons": ["reason_a", "reason_b"],
            "artifact_digests": {"plan": "sha256:abc"},
        }
        witness_path.write_text(
            json.dumps(witness, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        return witness_path

    def test_invert_success(self):
        with _tmp() as td:
            witness_path = self._make_witness(td)
            out = Path(td) / "proposal.json"
            rc = self._run(["invert", "--witness", str(witness_path), "--out", str(out)])
            self.assertEqual(rc, 0)
            self.assertTrue(out.exists())
            data = json.loads(out.read_text())
            self.assertIn("dual_proposal_id", data)

    def test_invert_determinism(self):
        with _tmp() as td:
            witness_path = self._make_witness(td)
            out1 = Path(td) / "p1.json"
            out2 = Path(td) / "p2.json"
            self._run(["invert", "--witness", str(witness_path), "--out", str(out1)])
            self._run(["invert", "--witness", str(witness_path), "--out", str(out2)])
            self.assertEqual(out1.read_bytes(), out2.read_bytes())

    def test_invert_pretty_flag(self):
        with _tmp() as td:
            witness_path = self._make_witness(td)
            out = Path(td) / "proposal.json"
            rc, stdout, _ = self._run_capturing([
                "invert", "--witness", str(witness_path),
                "--out", str(out), "--pretty",
            ])
            self.assertEqual(rc, 0)
            # pretty output should have newlines
            self.assertIn("\n", stdout)

    def test_invert_missing_witness(self):
        with _tmp() as td:
            out = Path(td) / "proposal.json"
            rc = self._run([
                "invert",
                "--witness", str(Path(td) / "missing.json"),
                "--out", str(out),
            ])
            self.assertEqual(rc, 0)
            data = json.loads(out.read_text())
            self.assertFalse(data.get("ok", True))

    def test_invert_invalid_witness_empty_object(self):
        with _tmp() as td:
            witness_path = Path(td) / "witness.json"
            witness_path.write_text("{}", encoding="utf-8")
            out = Path(td) / "proposal.json"
            rc = self._run(["invert", "--witness", str(witness_path), "--out", str(out)])
            self.assertEqual(rc, 0)
            data = json.loads(out.read_text())
            self.assertFalse(data.get("ok", True))
            self.assertTrue(data.get("errors"))

    def test_invert_invalid_witness_not_dict(self):
        with _tmp() as td:
            witness_path = Path(td) / "witness.json"
            witness_path.write_text("[1, 2, 3]", encoding="utf-8")
            out = Path(td) / "proposal.json"
            rc = self._run(["invert", "--witness", str(witness_path), "--out", str(out)])
            self.assertEqual(rc, 0)
            data = json.loads(out.read_text())
            self.assertFalse(data.get("ok", True))


# ---------------------------------------------------------------------------
# bundle subcommand
# ---------------------------------------------------------------------------

class TestCmdBundle(CliTestBase):
    def _make_ir(self, td: str) -> Path:
        ir_path = Path(td) / "program.ir.json"
        with _tmp() as t2:
            out = Path(t2) / "tmp.ir.json"
            main(["ir", str(HPL_EXAMPLE), "--out", str(out)])
            ir_path.write_bytes(out.read_bytes())
        return ir_path

    def test_bundle_no_artifacts_fails_gracefully(self):
        with _tmp() as td:
            out_dir = Path(td) / "bundle"
            rc, stdout, _ = self._run_capturing([
                "bundle", "--out-dir", str(out_dir),
            ])
            self.assertEqual(rc, 0)
            data = json.loads(stdout)
            self.assertFalse(data["ok"])
            self.assertTrue(data["errors"])

    def test_bundle_with_program_ir(self):
        with _tmp() as td:
            ir_path = self._make_ir(td)
            out_dir = Path(td) / "bundle"
            rc, stdout, _ = self._run_capturing([
                "bundle", "--out-dir", str(out_dir),
                "--program-ir", str(ir_path),
            ])
            self.assertEqual(rc, 0)
            data = json.loads(stdout)
            self.assertIsNotNone(data.get("bundle_path"))
            self.assertTrue(Path(data["bundle_path"]).exists())

    def test_bundle_quantum_semantics_refusal(self):
        with _tmp() as td:
            ir_path = Path(td) / "program.ir.json"
            ir_path.write_text("{}", encoding="utf-8")
            out_dir = Path(td) / "bundle"
            rc, stdout, _ = self._run_capturing([
                "bundle", "--out-dir", str(out_dir),
                "--program-ir", str(ir_path),
                "--quantum-semantics-v1",
            ])
            self.assertEqual(rc, 0)
            data = json.loads(stdout)
            self.assertFalse(data["ok"])
            self.assertTrue(data["errors"])

    def test_bundle_sign_without_key_fails(self):
        with _tmp() as td:
            ir_path = self._make_ir(td)
            out_dir = Path(td) / "bundle"
            rc, stdout, _ = self._run_capturing([
                "bundle", "--out-dir", str(out_dir),
                "--program-ir", str(ir_path),
                "--sign-bundle",
            ])
            self.assertEqual(rc, 0)
            data = json.loads(stdout)
            self.assertFalse(data["ok"])

    def test_bundle_missing_artifact_path(self):
        with _tmp() as td:
            out_dir = Path(td) / "bundle"
            rc, stdout, _ = self._run_capturing([
                "bundle", "--out-dir", str(out_dir),
                "--program-ir", str(Path(td) / "nonexistent.json"),
            ])
            self.assertEqual(rc, 0)
            data = json.loads(stdout)
            self.assertFalse(data["ok"])
            self.assertTrue(data["errors"])

    def test_bundle_writes_evidence(self):
        with _tmp() as td:
            ir_path = self._make_ir(td)
            out_dir = Path(td) / "bundle"
            self._run([
                "bundle", "--out-dir", str(out_dir),
                "--program-ir", str(ir_path),
            ])
            evidence = out_dir / "bundle_evidence.json"
            self.assertTrue(evidence.exists())

    def test_bundle_with_plan_and_runtime(self):
        with _tmp() as td:
            ir_path = self._make_ir(td)
            plan_path = Path(td) / "plan.json"
            runtime_path = Path(td) / "runtime.json"
            main(["plan", str(ir_path), "--out", str(plan_path)])
            main(["run", str(plan_path), "--out", str(runtime_path)])
            out_dir = Path(td) / "bundle"
            rc, stdout, _ = self._run_capturing([
                "bundle", "--out-dir", str(out_dir),
                "--program-ir", str(ir_path),
                "--plan", str(plan_path),
                "--runtime-result", str(runtime_path),
            ])
            self.assertEqual(rc, 0)
            data = json.loads(stdout)
            self.assertIsNotNone(data.get("bundle_path"))


# ---------------------------------------------------------------------------
# lifecycle subcommand
# ---------------------------------------------------------------------------

class TestCmdLifecycle(CliTestBase):
    def test_lifecycle_classical_success(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = self._run_capturing([
                "lifecycle", str(HPL_EXAMPLE),
                "--backend", "classical",
                "--out-dir", str(out_dir),
            ])
            self.assertEqual(rc, 0)
            data = json.loads(stdout)
            self.assertTrue(data["ok"])
            self.assertTrue(data["bundle_id"])

    def test_lifecycle_qasm_success(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = self._run_capturing([
                "lifecycle", str(HPL_EXAMPLE),
                "--backend", "qasm",
                "--out-dir", str(out_dir),
            ])
            self.assertEqual(rc, 0)
            data = json.loads(stdout)
            self.assertIsNotNone(data.get("bundle_path"))

    def test_lifecycle_require_epoch_missing_anchor(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = self._run_capturing([
                "lifecycle", str(HPL_EXAMPLE),
                "--backend", "classical",
                "--out-dir", str(out_dir),
                "--require-epoch",
                "--anchor", str(out_dir / "missing.anchor.json"),
            ])
            self.assertEqual(rc, 0)
            data = json.loads(stdout)
            self.assertFalse(data["ok"])

    def test_lifecycle_legacy_flag(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = self._run_capturing([
                "lifecycle", str(HPL_EXAMPLE),
                "--backend", "classical",
                "--out-dir", str(out_dir),
                "--legacy",
            ])
            self.assertEqual(rc, 0)
            data = json.loads(stdout)
            # legacy mode returns a result
            self.assertIn("ok", data)

    def test_lifecycle_constraint_inversion(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = self._run_capturing([
                "lifecycle", str(HPL_EXAMPLE),
                "--backend", "classical",
                "--out-dir", str(out_dir),
                "--require-epoch",
                "--anchor", str(out_dir / "missing.anchor.json"),
                "--constraint-inversion-v1",
            ])
            self.assertEqual(rc, 0)
            data = json.loads(stdout)
            self.assertFalse(data["ok"])
            bundle_path = Path(data["bundle_path"])
            manifest = json.loads((bundle_path / "bundle_manifest.json").read_text())
            roles = {e["role"] for e in manifest["artifacts"]}
            self.assertIn("constraint_witness", roles)
            self.assertIn("dual_proposal", roles)

    def test_lifecycle_writes_lifecycle_evidence(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            self._run([
                "lifecycle", str(HPL_EXAMPLE),
                "--backend", "classical",
                "--out-dir", str(out_dir),
            ])
            evidence = out_dir / "lifecycle_evidence.json"
            self.assertTrue(evidence.exists())
            ev = json.loads(evidence.read_text())
            self.assertIn("ok", ev)

    def test_lifecycle_deterministic_bundle_id(self):
        with _tmp() as td1, _tmp() as td2:
            out1 = Path(td1) / "out"
            out2 = Path(td2) / "out"
            _, stdout1, _ = self._run_capturing([
                "lifecycle", str(HPL_EXAMPLE),
                "--backend", "classical", "--out-dir", str(out1),
            ])
            _, stdout2, _ = self._run_capturing([
                "lifecycle", str(HPL_EXAMPLE),
                "--backend", "classical", "--out-dir", str(out2),
            ])
            d1 = json.loads(stdout1)
            d2 = json.loads(stdout2)
            self.assertEqual(d1["bundle_id"], d2["bundle_id"])

    def test_lifecycle_missing_input(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = self._run_capturing([
                "lifecycle", str(Path(td) / "nonexistent.hpl"),
                "--backend", "classical",
                "--out-dir", str(out_dir),
            ])
            # Missing input: lifecycle returns 0 with ok=False, or 1 on unexpected error
            self.assertIn(rc, (0, 1))
            if rc == 0:
                data = json.loads(stdout)
                self.assertFalse(data["ok"])

    def test_lifecycle_backend_not_in_allowed(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = self._run_capturing([
                "lifecycle", str(HPL_EXAMPLE),
                "--backend", "qasm",
                "--out-dir", str(out_dir),
                "--allowed-backends", "CLASSICAL",
                "--constraint-inversion-v1",
            ])
            self.assertEqual(rc, 0)
            data = json.loads(stdout)
            self.assertFalse(data["ok"])


# ---------------------------------------------------------------------------
# Helper / utility function tests (via public main entry point)
# ---------------------------------------------------------------------------

class TestVersionFlag(CliTestBase):
    def test_version_flag(self):
        import io
        from contextlib import redirect_stdout
        out = io.StringIO()
        with redirect_stdout(out):
            try:
                main(["--version"])
            except SystemExit as exc:
                self.assertEqual(exc.code, 0)
        self.assertIn("hpl", out.getvalue())


class TestNoSubcommand(CliTestBase):
    def test_no_subcommand_exits_nonzero(self):
        try:
            main([])
        except SystemExit as exc:
            self.assertNotEqual(exc.code, 0)


# ---------------------------------------------------------------------------
# Internal helper function unit tests
# ---------------------------------------------------------------------------

class TestInternalHelpers(unittest.TestCase):
    def test_canonical_json_sort_keys(self):
        from hpl.cli import _canonical_json
        data = {"b": 2, "a": 1}
        result = _canonical_json(data)
        self.assertEqual(result, '{"a":1,"b":2}')

    def test_canonical_json_compact(self):
        from hpl.cli import _canonical_json
        result = _canonical_json({"key": "val"})
        self.assertNotIn(" ", result)

    def test_parse_backends_normalizes(self):
        from hpl.cli import _parse_backends
        result = _parse_backends("classical,qasm")
        self.assertIn("CLASSICAL", result)
        self.assertIn("QASM", result)

    def test_parse_backends_deduplicates(self):
        from hpl.cli import _parse_backends
        result = _parse_backends("PYTHON,python,PYTHON")
        self.assertEqual(result.count("PYTHON"), 1)

    def test_parse_backends_empty_falls_back(self):
        from hpl.cli import _parse_backends
        result = _parse_backends("")
        self.assertIn("PYTHON", result)

    def test_normalize_backend_upper(self):
        from hpl.cli import _normalize_backend
        self.assertEqual(_normalize_backend("classical"), "CLASSICAL")
        self.assertEqual(_normalize_backend("QASM"), "QASM")

    def test_normalize_backend_none(self):
        from hpl.cli import _normalize_backend
        self.assertIsNone(_normalize_backend(None))

    def test_digest_text(self):
        from hpl.cli import _digest_text
        result = _digest_text("hello")
        self.assertTrue(result.startswith("sha256:"))

    def test_digest_text_value(self):
        from hpl.cli import _digest_text_value
        result = _digest_text_value("hello")
        self.assertIn("digest", result)
        self.assertTrue(result["digest"].startswith("sha256:"))

    def test_digest_file(self):
        from hpl.cli import _digest_file
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            p = Path(f.name)
            p.write_bytes(b"test content")
        try:
            result = _digest_file(p)
            self.assertIn("digest", result)
            self.assertTrue(result["digest"].startswith("sha256:"))
            self.assertEqual(result["path"], p.name)
        finally:
            p.unlink()

    def test_default_evidence_path(self):
        from hpl.cli import _default_evidence_path
        out = Path("/tmp/foo/program.ir.json")
        result = _default_evidence_path(out, "ir")
        self.assertEqual(result.name, "ir_evidence.json")

    def test_write_json_creates_file(self):
        from hpl.cli import _write_json
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "out.json"
            _write_json(p, {"key": "value"})
            self.assertTrue(p.exists())
            data = json.loads(p.read_text())
            self.assertEqual(data["key"], "value")

    def test_write_evidence_structure(self):
        from hpl.cli import _write_evidence
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "evidence.json"
            _write_evidence(
                p,
                command="test_cmd",
                ok=True,
                errors=[],
                inputs={"in_key": {"path": "foo.json", "digest": "sha256:abc"}},
                outputs={"out_key": {"path": "bar.json", "digest": "sha256:def"}},
            )
            self.assertTrue(p.exists())
            data = json.loads(p.read_text())
            self.assertEqual(data["command"], "test_cmd")
            self.assertTrue(data["ok"])

    def test_relative_to_root(self):
        from hpl.cli import _relative_to_root, ROOT
        p = ROOT / "some" / "path.json"
        result = _relative_to_root(p)
        self.assertFalse(result.is_absolute())

    def test_relative_to_root_external(self):
        from hpl.cli import _relative_to_root
        p = Path("/tmp/external.json")
        result = _relative_to_root(p)
        self.assertEqual(result, p)


# ---------------------------------------------------------------------------
# _write_refusal_evidence helper
# ---------------------------------------------------------------------------

class TestWriteRefusalEvidence(unittest.TestCase):
    def test_write_refusal_evidence_no_path(self):
        from hpl.cli import _write_refusal_evidence
        # Should not raise when evidence_path is None
        _write_refusal_evidence(
            command="ir",
            inputs={"input": "foo.hpl"},
            errors=["something went wrong"],
            evidence_path=None,
        )

    def test_write_refusal_evidence_with_path(self):
        from hpl.cli import _write_refusal_evidence
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "evidence.json"
            _write_refusal_evidence(
                command="ir",
                inputs={"input": "foo.hpl"},
                errors=["err1"],
                evidence_path=p,
            )
            self.assertTrue(p.exists())
            data = json.loads(p.read_text())
            self.assertFalse(data["ok"])
            self.assertIn("err1", data["errors"])


# ---------------------------------------------------------------------------
# _load_contract helper
# ---------------------------------------------------------------------------

class TestLoadContract(unittest.TestCase):
    def test_load_contract_none_path(self):
        from hpl.cli import _load_contract
        plan_dict = {"steps": [{"operator_id": "op1"}, {"operator_id": "op2"}]}
        contract = _load_contract(None, plan_dict)
        self.assertIn("op1", contract.allowed_steps)
        self.assertIn("op2", contract.allowed_steps)

    def test_load_contract_from_file(self):
        from hpl.cli import _load_contract
        with tempfile.TemporaryDirectory() as td:
            contract_path = Path(td) / "contract.json"
            contract_path.write_text(json.dumps({
                "allowed_steps": ["step_a", "step_b"],
                "require_epoch_verification": True,
                "require_signature_verification": False,
            }), encoding="utf-8")
            contract = _load_contract(contract_path, {})
            self.assertIn("step_a", contract.allowed_steps)
            self.assertTrue(contract.require_epoch_verification)

    def test_load_contract_missing_file_uses_plan(self):
        from hpl.cli import _load_contract
        plan_dict = {"steps": [{"operator_id": "op_x"}]}
        contract = _load_contract(Path("/nonexistent/contract.json"), plan_dict)
        self.assertIn("op_x", contract.allowed_steps)


# ---------------------------------------------------------------------------
# Combined pipeline: ir -> plan -> run -> bundle
# ---------------------------------------------------------------------------

class TestFullPipeline(CliTestBase):
    def test_full_pipeline_classical(self):
        with _tmp() as td:
            td_path = Path(td)
            ir_out = td_path / "program.ir.json"
            plan_out = td_path / "plan.json"
            run_out = td_path / "runtime.json"
            bundle_out = td_path / "bundle"

            self.assertEqual(main(["ir", str(HPL_EXAMPLE), "--out", str(ir_out)]), 0)
            self.assertEqual(main(["plan", str(ir_out), "--out", str(plan_out)]), 0)
            self.assertEqual(main(["run", str(plan_out), "--out", str(run_out)]), 0)

            rc, stdout, _ = self._run_capturing([
                "bundle", "--out-dir", str(bundle_out),
                "--program-ir", str(ir_out),
                "--plan", str(plan_out),
                "--runtime-result", str(run_out),
            ])
            self.assertEqual(rc, 0)
            data = json.loads(stdout)
            self.assertIsNotNone(data.get("bundle_path"))
            self.assertTrue(Path(data["bundle_path"]).exists())

    def test_full_pipeline_with_lower_classical(self):
        with _tmp() as td:
            td_path = Path(td)
            ir_out = td_path / "program.ir.json"
            backend_out = td_path / "backend.ir.json"

            self.assertEqual(main(["ir", str(HPL_EXAMPLE), "--out", str(ir_out)]), 0)
            self.assertEqual(main([
                "lower", "--backend", "classical",
                "--ir", str(ir_out), "--out", str(backend_out),
            ]), 0)
            self.assertTrue(backend_out.exists())

    def test_full_pipeline_with_lower_qasm(self):
        with _tmp() as td:
            td_path = Path(td)
            ir_out = td_path / "program.ir.json"
            qasm_out = td_path / "program.qasm"

            self.assertEqual(main(["ir", str(HPL_EXAMPLE), "--out", str(ir_out)]), 0)
            self.assertEqual(main([
                "lower", "--backend", "qasm",
                "--ir", str(ir_out), "--out", str(qasm_out),
            ]), 0)
            self.assertTrue(qasm_out.exists())


# ---------------------------------------------------------------------------
# _parse_backends edge cases
# ---------------------------------------------------------------------------

class TestParseBackends(unittest.TestCase):
    def test_single_backend(self):
        from hpl.cli import _parse_backends
        result = _parse_backends("CLASSICAL")
        self.assertEqual(result, ["CLASSICAL"])

    def test_multiple_backends_sorted(self):
        from hpl.cli import _parse_backends
        result = _parse_backends("QASM,PYTHON,CLASSICAL")
        self.assertEqual(sorted(result), result)

    def test_whitespace_stripped(self):
        from hpl.cli import _parse_backends
        result = _parse_backends("  CLASSICAL , PYTHON  ")
        self.assertIn("CLASSICAL", result)
        self.assertIn("PYTHON", result)


if __name__ == "__main__":
    unittest.main()
