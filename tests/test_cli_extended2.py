"""Extended CLI tests batch 2 – covering demo subcommands (lines 957-2403)."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hpl.cli import main  # noqa: E402

HPL_EXAMPLE = ROOT / "examples" / "momentum_trade.hpl"

# fixture paths
FIXTURE_DIR = ROOT / "tests" / "fixtures"
TRADING_FIXTURE = FIXTURE_DIR / "trading" / "price_series_simple.json"
TRADING_POLICY = FIXTURE_DIR / "trading" / "policy_safe.json"
SHADOW_POLICY = FIXTURE_DIR / "trading" / "shadow_policy_safe.json"
SHADOW_MODEL = FIXTURE_DIR / "trading" / "shadow_model.json"
NS_STATE = FIXTURE_DIR / "pde" / "ns_state_initial.json"
NS_POLICY = FIXTURE_DIR / "pde" / "ns_policy_safe.json"
AGENT_PROPOSAL = FIXTURE_DIR / "agent_proposal_allow.json"
AGENT_POLICY = FIXTURE_DIR / "agent_policy.json"


def _tmp():
    return tempfile.TemporaryDirectory()


def _run(args):
    """Call main() capturing stdout/stderr; return (rc, stdout_str, stderr_str)."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = main(args)
    return rc, out.getvalue(), err.getvalue()


def _parse(stdout: str) -> dict:
    return json.loads(stdout)


# ---------------------------------------------------------------------------
# demo ci-governance
# ---------------------------------------------------------------------------

