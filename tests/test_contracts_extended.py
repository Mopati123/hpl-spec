"""Extended test coverage for src/hpl/runtime/contracts.py.

Targets the uncovered branches (lines 32, 36-42, 54, 59-73, 76, 78, 80-97):
  - backend check: token missing (line 32) and backend not permitted (line 34)
  - measurement-mode checks (lines 36-42)
  - io_scope/io_scopes/io_endpoint permission checks (lines 54, 59-73)
  - net_cap/net_caps/net_endpoint permission checks (lines 76, 78, 80-97)
  - postconditions always passes (line 100-101)
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from hpl.execution_token import ExecutionToken
from hpl.runtime.context import RuntimeContext
from hpl.runtime.contracts import ExecutionContract


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ctx(token: ExecutionToken | None = None) -> RuntimeContext:
    return RuntimeContext(execution_token=token)


def _token(
    allowed_backends=None,
    measurement_modes_allowed=None,
    io_policy=None,
    net_policy=None,
):
    return ExecutionToken.build(
        allowed_backends=allowed_backends or ["PYTHON", "CLASSICAL", "QASM"],
        measurement_modes_allowed=measurement_modes_allowed,
        io_policy=io_policy,
        net_policy=net_policy,
    )


def _step(**kwargs):
    return dict(kwargs)


# ============================================================================
# Basic / allowed_steps
# ============================================================================

class TestPreconditionsBasic(unittest.TestCase):

    def test_no_constraints_passes(self):
        contract = ExecutionContract()
        ok, errs = contract.preconditions(_step(step_id="any"), _ctx())
        self.assertTrue(ok)
        self.assertEqual(errs, [])

    def test_allowed_steps_match(self):
        contract = ExecutionContract(allowed_steps={"A", "B"})
        ok, errs = contract.preconditions(_step(step_id="A"), _ctx())
        self.assertTrue(ok)

    def test_allowed_steps_mismatch(self):
        contract = ExecutionContract(allowed_steps={"A"})
        ok, errs = contract.preconditions(_step(step_id="Z"), _ctx())
        self.assertFalse(ok)
        self.assertTrue(any("step not allowed" in e for e in errs))

    def test_step_id_via_operator_id(self):
        """step_id fallback to operator_id."""
        contract = ExecutionContract(allowed_steps={"OP1"})
        ok, errs = contract.preconditions(_step(operator_id="OP1"), _ctx())
        self.assertTrue(ok)

    def test_step_id_empty_when_both_missing(self):
        """No step_id and no operator_id → empty string step_id, no allowed_steps → passes."""
        contract = ExecutionContract()
        ok, errs = contract.preconditions(_step(), _ctx())
        self.assertTrue(ok)

    def test_postconditions_always_pass(self):
        contract = ExecutionContract()
        ok, errs = contract.postconditions(_step(step_id="x"), _ctx())
        self.assertTrue(ok)
        self.assertEqual(errs, [])


# ============================================================================
# Backend requirement
# ============================================================================

class TestPreconditionsBackend(unittest.TestCase):

    def test_backend_required_token_missing_line_32(self):
        """Line 32: token is None but a backend is required."""
        contract = ExecutionContract(required_backend="QASM")
        # ctx has no execution_token
        ok, errs = contract.preconditions(_step(step_id="s"), _ctx(token=None))
        self.assertFalse(ok)
        self.assertTrue(any("execution token missing" in e for e in errs))

    def test_backend_not_permitted_line_34(self):
        """Line 34: token present but backend not in allowed list."""
        tok = _token(allowed_backends=["CLASSICAL"])
        contract = ExecutionContract(required_backend="QASM")
        ok, errs = contract.preconditions(_step(step_id="s"), _ctx(token=tok))
        self.assertFalse(ok)
        self.assertTrue(any("backend not permitted" in e for e in errs))

    def test_backend_permitted_passes(self):
        tok = _token(allowed_backends=["QASM"])
        contract = ExecutionContract(required_backend="QASM")
        ok, errs = contract.preconditions(_step(step_id="s"), _ctx(token=tok))
        self.assertTrue(ok)

    def test_backend_from_step_requires_dict(self):
        """Backend extracted from step['requires']['backend']."""
        tok = _token(allowed_backends=["CLASSICAL"])
        contract = ExecutionContract()
        step = _step(step_id="s", requires={"backend": "QASM"})
        ok, errs = contract.preconditions(step, _ctx(token=tok))
        self.assertFalse(ok)
        self.assertTrue(any("backend not permitted" in e for e in errs))

    def test_backend_from_step_required_backend_field(self):
        """Backend from step['required_backend'] when requires is not dict."""
        tok = _token(allowed_backends=["CLASSICAL"])
        contract = ExecutionContract()
        step = _step(step_id="s", required_backend="QASM")
        ok, errs = contract.preconditions(step, _ctx(token=tok))
        self.assertFalse(ok)
        self.assertTrue(any("backend not permitted" in e for e in errs))

    def test_no_backend_requirement_no_token(self):
        """No backend requirement → no error even if token is None."""
        contract = ExecutionContract()
        ok, errs = contract.preconditions(_step(step_id="s"), _ctx(token=None))
        self.assertTrue(ok)


# ============================================================================
# Measurement modes (lines 36-42)
# ============================================================================

class TestPreconditionsMeasurementModes(unittest.TestCase):

    def test_measure_effect_type_allowed_lines_36_to_39(self):
        """Line 37-39: MEASURE_X in allowed modes → passes."""
        tok = _token(measurement_modes_allowed=["MEASURE_STANDARD"])
        contract = ExecutionContract()
        ok, errs = contract.preconditions(
            _step(step_id="s", effect_type="MEASURE_STANDARD"), _ctx(token=tok)
        )
        self.assertTrue(ok)
        self.assertEqual(errs, [])

    def test_measure_effect_type_not_allowed(self):
        """MEASURE_EXOTIC not in allowed modes → error."""
        tok = _token(measurement_modes_allowed=["MEASURE_STANDARD"])
        contract = ExecutionContract()
        ok, errs = contract.preconditions(
            _step(step_id="s", effect_type="MEASURE_EXOTIC"), _ctx(token=tok)
        )
        self.assertFalse(ok)
        self.assertTrue(any("measurement mode not permitted" in e for e in errs))

    def test_compute_delta_s_allowed_line_40_to_42(self):
        """Line 40-42: COMPUTE_DELTA_S in allowed modes → passes."""
        tok = _token(measurement_modes_allowed=["COMPUTE_DELTA_S"])
        contract = ExecutionContract()
        ok, errs = contract.preconditions(
            _step(step_id="s", effect_type="COMPUTE_DELTA_S"), _ctx(token=tok)
        )
        self.assertTrue(ok)

    def test_compute_delta_s_not_allowed(self):
        """COMPUTE_DELTA_S not in allowed modes → error."""
        tok = _token(measurement_modes_allowed=["MEASURE_STANDARD"])
        contract = ExecutionContract()
        ok, errs = contract.preconditions(
            _step(step_id="s", effect_type="COMPUTE_DELTA_S"), _ctx(token=tok)
        )
        self.assertFalse(ok)
        self.assertTrue(any("measurement mode not permitted" in e for e in errs))

    def test_delta_s_gate_not_allowed(self):
        """DELTA_S_GATE not in allowed modes → error."""
        tok = _token(measurement_modes_allowed=["MEASURE_STANDARD"])
        contract = ExecutionContract()
        ok, errs = contract.preconditions(
            _step(step_id="s", effect_type="DELTA_S_GATE"), _ctx(token=tok)
        )
        self.assertFalse(ok)
        self.assertTrue(any("measurement mode not permitted" in e for e in errs))

    def test_delta_s_gate_allowed(self):
        tok = _token(measurement_modes_allowed=["DELTA_S_GATE"])
        contract = ExecutionContract()
        ok, errs = contract.preconditions(
            _step(step_id="s", effect_type="DELTA_S_GATE"), _ctx(token=tok)
        )
        self.assertTrue(ok)

    def test_no_effect_type_no_measurement_check(self):
        """Empty effect_type → no measurement-mode errors even with restricted token."""
        tok = _token(measurement_modes_allowed=["MEASURE_STANDARD"])
        contract = ExecutionContract()
        ok, errs = contract.preconditions(_step(step_id="s"), _ctx(token=tok))
        self.assertTrue(ok)

    def test_no_measurement_modes_token_skips_check(self):
        """Token with no measurement_modes_allowed → measurement block skipped."""
        tok = _token(measurement_modes_allowed=None)
        contract = ExecutionContract()
        ok, errs = contract.preconditions(
            _step(step_id="s", effect_type="MEASURE_EXOTIC"), _ctx(token=tok)
        )
        self.assertTrue(ok)


# ============================================================================
# IO permission checks (lines 54, 59-73)
# ============================================================================

class TestPreconditionsIOPolicy(unittest.TestCase):

    def _io_token(self, io_allowed=True, io_scopes=None, io_endpoints=None):
        io_policy = {
            "io_allowed": io_allowed,
            "io_scopes": io_scopes or [],
            "io_endpoints_allowed": io_endpoints or [],
        }
        return _token(io_policy=io_policy)

    def test_io_scope_no_token_denied(self):
        """No token → IOPermissionDenied."""
        contract = ExecutionContract()
        step = _step(requires={"io_scope": "READ"})
        ok, errs = contract.preconditions(step, _ctx(token=None))
        self.assertFalse(ok)
        self.assertIn("IOPermissionDenied", errs)

    def test_io_scope_io_not_allowed(self):
        """io_allowed=False → IOPermissionDenied."""
        tok = self._io_token(io_allowed=False)
        contract = ExecutionContract()
        step = _step(requires={"io_scope": "READ"})
        ok, errs = contract.preconditions(step, _ctx(token=tok))
        self.assertFalse(ok)
        self.assertIn("IOPermissionDenied", errs)

    def test_io_scope_allowed_passes(self):
        """io_allowed=True, scope in list → passes."""
        tok = self._io_token(io_allowed=True, io_scopes=["READ"])
        contract = ExecutionContract()
        step = _step(requires={"io_scope": "READ"})
        ok, errs = contract.preconditions(step, _ctx(token=tok))
        self.assertTrue(ok)
        self.assertEqual(errs, [])

    def test_io_scope_not_in_allowed_scopes(self):
        """Scope requested but not in policy → IOPermissionDenied:scope."""
        tok = self._io_token(io_allowed=True, io_scopes=["READ"])
        contract = ExecutionContract()
        step = _step(requires={"io_scope": "WRITE"})
        ok, errs = contract.preconditions(step, _ctx(token=tok))
        self.assertFalse(ok)
        self.assertTrue(any("IOPermissionDenied:WRITE" in e for e in errs))

    def test_io_scopes_list_line_54(self):
        """Line 54: io_scopes is a list → each item added to required_scopes."""
        tok = self._io_token(io_allowed=True, io_scopes=["READ", "WRITE"])
        contract = ExecutionContract()
        step = _step(requires={"io_scopes": ["READ", "WRITE"]})
        ok, errs = contract.preconditions(step, _ctx(token=tok))
        self.assertTrue(ok)

    def test_io_scopes_list_one_denied(self):
        """List with one denied scope → error for that scope."""
        tok = self._io_token(io_allowed=True, io_scopes=["READ"])
        contract = ExecutionContract()
        step = _step(requires={"io_scopes": ["READ", "WRITE"]})
        ok, errs = contract.preconditions(step, _ctx(token=tok))
        self.assertFalse(ok)
        self.assertTrue(any("IOPermissionDenied:WRITE" in e for e in errs))

    def test_io_endpoint_allowed(self):
        """Endpoint in allowed list → passes."""
        tok = self._io_token(io_allowed=True, io_endpoints=["https://example.com"])
        contract = ExecutionContract()
        step = _step(requires={"io_endpoint": "https://example.com"})
        ok, errs = contract.preconditions(step, _ctx(token=tok))
        self.assertTrue(ok)

    def test_io_endpoint_not_allowed_line_73(self):
        """Line 73: endpoint not in allowed list → EndpointNotAllowed."""
        tok = self._io_token(io_allowed=True, io_endpoints=["https://allowed.com"])
        contract = ExecutionContract()
        step = _step(requires={"io_endpoint": "https://other.com"})
        ok, errs = contract.preconditions(step, _ctx(token=tok))
        self.assertFalse(ok)
        self.assertIn("EndpointNotAllowed", errs)

    def test_io_endpoint_empty_allowlist_no_restriction(self):
        """Empty endpoint allowlist → endpoint not checked (any allowed)."""
        tok = self._io_token(io_allowed=True, io_endpoints=[])
        contract = ExecutionContract()
        step = _step(requires={"io_endpoint": "https://anything.com"})
        ok, errs = contract.preconditions(step, _ctx(token=tok))
        self.assertTrue(ok)

    def test_io_scope_and_endpoint_combined(self):
        """Both scope and endpoint required and both allowed."""
        tok = self._io_token(io_allowed=True, io_scopes=["READ"], io_endpoints=["https://x.com"])
        contract = ExecutionContract()
        step = _step(requires={"io_scope": "READ", "io_endpoint": "https://x.com"})
        ok, errs = contract.preconditions(step, _ctx(token=tok))
        self.assertTrue(ok)

    def test_io_token_policy_none_denied(self):
        """Token exists but io_policy is None → IOPermissionDenied."""
        tok = ExecutionToken.build(allowed_backends=["CLASSICAL"])
        # io_policy will be None since none passed
        contract = ExecutionContract()
        step = _step(requires={"io_scope": "READ"})
        ok, errs = contract.preconditions(step, _ctx(token=tok))
        self.assertFalse(ok)
        self.assertIn("IOPermissionDenied", errs)


# ============================================================================
# Net permission checks (lines 76, 78, 80-97)
# ============================================================================

class TestPreconditionsNetPolicy(unittest.TestCase):

    def _net_token(self, net_caps=None, net_endpoints=None):
        net_policy = {
            "net_mode": "live",
            "net_caps": net_caps or [],
            "net_endpoints_allowlist": net_endpoints or [],
        }
        return _token(net_policy=net_policy)

    def test_net_cap_no_token_denied(self):
        """No token → NetPermissionDenied."""
        contract = ExecutionContract()
        step = _step(requires={"net_cap": "HTTP"})
        ok, errs = contract.preconditions(step, _ctx(token=None))
        self.assertFalse(ok)
        self.assertIn("NetPermissionDenied", errs)

    def test_net_cap_no_net_policy_denied(self):
        """Token exists but net_policy is None → NetPermissionDenied."""
        tok = ExecutionToken.build(allowed_backends=["CLASSICAL"])
        contract = ExecutionContract()
        step = _step(requires={"net_cap": "HTTP"})
        ok, errs = contract.preconditions(step, _ctx(token=tok))
        self.assertFalse(ok)
        self.assertIn("NetPermissionDenied", errs)

    def test_net_cap_allowed_passes(self):
        """net_cap in policy → passes."""
        tok = self._net_token(net_caps=["HTTP"])
        contract = ExecutionContract()
        step = _step(requires={"net_cap": "HTTP"})
        ok, errs = contract.preconditions(step, _ctx(token=tok))
        self.assertTrue(ok)

    def test_net_cap_not_permitted(self):
        """net_cap not in policy → NetPermissionDenied:cap."""
        tok = self._net_token(net_caps=["HTTP"])
        contract = ExecutionContract()
        step = _step(requires={"net_cap": "WEBSOCKET"})
        ok, errs = contract.preconditions(step, _ctx(token=tok))
        self.assertFalse(ok)
        self.assertTrue(any("NetPermissionDenied:WEBSOCKET" in e for e in errs))

    def test_net_caps_list_line_78(self):
        """Line 78: net_caps is a list → each added to required_net_caps."""
        tok = self._net_token(net_caps=["HTTP", "GRPC"])
        contract = ExecutionContract()
        step = _step(requires={"net_caps": ["HTTP", "GRPC"]})
        ok, errs = contract.preconditions(step, _ctx(token=tok))
        self.assertTrue(ok)

    def test_net_caps_list_one_denied(self):
        """One cap in list not permitted → error."""
        tok = self._net_token(net_caps=["HTTP"])
        contract = ExecutionContract()
        step = _step(requires={"net_caps": ["HTTP", "GRPC"]})
        ok, errs = contract.preconditions(step, _ctx(token=tok))
        self.assertFalse(ok)
        self.assertTrue(any("NetPermissionDenied:GRPC" in e for e in errs))

    def test_net_endpoint_allowed_line_96(self):
        """Endpoint in allowlist → passes."""
        tok = self._net_token(net_caps=[], net_endpoints=["api.example.com"])
        contract = ExecutionContract()
        step = _step(requires={"net_endpoint": "api.example.com"})
        ok, errs = contract.preconditions(step, _ctx(token=tok))
        self.assertTrue(ok)

    def test_net_endpoint_not_in_allowlist_line_97(self):
        """Endpoint not in allowlist → NetEndpointNotAllowed."""
        tok = self._net_token(net_caps=[], net_endpoints=["api.example.com"])
        contract = ExecutionContract()
        step = _step(requires={"net_endpoint": "api.other.com"})
        ok, errs = contract.preconditions(step, _ctx(token=tok))
        self.assertFalse(ok)
        self.assertIn("NetEndpointNotAllowed", errs)

    def test_net_endpoint_empty_allowlist_no_restriction(self):
        """Empty endpoint allowlist → no restriction on endpoints."""
        tok = self._net_token(net_caps=[], net_endpoints=[])
        contract = ExecutionContract()
        step = _step(requires={"net_endpoint": "anything.com"})
        ok, errs = contract.preconditions(step, _ctx(token=tok))
        self.assertTrue(ok)

    def test_net_cap_line_76_single_string(self):
        """Line 76: net_cap is a str → appended once."""
        tok = self._net_token(net_caps=["UDP"])
        contract = ExecutionContract()
        step = _step(requires={"net_cap": "UDP"})
        ok, errs = contract.preconditions(step, _ctx(token=tok))
        self.assertTrue(ok)

    def test_net_cap_and_endpoint_combined(self):
        """Both net_cap and net_endpoint required and allowed."""
        tok = self._net_token(net_caps=["HTTP"], net_endpoints=["srv.example.com"])
        contract = ExecutionContract()
        step = _step(requires={"net_cap": "HTTP", "net_endpoint": "srv.example.com"})
        ok, errs = contract.preconditions(step, _ctx(token=tok))
        self.assertTrue(ok)


# ============================================================================
# Contract dataclass defaults
# ============================================================================

class TestExecutionContractDefaults(unittest.TestCase):

    def test_default_allowed_steps_empty(self):
        contract = ExecutionContract()
        # Empty set → no step filtering
        ok, errs = contract.preconditions(_step(step_id="anything"), _ctx())
        self.assertTrue(ok)

    def test_require_epoch_verification_default_false(self):
        contract = ExecutionContract()
        self.assertFalse(contract.require_epoch_verification)

    def test_require_signature_verification_default_false(self):
        contract = ExecutionContract()
        self.assertFalse(contract.require_signature_verification)

    def test_required_backend_default_none(self):
        contract = ExecutionContract()
        self.assertIsNone(contract.required_backend)

    def test_postconditions_always_ok(self):
        contract = ExecutionContract(allowed_steps={"X"})
        ok, errs = contract.postconditions(_step(step_id="ANYTHING"), _ctx())
        self.assertTrue(ok)
        self.assertEqual(errs, [])


if __name__ == "__main__":
    unittest.main()
