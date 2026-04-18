"""Targeted tests for small module gaps: papas, dev_change_event, coupling_event,
classical_lowering, execution_token, measurement_selection."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from hpl.observers.papas import (
    _normalize_reasons,
    build_papas_report,
    is_enabled,
)
from hpl.audit.dev_change_event import (
    build_dev_change_event,
    write_dev_change_event,
    DEFAULT_TIMESTAMP as DCE_DEFAULT_TIMESTAMP,
)
from hpl.audit.coupling_event import (
    build_coupling_event_from_registry,
    write_event_json,
    _find_projector,
    _coerce_str,
    _digest_payload,
)
from hpl.backends.classical_lowering import lower_program_ir_to_backend_ir, _build_ops
from hpl.execution_token import (
    ExecutionToken,
    _normalize_io_policy,
    _normalize_net_policy,
)
from hpl.runtime.effects.measurement_selection import (
    build_measurement_selection,
    TRACK_PUBLISH,
    TRACK_REGULATOR,
    TRACK_SHADOW,
)


# ---------------------------------------------------------------------------
# papas.py
# ---------------------------------------------------------------------------

class TestNormalizeReasons:
    def test_list_input(self):
        result = _normalize_reasons(["b", "a"])
        assert result == ["a", "b"]

    def test_none_input(self):
        result = _normalize_reasons(None)
        assert result == []

    def test_non_list_non_none(self):
        result = _normalize_reasons("single_reason")
        assert result == ["single_reason"]

    def test_non_list_int(self):
        result = _normalize_reasons(42)
        assert result == ["42"]


class TestBuildPapasReport:
    def test_no_dual_proposal(self):
        witness = {"witness_id": "w1", "stage": "test", "refusal_reasons": []}
        report = build_papas_report(witness)
        assert report["observer_id"] == "papas"
        assert "dual_proposal" not in report

    def test_with_dual_proposal(self):
        witness = {
            "witness_id": "w2",
            "stage": "test",
            "refusal_reasons": ["r1"],
            "constraints": {},
        }
        report = build_papas_report(witness, allow_dual_proposal=True)
        assert "dual_proposal" in report
        assert report["refusal_reasons"] == ["r1"]

    def test_non_list_reasons_in_report(self):
        witness = {"refusal_reasons": "oops"}
        report = build_papas_report(witness)
        assert report["refusal_reasons"] == ["oops"]


class TestIsEnabled:
    def test_none_always_enabled(self):
        assert is_enabled(None) is True

    def test_papas_in_list(self):
        assert is_enabled(["papas", "other"]) is True

    def test_papas_case_insensitive(self):
        assert is_enabled(["PAPAS"]) is True

    def test_not_in_list(self):
        assert is_enabled(["other"]) is False


# ---------------------------------------------------------------------------
# dev_change_event.py
# ---------------------------------------------------------------------------

class TestBuildDevChangeEvent:
    def test_normal(self):
        bundle = build_dev_change_event(
            mode="ci",
            branch="main",
            target_ledger_item="item1",
            files_changed=["a.py"],
            test_results="ok",
            tool_outputs="out",
            policy_version="v1",
        )
        assert bundle.event["mode"] == "ci"
        assert bundle.event["branch"] == "main"
        assert "change_id" in bundle.event
        assert "papas_witness_digest" in bundle.event

    def test_empty_timestamp_uses_default(self):
        bundle = build_dev_change_event(
            mode="ci",
            branch="main",
            target_ledger_item="item1",
            files_changed=[],
            test_results="",
            tool_outputs="",
            policy_version="v1",
            timestamp="",
        )
        assert bundle.event["timestamp"] == DCE_DEFAULT_TIMESTAMP

    def test_witness_record_present(self):
        bundle = build_dev_change_event(
            mode="shadow",
            branch="dev",
            target_ledger_item="item2",
            files_changed=["x.py", "y.py"],
            test_results="pass",
            tool_outputs="tools",
            policy_version="v2",
        )
        assert "observer_id" in bundle.witness_record


class TestWriteDevChangeEvent:
    def test_writes_json(self, tmp_path):
        event = {"key": "value", "num": 42}
        out = tmp_path / "event.json"
        write_dev_change_event(event, out)
        data = json.loads(out.read_text())
        assert data["key"] == "value"
        assert data["num"] == 42


# ---------------------------------------------------------------------------
# coupling_event.py
# ---------------------------------------------------------------------------

def _minimal_registry():
    return {
        "edges": [
            {
                "id": "e1",
                "projector": "p1",
                "operator_name": "op",
                "sector_src": "A",
                "sector_dst": "B",
                "invariants_checked": ["inv1"],
            }
        ],
        "projectors": [
            {"id": "p1", "version": "1.0"},
        ],
    }


class TestCouplingEventErrors:
    def test_edges_not_list_raises(self):
        reg = {"edges": "bad", "projectors": [{"id": "p1", "version": "1"}]}
        with pytest.raises(ValueError, match="edges list is required"):
            build_coupling_event_from_registry(reg)

    def test_edges_empty_raises(self):
        reg = {"edges": [], "projectors": [{"id": "p1", "version": "1"}]}
        with pytest.raises(ValueError, match="edges list is required"):
            build_coupling_event_from_registry(reg)

    def test_projectors_not_list_raises(self):
        reg = {"edges": [{"id": "e1", "projector": "p1"}], "projectors": "bad"}
        with pytest.raises(ValueError, match="projectors list is required"):
            build_coupling_event_from_registry(reg)

    def test_projectors_empty_raises(self):
        reg = {"edges": [{"id": "e1", "projector": "p1"}], "projectors": []}
        with pytest.raises(ValueError, match="projectors list is required"):
            build_coupling_event_from_registry(reg)

    def test_missing_projector_id_raises(self):
        # edge has no "projector" key
        reg = {
            "edges": [{"id": "e1"}],
            "projectors": [{"id": "p1", "version": "1"}],
        }
        with pytest.raises(ValueError, match="edge missing projector id"):
            build_coupling_event_from_registry(reg)

    def test_projector_not_found_raises(self):
        reg = {
            "edges": [{"id": "e1", "projector": "missing_proj"}],
            "projectors": [{"id": "p1", "version": "1"}],
        }
        with pytest.raises(ValueError, match="not found"):
            build_coupling_event_from_registry(reg)


class TestCouplingEventSuccess:
    def test_build_success(self):
        bundle = build_coupling_event_from_registry(_minimal_registry())
        assert "event_id" in bundle.event
        assert bundle.entanglement_metadata["sector_src"] == "A"

    def test_with_payloads(self):
        bundle = build_coupling_event_from_registry(
            _minimal_registry(),
            input_payload={"x": 1},
            output_payload={"y": 2},
        )
        assert bundle.event["input_digest"].startswith("sha256:")
        assert bundle.event["output_digest"].startswith("sha256:")

    def test_empty_timestamp_uses_default(self):
        bundle = build_coupling_event_from_registry(_minimal_registry(), timestamp="")
        assert bundle.event["timestamp"] == "1970-01-01T00:00:00Z"


class TestWriteEventJson:
    def test_writes_json(self, tmp_path):
        event = {"hello": "world"}
        out = tmp_path / "evt.json"
        write_event_json(event, out)
        assert json.loads(out.read_text()) == {"hello": "world"}


class TestFindProjector:
    def test_found(self):
        projectors = [{"id": "p1", "version": "v1"}, {"id": "p2", "version": "v2"}]
        result = _find_projector(projectors, "p2")
        assert result["version"] == "v2"

    def test_not_found_raises(self):
        with pytest.raises(ValueError, match="not found"):
            _find_projector([{"id": "p1"}], "px")

    def test_no_projector_id_raises(self):
        with pytest.raises(ValueError, match="edge missing projector id"):
            _find_projector([], None)

    def test_empty_projector_id_raises(self):
        with pytest.raises(ValueError, match="edge missing projector id"):
            _find_projector([], "")


class TestCoerceStr:
    def test_valid_string(self):
        assert _coerce_str("hello", "fb") == "hello"

    def test_none_uses_fallback(self):
        assert _coerce_str(None, "fallback") == "fallback"

    def test_empty_string_uses_fallback(self):
        assert _coerce_str("", "fallback") == "fallback"

    def test_non_string_uses_fallback(self):
        assert _coerce_str(42, "fallback") == "fallback"


class TestDigestPayload:
    def test_none_uses_fallback_seed(self):
        result = _digest_payload(None, "seed")
        assert result.startswith("sha256:")

    def test_non_none_digests_payload(self):
        result = _digest_payload({"x": 1}, "seed")
        assert result.startswith("sha256:")


# ---------------------------------------------------------------------------
# classical_lowering.py
# ---------------------------------------------------------------------------

class TestBuildOps:
    def test_normal_terms(self):
        ir = {"hamiltonian": {"terms": [{"operator_id": "H", "cls": "Pauli", "coefficient": 1.0}]}}
        ops = _build_ops(ir)
        assert len(ops) == 1
        assert ops[0]["operator_id"] == "H"

    def test_terms_not_list_returns_empty(self):
        ir = {"hamiltonian": {"terms": "not_a_list"}}
        ops = _build_ops(ir)
        assert ops == []

    def test_non_dict_term_skipped(self):
        ir = {"hamiltonian": {"terms": ["not_a_dict", {"operator_id": "X", "cls": "P", "coefficient": 2.0}]}}
        ops = _build_ops(ir)
        assert len(ops) == 1
        assert ops[0]["operator_id"] == "X"

    def test_empty_terms(self):
        ir = {"hamiltonian": {"terms": []}}
        ops = _build_ops(ir)
        assert ops == []

    def test_no_hamiltonian(self):
        ir = {}
        ops = _build_ops(ir)
        assert ops == []

    def test_lower_full(self):
        ir = {
            "program_id": "prog1",
            "hamiltonian": {"terms": [{"operator_id": "Z", "cls": "Pauli", "coefficient": 0.5}]},
        }
        backend_ir = lower_program_ir_to_backend_ir(ir)
        assert backend_ir.backend_target == "classical"
        assert len(backend_ir.ops) == 1


# ---------------------------------------------------------------------------
# execution_token.py
# ---------------------------------------------------------------------------

class TestNormalizeIoPolicy:
    def test_non_dict_returns_none(self):
        assert _normalize_io_policy(None) is None
        assert _normalize_io_policy("bad") is None
        assert _normalize_io_policy(42) is None

    def test_invalid_io_mode_normalized(self):
        policy = {"io_mode": "unknown_mode"}
        result = _normalize_io_policy(policy)
        assert result["io_mode"] == "dry_run"

    def test_valid_io_mode_live(self):
        policy = {"io_mode": "live"}
        result = _normalize_io_policy(policy)
        assert result["io_mode"] == "live"

    def test_io_budget_calls_included(self):
        policy = {"io_budget_calls": 5}
        result = _normalize_io_policy(policy)
        assert result["io_budget_calls"] == 5

    def test_io_budget_calls_excluded_when_absent(self):
        result = _normalize_io_policy({})
        assert "io_budget_calls" not in result


class TestNormalizeNetPolicy:
    def test_non_dict_returns_none(self):
        assert _normalize_net_policy(None) is None
        assert _normalize_net_policy("bad") is None

    def test_invalid_net_mode_normalized(self):
        policy = {"net_mode": "bogus"}
        result = _normalize_net_policy(policy)
        assert result["net_mode"] == "dry_run"

    def test_valid_net_mode_live(self):
        policy = {"net_mode": "live"}
        result = _normalize_net_policy(policy)
        assert result["net_mode"] == "live"

    def test_net_budget_calls_included(self):
        policy = {"net_budget_calls": 3}
        result = _normalize_net_policy(policy)
        assert result["net_budget_calls"] == 3


class TestExecutionTokenToDict:
    def test_notes_included_when_set(self):
        t = ExecutionToken.build(allowed_backends=["CLASSICAL"], notes="a note")
        d = t.to_dict()
        assert d["notes"] == "a note"

    def test_notes_excluded_when_none(self):
        t = ExecutionToken.build(allowed_backends=["CLASSICAL"])
        d = t.to_dict()
        assert "notes" not in d

    def test_delta_s_budget_included_when_nonzero(self):
        t = ExecutionToken.build(allowed_backends=["CLASSICAL"], delta_s_budget=5)
        d = t.to_dict()
        assert d["delta_s_budget"] == 5

    def test_measurement_modes_included(self):
        t = ExecutionToken.build(allowed_backends=["CLASSICAL"], measurement_modes_allowed=["MODE_A"])
        d = t.to_dict()
        assert "measurement_modes_allowed" in d


class TestExecutionTokenFromDict:
    def test_allowed_backends_not_list_defaults_empty(self):
        t = ExecutionToken.from_dict({
            "token_id": "t1",
            "allowed_backends": "not_a_list",
            "budget_steps": 100,
        })
        assert t.allowed_backends == []

    def test_measurement_modes_not_list_defaults_empty(self):
        t = ExecutionToken.from_dict({
            "token_id": "t1",
            "allowed_backends": ["CLASSICAL"],
            "measurement_modes_allowed": "bad",
        })
        assert t.measurement_modes_allowed is None

    def test_no_token_id_calls_build(self):
        t = ExecutionToken.from_dict({
            "allowed_backends": ["CLASSICAL"],
            "budget_steps": 50,
        })
        assert t.token_id.startswith("sha256:")
        assert t.budget_steps == 50

    def test_with_token_id_constructs_directly(self):
        t_orig = ExecutionToken.build(allowed_backends=["CLASSICAL"])
        d = t_orig.to_dict()
        t2 = ExecutionToken.from_dict(d)
        assert t2.token_id == t_orig.token_id

    def test_notes_preserved(self):
        t = ExecutionToken.from_dict({
            "token_id": "t1",
            "allowed_backends": ["CLASSICAL"],
            "notes": "test note",
        })
        assert t.notes == "test note"

    def test_delta_s_policy_not_dict_becomes_none(self):
        t = ExecutionToken.from_dict({
            "token_id": "t1",
            "allowed_backends": ["CLASSICAL"],
            "delta_s_policy": "bad",
        })
        assert t.delta_s_policy is None


# ---------------------------------------------------------------------------
# measurement_selection.py
# ---------------------------------------------------------------------------

class TestMeasurementSelection:
    def test_non_dict_input(self):
        result = build_measurement_selection("not_a_dict")
        assert not result.ok
        assert "boundary_conditions_invalid" in result.errors

    def test_no_selection_empty_dict(self):
        result = build_measurement_selection({})
        assert not result.ok
        assert "no_selection" in result.errors

    def test_ambiguous_selection(self):
        # Both ci_available (PUBLISH) and regulator_request_id (REGULATOR) set
        result = build_measurement_selection({
            "ci_available": True,
            "regulator_request_id": "req-123",
        })
        assert not result.ok
        assert any("ambiguous_selection" in e for e in result.errors)

    def test_track_publish_ci_available(self):
        result = build_measurement_selection({"ci_available": True})
        assert result.ok
        assert result.selection["selected_track"] == TRACK_PUBLISH

    def test_track_regulator_request_id(self):
        result = build_measurement_selection({"regulator_request_id": "req-abc"})
        assert result.ok
        assert result.selection["selected_track"] == TRACK_REGULATOR

    def test_track_regulator_request(self):
        result = build_measurement_selection({"regulator_request": "some-request"})
        assert result.ok
        assert result.selection["selected_track"] == TRACK_REGULATOR

    def test_track_shadow_market_window(self):
        result = build_measurement_selection({"market_window_open": True})
        assert result.ok
        assert result.selection["selected_track"] == TRACK_SHADOW

    def test_track_shadow_risk_mode_shadow(self):
        result = build_measurement_selection({"risk_mode": "shadow"})
        assert result.ok
        assert result.selection["selected_track"] == TRACK_SHADOW

    def test_track_shadow_risk_mode_live(self):
        result = build_measurement_selection({"risk_mode": "live"})
        assert result.ok
        assert result.selection["selected_track"] == TRACK_SHADOW

    def test_risk_mode_unknown_no_candidate(self):
        result = build_measurement_selection({"risk_mode": "unknown"})
        assert not result.ok
        assert "no_selection" in result.errors

    def test_selection_includes_requested_constraints(self):
        result = build_measurement_selection({
            "ci_available": True,
            "requested_constraints": {"max_latency_ms": 100},
        })
        assert result.ok
        assert result.selection["requested_constraints"]["max_latency_ms"] == 100

    def test_requested_constraints_non_dict_defaults(self):
        result = build_measurement_selection({
            "ci_available": True,
            "requested_constraints": "bad",
        })
        assert result.ok
        assert result.selection["requested_constraints"] == {}

    def test_selection_id_is_digest(self):
        result = build_measurement_selection({"ci_available": True})
        assert result.selection["selection_id"].startswith("sha256:")

    def test_boundary_conditions_digest_present(self):
        result = build_measurement_selection({"ci_available": True})
        assert result.selection["boundary_conditions_digest"].startswith("sha256:")