class TestDemoCiGovernance(unittest.TestCase):
    """Tests for _cmd_demo_ci_governance (lines 956-1128)."""

    def _base_args(self, out_dir: Path):
        return [
            "demo", "ci-governance",
            "--out-dir", str(out_dir),
            "--input", str(HPL_EXAMPLE),
            "--backend", "classical",
        ]

    def test_ci_governance_runs_and_returns_ok_false_no_signing_key(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            # no signing_key → errors, ok=False
            self.assertFalse(data["ok"])
            self.assertIsNotNone(data.get("bundle_path"))

    def test_ci_governance_bundle_dir_created(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            # bundle_path must be set even when ok=False
            self.assertIsNotNone(data.get("bundle_path"))
            bundle_path = Path(data["bundle_path"])
            self.assertTrue(bundle_path.exists())

    def test_ci_governance_manifest_written(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            bundle_path = Path(data["bundle_path"])
            manifest_path = bundle_path / "bundle_manifest.json"
            self.assertTrue(manifest_path.exists())
            manifest = json.loads(manifest_path.read_text())
            self.assertIn("artifacts", manifest)

    def test_ci_governance_constraint_witness_emitted_on_refusal(self):
        """No signing key means refusal → constraint_witness + dual_proposal in bundle."""
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            self.assertFalse(data["ok"])
            bundle_path = Path(data["bundle_path"])
            manifest = json.loads((bundle_path / "bundle_manifest.json").read_text())
            roles = {e["role"] for e in manifest["artifacts"]}
            self.assertIn("constraint_witness", roles)
            self.assertIn("dual_proposal", roles)

    def test_ci_governance_hpl_error_returns_nonzero_or_ok_false(self):
        """Feeding a missing HPL file triggers an error (rc=0 with ok=False, or rc=1)."""
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run([
                "demo", "ci-governance",
                "--out-dir", str(out_dir),
                "--input", str(Path(td) / "nonexistent.hpl"),
                "--backend", "classical",
            ])
            self.assertIn(rc, (0, 1))
            if rc == 0:
                data = _parse(stdout)
                self.assertFalse(data["ok"])


# ---------------------------------------------------------------------------
# demo agent-governance
# ---------------------------------------------------------------------------

class TestDemoAgentGovernance(unittest.TestCase):
    """Tests for _cmd_demo_agent_governance (lines 1131-1299)."""

    def _base_args(self, out_dir: Path):
        return [
            "demo", "agent-governance",
            "--out-dir", str(out_dir),
            "--input", str(HPL_EXAMPLE),
            "--proposal", str(AGENT_PROPOSAL),
            "--policy", str(AGENT_POLICY),
        ]

    def test_agent_governance_runs(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            self.assertIn("ok", data)
            self.assertIsNotNone(data.get("bundle_path"))

    def test_agent_governance_bundle_manifest_exists(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            bundle_path = Path(data["bundle_path"])
            manifest_path = bundle_path / "bundle_manifest.json"
            self.assertTrue(manifest_path.exists())

    def test_agent_governance_no_signing_key_errors(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            # no signing key → error in errors list
            self.assertFalse(data["ok"])
            self.assertTrue(data["errors"])

    def test_agent_governance_missing_proposal_hpl_error(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run([
                "demo", "agent-governance",
                "--out-dir", str(out_dir),
                "--input", str(Path(td) / "nonexistent.hpl"),
                "--proposal", str(AGENT_PROPOSAL),
                "--policy", str(AGENT_POLICY),
            ])
            self.assertIn(rc, (0, 1))
            if rc == 0:
                data = _parse(stdout)
                self.assertFalse(data["ok"])

    def test_agent_governance_invalid_proposal_json(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            bad_proposal = Path(td) / "bad.json"
            bad_proposal.write_text("{not valid json", encoding="utf-8")
            rc, stdout, _ = _run([
                "demo", "agent-governance",
                "--out-dir", str(out_dir),
                "--input", str(HPL_EXAMPLE),
                "--proposal", str(bad_proposal),
                "--policy", str(AGENT_POLICY),
            ])
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            self.assertFalse(data["ok"])

    def test_agent_governance_invalid_policy_json(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            bad_policy = Path(td) / "bad_policy.json"
            bad_policy.write_text("{not valid json", encoding="utf-8")
            rc, stdout, _ = _run([
                "demo", "agent-governance",
                "--out-dir", str(out_dir),
                "--input", str(HPL_EXAMPLE),
                "--proposal", str(AGENT_PROPOSAL),
                "--policy", str(bad_policy),
            ])
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            self.assertFalse(data["ok"])

    def test_agent_governance_constraint_witness_on_refusal(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            # No signing key → refusal → constraint artifacts
            self.assertFalse(data["ok"])
            bundle_path = Path(data["bundle_path"])
            manifest = json.loads((bundle_path / "bundle_manifest.json").read_text())
            roles = {e["role"] for e in manifest["artifacts"]}
            self.assertIn("constraint_witness", roles)
            self.assertIn("dual_proposal", roles)


# ---------------------------------------------------------------------------
# demo trading-paper
# ---------------------------------------------------------------------------

class TestDemoTradingPaper(unittest.TestCase):
    """Tests for _cmd_demo_trading_paper (lines 1302-1465)."""

    def _base_args(self, out_dir: Path):
        return [
            "demo", "trading-paper",
            "--out-dir", str(out_dir),
            "--input", str(HPL_EXAMPLE),
            "--market-fixture", str(TRADING_FIXTURE),
            "--policy", str(TRADING_POLICY),
        ]

    def test_trading_paper_runs(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            self.assertIn("ok", data)
            self.assertIsNotNone(data.get("bundle_path"))

    def test_trading_paper_bundle_exists(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            self.assertTrue(Path(data["bundle_path"]).exists())

    def test_trading_paper_no_signing_key_errors(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            self.assertFalse(data["ok"])
            self.assertTrue(any("signing_key" in e for e in data["errors"]))

    def test_trading_paper_constraint_inversion_flag(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir) + ["--constraint-inversion-v1"])
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            self.assertIn("ok", data)

    def test_trading_paper_hpl_error_on_missing_input(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run([
                "demo", "trading-paper",
                "--out-dir", str(out_dir),
                "--input", str(Path(td) / "nonexistent.hpl"),
                "--market-fixture", str(TRADING_FIXTURE),
                "--policy", str(TRADING_POLICY),
            ])
            self.assertIn(rc, (0, 1))
            if rc == 0:
                data = _parse(stdout)
                self.assertFalse(data["ok"])


# ---------------------------------------------------------------------------
# demo trading-shadow
# ---------------------------------------------------------------------------

class TestDemoTradingShadow(unittest.TestCase):
    """Tests for _cmd_demo_trading_shadow (lines 1468-1646)."""

    def _base_args(self, out_dir: Path):
        return [
            "demo", "trading-shadow",
            "--out-dir", str(out_dir),
            "--input", str(HPL_EXAMPLE),
            "--market-fixture", str(TRADING_FIXTURE),
            "--policy", str(SHADOW_POLICY),
            "--shadow-model", str(SHADOW_MODEL),
        ]

    def test_trading_shadow_runs(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            self.assertIn("ok", data)
            self.assertIsNotNone(data.get("bundle_path"))

    def test_trading_shadow_bundle_exists(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            self.assertTrue(Path(data["bundle_path"]).exists())

    def test_trading_shadow_no_signing_key_errors(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            self.assertFalse(data["ok"])
            self.assertTrue(any("signing_key" in e for e in data["errors"]))

    def test_trading_shadow_hpl_error_on_missing_input(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run([
                "demo", "trading-shadow",
                "--out-dir", str(out_dir),
                "--input", str(Path(td) / "nonexistent.hpl"),
                "--market-fixture", str(TRADING_FIXTURE),
                "--policy", str(SHADOW_POLICY),
                "--shadow-model", str(SHADOW_MODEL),
            ])
            self.assertIn(rc, (0, 1))
            if rc == 0:
                data = _parse(stdout)
                self.assertFalse(data["ok"])

    def test_trading_shadow_constraint_inversion(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir) + ["--constraint-inversion-v1"])
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            self.assertFalse(data["ok"])
            bundle_path = Path(data["bundle_path"])
            manifest = json.loads((bundle_path / "bundle_manifest.json").read_text())
            roles = {e["role"] for e in manifest["artifacts"]}
            self.assertIn("constraint_witness", roles)
            self.assertIn("dual_proposal", roles)


# ---------------------------------------------------------------------------
# demo trading-io-shadow
# ---------------------------------------------------------------------------

class TestDemoTradingIoShadow(unittest.TestCase):
    """Tests for _cmd_demo_trading_io_shadow (lines 1649-1832)."""

    def _base_args(self, out_dir: Path):
        return [
            "demo", "trading-io-shadow",
            "--out-dir", str(out_dir),
            "--input", str(HPL_EXAMPLE),
            "--endpoint", "broker://demo",
            "--io-timeout-ms", "1000",
        ]

    def test_trading_io_shadow_runs(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            self.assertIn("ok", data)

    def test_trading_io_shadow_bundle_exists(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            bundle_path = data.get("bundle_path")
            self.assertIsNotNone(bundle_path)
            self.assertTrue(Path(bundle_path).exists())

    def test_trading_io_shadow_no_signing_key_errors(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            self.assertFalse(data["ok"])
            self.assertTrue(any("signing_key" in e for e in data["errors"]))

    def test_trading_io_shadow_hpl_error_on_missing_input(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run([
                "demo", "trading-io-shadow",
                "--out-dir", str(out_dir),
                "--input", str(Path(td) / "nonexistent.hpl"),
                "--endpoint", "broker://demo",
            ])
            self.assertIn(rc, (0, 1))
            if rc == 0:
                data = _parse(stdout)
                self.assertFalse(data["ok"])

    def test_trading_io_shadow_redaction_report_in_bundle(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            bundle_path = Path(data["bundle_path"])
            manifest = json.loads((bundle_path / "bundle_manifest.json").read_text())
            roles = {e["role"] for e in manifest["artifacts"]}
            self.assertIn("redaction_report", roles)


# ---------------------------------------------------------------------------
# demo trading-io-live-min
# ---------------------------------------------------------------------------

class TestDemoTradingIoLiveMin(unittest.TestCase):
    """Tests for _cmd_demo_trading_io_live_min (lines 1835-2024)."""

    def _base_args(self, out_dir: Path):
        return [
            "demo", "trading-io-live-min",
            "--out-dir", str(out_dir),
            "--input", str(HPL_EXAMPLE),
            "--endpoint", "broker://demo",
            "--io-timeout-ms", "1000",
            "--io-mode", "dry_run",
        ]

    def test_trading_io_live_min_runs(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            self.assertIn("ok", data)

    def test_trading_io_live_min_bundle_exists(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            self.assertIsNotNone(data.get("bundle_path"))
            self.assertTrue(Path(data["bundle_path"]).exists())

    def test_trading_io_live_min_no_signing_key_errors(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            self.assertFalse(data["ok"])
            self.assertTrue(any("signing_key" in e for e in data["errors"]))

    def test_trading_io_live_min_with_order_file(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            order_path = Path(td) / "order.json"
            order_path.write_text(json.dumps({
                "order_id": "test-order-1",
                "symbol": "TEST",
                "side": "buy",
                "qty": 10,
            }), encoding="utf-8")
            rc, stdout, _ = _run(self._base_args(out_dir) + ["--order", str(order_path)])
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            self.assertIn("ok", data)

    def test_trading_io_live_min_redaction_report_in_bundle(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            bundle_path = Path(data["bundle_path"])
            manifest = json.loads((bundle_path / "bundle_manifest.json").read_text())
            roles = {e["role"] for e in manifest["artifacts"]}
            self.assertIn("redaction_report", roles)

    def test_trading_io_live_min_hpl_error_on_missing_input(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run([
                "demo", "trading-io-live-min",
                "--out-dir", str(out_dir),
                "--input", str(Path(td) / "nonexistent.hpl"),
                "--endpoint", "broker://demo",
            ])
            self.assertIn(rc, (0, 1))
            if rc == 0:
                data = _parse(stdout)
                self.assertFalse(data["ok"])


# ---------------------------------------------------------------------------
# demo navier-stokes
# ---------------------------------------------------------------------------

class TestDemoNavierStokes(unittest.TestCase):
    """Tests for _cmd_demo_navier_stokes (lines 2027-2198)."""

    def _base_args(self, out_dir: Path):
        return [
            "demo", "navier-stokes",
            "--out-dir", str(out_dir),
            "--input", str(HPL_EXAMPLE),
            "--state", str(NS_STATE),
            "--policy", str(NS_POLICY),
        ]

    def test_navier_stokes_runs(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            self.assertIn("ok", data)

    def test_navier_stokes_bundle_exists(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            self.assertIsNotNone(data.get("bundle_path"))
            self.assertTrue(Path(data["bundle_path"]).exists())

    def test_navier_stokes_no_signing_key_errors(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            self.assertFalse(data["ok"])
            self.assertTrue(any("signing_key" in e for e in data["errors"]))

    def test_navier_stokes_constraint_inversion(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir) + ["--constraint-inversion-v1"])
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            self.assertFalse(data["ok"])
            bundle_path = Path(data["bundle_path"])
            manifest = json.loads((bundle_path / "bundle_manifest.json").read_text())
            roles = {e["role"] for e in manifest["artifacts"]}
            self.assertIn("constraint_witness", roles)
            self.assertIn("dual_proposal", roles)

    def test_navier_stokes_hpl_error_on_missing_input(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run([
                "demo", "navier-stokes",
                "--out-dir", str(out_dir),
                "--input", str(Path(td) / "nonexistent.hpl"),
                "--state", str(NS_STATE),
                "--policy", str(NS_POLICY),
            ])
            self.assertIn(rc, (0, 1))
            if rc == 0:
                data = _parse(stdout)
                self.assertFalse(data["ok"])


# ---------------------------------------------------------------------------
# demo net-shadow
# ---------------------------------------------------------------------------

class TestDemoNetShadow(unittest.TestCase):
    """Tests for _cmd_demo_net_shadow (lines 2201-2403)."""

    def _base_args(self, out_dir: Path):
        return [
            "demo", "net-shadow",
            "--out-dir", str(out_dir),
            "--input", str(HPL_EXAMPLE),
            "--endpoint", "net://demo",
            "--message", "hello",
            "--net-timeout-ms", "1000",
        ]

    def test_net_shadow_runs(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            self.assertIn("ok", data)

    def test_net_shadow_bundle_exists(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            self.assertIsNotNone(data.get("bundle_path"))
            self.assertTrue(Path(data["bundle_path"]).exists())

    def test_net_shadow_no_signing_key_errors(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            self.assertFalse(data["ok"])
            self.assertTrue(any("signing_key" in e for e in data["errors"]))

    def test_net_shadow_redaction_report_in_bundle(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir))
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            bundle_path = Path(data["bundle_path"])
            manifest = json.loads((bundle_path / "bundle_manifest.json").read_text())
            roles = {e["role"] for e in manifest["artifacts"]}
            self.assertIn("redaction_report", roles)

    def test_net_shadow_constraint_inversion(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run(self._base_args(out_dir) + ["--constraint-inversion-v1"])
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            self.assertFalse(data["ok"])
            bundle_path = Path(data["bundle_path"])
            manifest = json.loads((bundle_path / "bundle_manifest.json").read_text())
            roles = {e["role"] for e in manifest["artifacts"]}
            self.assertIn("constraint_witness", roles)
            self.assertIn("dual_proposal", roles)

    def test_net_shadow_hpl_error_on_missing_input(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run([
                "demo", "net-shadow",
                "--out-dir", str(out_dir),
                "--input", str(Path(td) / "nonexistent.hpl"),
                "--endpoint", "net://demo",
                "--message", "hi",
            ])
            self.assertIn(rc, (0, 1))
            if rc == 0:
                data = _parse(stdout)
                self.assertFalse(data["ok"])


# ---------------------------------------------------------------------------
# _cmd_demo dispatcher: unknown demo name
# ---------------------------------------------------------------------------

class TestDemoDispatcher(unittest.TestCase):
    """Test the _cmd_demo dispatcher (lines 935-953)."""

    def test_unknown_demo_name_handled(self):
        """The dispatcher prints an error JSON for unknown demo names.
        Since argparse validates choices at the top, we test the internal function directly."""
        from hpl.cli import _cmd_demo
        import argparse
        args = argparse.Namespace(demo_name="totally-unknown-demo")
        out = io.StringIO()
        with redirect_stdout(out):
            rc = _cmd_demo(args)
        self.assertEqual(rc, 0)
        data = json.loads(out.getvalue())
        self.assertFalse(data["ok"])
        self.assertIn("unknown demo", data["errors"])


# ---------------------------------------------------------------------------
# _load_tool_module helper (lines 2429-2434)
# ---------------------------------------------------------------------------

class TestLoadToolModule(unittest.TestCase):
    def test_load_tool_module_loads_a_real_module(self):
        from hpl.cli import _load_tool_module, ROOT
        # bundle_evidence is a real tool module in the tools/ dir
        bundle_ev = _load_tool_module(
            "bundle_evidence_test_load",
            ROOT / "tools" / "bundle_evidence.py",
        )
        self.assertTrue(hasattr(bundle_ev, "build_bundle"))

    def test_load_tool_module_makes_module_available_in_sys_modules(self):
        from hpl.cli import _load_tool_module, ROOT
        _load_tool_module(
            "bundle_evidence_sys_check",
            ROOT / "tools" / "bundle_evidence.py",
        )
        import sys
        self.assertIn("bundle_evidence_sys_check", sys.modules)


# ---------------------------------------------------------------------------
# Additional coverage of lines around 268-269, 284 (_cmd_demo dispatch in main)
# ---------------------------------------------------------------------------

class TestMainDemoDispatch(unittest.TestCase):
    """Exercise the main() → demo branch (lines 268-269)."""

    def test_main_dispatches_to_demo(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            rc, stdout, _ = _run([
                "demo", "trading-paper",
                "--out-dir", str(out_dir),
                "--input", str(HPL_EXAMPLE),
                "--market-fixture", str(TRADING_FIXTURE),
                "--policy", str(TRADING_POLICY),
            ])
            self.assertEqual(rc, 0)
            data = _parse(stdout)
            self.assertIn("ok", data)


# ---------------------------------------------------------------------------
# Broader coverage: verify work-dir teardown + re-creation on repeated calls
# ---------------------------------------------------------------------------

class TestDemoWorkDirRecreation(unittest.TestCase):
    def test_ci_governance_cleans_work_dir_on_repeat(self):
        with _tmp() as td:
            out_dir = Path(td) / "out"
            args = [
                "demo", "ci-governance",
                "--out-dir", str(out_dir),
                "--input", str(HPL_EXAMPLE),
                "--backend", "classical",
            ]
            rc1, stdout1, _ = _run(args)
            self.assertEqual(rc1, 0)
            # run again – should not error out
            rc2, stdout2, _ = _run(args)
            self.assertEqual(rc2, 0)
            data = _parse(stdout2)
            self.assertIn("ok", data)


if __name__ == "__main__":
    unittest.main()
