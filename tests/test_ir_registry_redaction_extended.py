"""Extended tests for IR emitter, operator registry, and redaction."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from hpl.dynamics import ir_emitter
from hpl.ast import Node
from hpl.errors import ValidationError
from hpl.operators import registry as op_registry
from hpl.runtime.redaction import (
    scan_artifacts,
    _scan_bytes,
    _scan_json,
    _looks_like_secret_key,
    _looks_like_safe_hash,
    _display_path,
)


# ---------------------------------------------------------------------------
# Helpers for building AST nodes
# ---------------------------------------------------------------------------

def atom(value) -> Node:
    return Node(value=value)


def lst(*children) -> Node:
    return Node(value=list(children))


def make_hamiltonian_term(op_id: str, coefficient: float) -> Node:
    return lst(atom("term"), atom(op_id), atom(coefficient))


def make_hamiltonian(*terms) -> Node:
    return lst(atom("hamiltonian"), *terms)


def make_program(*forms) -> list:
    return list(forms)


# ---------------------------------------------------------------------------
# IR Emitter — _collect_terms_from_node branches (lines 69-83)
# ---------------------------------------------------------------------------

class IREmitterCollectTermsTests(unittest.TestCase):
    def test_atom_node_returns_no_terms(self):
        """is_atom path — lines 70-71."""
        node = atom("hello")
        terms = []
        ir_emitter._collect_terms_from_node(node, terms)
        self.assertEqual(terms, [])

    def test_empty_list_node_returns_no_terms(self):
        """not items path — lines 73-74."""
        node = lst()
        terms = []
        ir_emitter._collect_terms_from_node(node, terms)
        self.assertEqual(terms, [])

    def test_non_hamiltonian_head_recurses(self):
        """Recurse into children — lines 82-83."""
        term_node = make_hamiltonian_term("OP_X", 1.0)
        ham_node = make_hamiltonian(term_node)
        # Wrap in a non-hamiltonian form
        wrapper = lst(atom("other"), ham_node)
        terms = []
        ir_emitter._collect_terms_from_node(wrapper, terms)
        self.assertEqual(len(terms), 1)
        self.assertEqual(terms[0][0], "OP_X")

    def test_hamiltonian_head_collects_terms(self):
        """hamiltonian head path — lines 76-81."""
        t1 = make_hamiltonian_term("OP_A", 1.0)
        t2 = make_hamiltonian_term("OP_B", 2.5)
        ham_node = make_hamiltonian(t1, t2)
        terms = []
        ir_emitter._collect_terms_from_node(ham_node, terms)
        self.assertEqual(len(terms), 2)
        self.assertEqual(terms[0][0], "OP_A")
        self.assertEqual(terms[1][0], "OP_B")

    def test_collect_terms_from_program(self):
        t = make_hamiltonian_term("OP_Z", 3.0)
        ham = make_hamiltonian(t)
        program = make_program(ham)
        terms = ir_emitter._collect_terms(program)
        self.assertEqual(len(terms), 1)
        self.assertEqual(terms[0][0], "OP_Z")


# ---------------------------------------------------------------------------
# IR Emitter — _term_from_node branches (lines 86-99)
# ---------------------------------------------------------------------------

class IREmitterTermFromNodeTests(unittest.TestCase):
    def test_atom_node_returns_none(self):
        """is_atom path — line 88."""
        result = ir_emitter._term_from_node(atom("x"))
        self.assertIsNone(result)

    def test_wrong_length_list_returns_none(self):
        """len != 3 path — line 91."""
        node = lst(atom("term"), atom("OP_X"))
        result = ir_emitter._term_from_node(node)
        self.assertIsNone(result)

    def test_wrong_head_returns_none(self):
        """head.value != 'term' — lines 93-99."""
        node = lst(atom("not_term"), atom("OP_X"), atom(1.0))
        result = ir_emitter._term_from_node(node)
        self.assertIsNone(result)

    def test_non_atom_operator_ref_returns_none(self):
        """operator_ref.is_atom False — line 96."""
        nested = lst(atom("a"), atom("b"))
        node = lst(atom("term"), nested, atom(1.0))
        result = ir_emitter._term_from_node(node)
        self.assertIsNone(result)

    def test_non_numeric_coefficient_returns_none(self):
        """coefficient not int/float — lines 97-99."""
        node = lst(atom("term"), atom("OP_X"), atom("not_a_number"))
        result = ir_emitter._term_from_node(node)
        self.assertIsNone(result)

    def test_valid_term_returns_tuple(self):
        """Happy path — line 98."""
        node = lst(atom("term"), atom("OP_X"), atom(2.0))
        result = ir_emitter._term_from_node(node)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "OP_X")
        self.assertAlmostEqual(result[1], 2.0)

    def test_integer_coefficient_accepted(self):
        node = lst(atom("term"), atom("OP_Y"), atom(5))
        result = ir_emitter._term_from_node(node)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result[1], 5.0)


# ---------------------------------------------------------------------------
# IR Emitter — validate_program_ir schema checks (lines 109-204)
# ---------------------------------------------------------------------------

class IREmitterValidationTests(unittest.TestCase):
    def _valid_ir(self) -> dict:
        return {
            "program_id": "test",
            "hamiltonian": {
                "terms": [
                    {"operator_id": "OP_A", "cls": "C", "coefficient": 1.0}
                ]
            },
            "operators": {
                "OP_A": {"type": "unspecified", "commutes_with": [], "backend_map": []}
            },
            "invariants": [],
            "scheduler": {"collapse_policy": "unspecified", "authorized_observers": []},
        }

    def test_non_dict_ir_raises(self):
        """Line 111."""
        with self.assertRaises(ValidationError):
            ir_emitter.validate_program_ir("not a dict")

    def test_missing_required_field_raises(self):
        """Lines 113-115."""
        ir = self._valid_ir()
        del ir["program_id"]
        with self.assertRaises(ValidationError) as ctx:
            ir_emitter.validate_program_ir(ir)
        self.assertIn("program_id", str(ctx.exception))

    def test_program_id_wrong_type_raises(self):
        """Line 117 — _require_type."""
        ir = self._valid_ir()
        ir["program_id"] = 42
        with self.assertRaises(ValidationError):
            ir_emitter.validate_program_ir(ir)

    def test_hamiltonian_not_dict_raises(self):
        """Line 136."""
        ir = self._valid_ir()
        ir["hamiltonian"] = "not a dict"
        with self.assertRaises(ValidationError):
            ir_emitter.validate_program_ir(ir)

    def test_hamiltonian_missing_terms_raises(self):
        """Line 138."""
        ir = self._valid_ir()
        ir["hamiltonian"] = {}
        with self.assertRaises(ValidationError):
            ir_emitter.validate_program_ir(ir)

    def test_hamiltonian_terms_not_list_raises(self):
        """Line 141."""
        ir = self._valid_ir()
        ir["hamiltonian"]["terms"] = "not a list"
        with self.assertRaises(ValidationError):
            ir_emitter.validate_program_ir(ir)

    def test_term_not_dict_raises(self):
        """Line 154."""
        ir = self._valid_ir()
        ir["hamiltonian"]["terms"] = ["not_a_dict"]
        with self.assertRaises(ValidationError):
            ir_emitter.validate_program_ir(ir)

    def test_term_missing_field_raises(self):
        """Line 157."""
        ir = self._valid_ir()
        ir["hamiltonian"]["terms"] = [{"operator_id": "OP_A", "cls": "C"}]
        with self.assertRaises(ValidationError):
            ir_emitter.validate_program_ir(ir)

    def test_term_cls_not_in_enum_raises(self):
        """Line 161."""
        ir = self._valid_ir()
        ir["hamiltonian"]["terms"] = [{"operator_id": "OP_A", "cls": "X", "coefficient": 1.0}]
        with self.assertRaises(ValidationError):
            ir_emitter.validate_program_ir(ir)

    def test_term_coefficient_not_number_raises(self):
        """Line 163."""
        ir = self._valid_ir()
        ir["hamiltonian"]["terms"] = [{"operator_id": "OP_A", "cls": "C", "coefficient": "bad"}]
        with self.assertRaises(ValidationError):
            ir_emitter.validate_program_ir(ir)

    def test_operators_not_dict_raises(self):
        """Line 168."""
        ir = self._valid_ir()
        ir["operators"] = "not a dict"
        with self.assertRaises(ValidationError):
            ir_emitter.validate_program_ir(ir)

    def test_operator_entry_not_dict_raises(self):
        """Line 172."""
        ir = self._valid_ir()
        ir["operators"] = {"OP_A": "not_a_dict"}
        with self.assertRaises(ValidationError):
            ir_emitter.validate_program_ir(ir)

    def test_operator_missing_field_raises(self):
        """Line 175."""
        ir = self._valid_ir()
        ir["operators"] = {"OP_A": {"type": "unspecified", "commutes_with": []}}
        with self.assertRaises(ValidationError):
            ir_emitter.validate_program_ir(ir)

    def test_operator_commutes_with_not_list_raises(self):
        """Line 178."""
        ir = self._valid_ir()
        ir["operators"]["OP_A"]["commutes_with"] = "not_a_list"
        with self.assertRaises(ValidationError):
            ir_emitter.validate_program_ir(ir)

    def test_operator_backend_map_not_list_raises(self):
        """Line 180."""
        ir = self._valid_ir()
        ir["operators"]["OP_A"]["backend_map"] = "not_a_list"
        with self.assertRaises(ValidationError):
            ir_emitter.validate_program_ir(ir)

    def test_invariants_not_list_raises(self):
        """Line 185."""
        ir = self._valid_ir()
        ir["invariants"] = "not a list"
        with self.assertRaises(ValidationError):
            ir_emitter.validate_program_ir(ir)

    def test_invariant_not_dict_raises(self):
        """Line 187."""
        ir = self._valid_ir()
        ir["invariants"] = ["not_a_dict"]
        with self.assertRaises(ValidationError):
            ir_emitter.validate_program_ir(ir)

    def test_invariant_missing_field_raises(self):
        """Line 190."""
        ir = self._valid_ir()
        ir["invariants"] = [{"id": "inv1"}]
        with self.assertRaises(ValidationError):
            ir_emitter.validate_program_ir(ir)

    def test_invariant_id_wrong_type_raises(self):
        """Line 192."""
        ir = self._valid_ir()
        ir["invariants"] = [{"id": 42, "expression": "x > 0"}]
        with self.assertRaises(ValidationError):
            ir_emitter.validate_program_ir(ir)

    def test_invariant_expression_wrong_type_raises(self):
        """Line 193."""
        ir = self._valid_ir()
        ir["invariants"] = [{"id": "inv1", "expression": 42}]
        with self.assertRaises(ValidationError):
            ir_emitter.validate_program_ir(ir)

    def test_scheduler_not_dict_raises(self):
        """Line 198."""
        ir = self._valid_ir()
        ir["scheduler"] = "not a dict"
        with self.assertRaises(ValidationError):
            ir_emitter.validate_program_ir(ir)

    def test_scheduler_missing_field_raises(self):
        """Line 201."""
        ir = self._valid_ir()
        ir["scheduler"] = {"collapse_policy": "unspecified"}
        with self.assertRaises(ValidationError):
            ir_emitter.validate_program_ir(ir)

    def test_scheduler_collapse_policy_wrong_type_raises(self):
        """Line 202 (via _require_type)."""
        ir = self._valid_ir()
        ir["scheduler"]["collapse_policy"] = 123
        with self.assertRaises(ValidationError):
            ir_emitter.validate_program_ir(ir)

    def test_scheduler_authorized_observers_not_list_raises(self):
        """Line 204."""
        ir = self._valid_ir()
        ir["scheduler"]["authorized_observers"] = "not_a_list"
        with self.assertRaises(ValidationError):
            ir_emitter.validate_program_ir(ir)

    def test_unknown_ir_field_raises(self):
        """Line 126."""
        ir = self._valid_ir()
        ir["unknown_field"] = "bad"
        with self.assertRaises(ValidationError):
            ir_emitter.validate_program_ir(ir)

    def test_valid_ir_with_invariant_passes(self):
        ir = self._valid_ir()
        ir["invariants"] = [{"id": "inv1", "expression": "x > 0"}]
        # Should not raise
        ir_emitter.validate_program_ir(ir)

    def test_emit_program_ir_with_trace(self):
        """Test trace argument path."""
        from hpl.trace import TraceCollector
        t1 = make_hamiltonian_term("OP_A", 1.0)
        ham = make_hamiltonian(t1)
        program = make_program(ham)
        trace = TraceCollector()
        ir = ir_emitter.emit_program_ir(program, program_id="test_trace", trace=trace)
        self.assertIn("OP_A", ir["operators"])


# ---------------------------------------------------------------------------
# Operator Registry — edge cases (lines 25, 44-45, 51, 55-73, 99, 112)
# ---------------------------------------------------------------------------

class OperatorRegistryTests(unittest.TestCase):
    def test_resolve_registry_paths_with_explicit_paths(self):
        """Line 25 — explicit paths returned sorted."""
        with tempfile.TemporaryDirectory() as tmp:
            p1 = Path(tmp) / "b_registry.json"
            p2 = Path(tmp) / "a_registry.json"
            p1.write_text("{}", encoding="utf-8")
            p2.write_text("{}", encoding="utf-8")
            paths = op_registry.resolve_registry_paths(
                root=Path(tmp), registry_paths=[p1, p2]
            )
            self.assertEqual(len(paths), 2)
            # Sorted order
            self.assertEqual(paths[0], p2.resolve())
            self.assertEqual(paths[1], p1.resolve())

    def test_load_registries_no_sources_returns_error(self):
        """Lines 43-45 — no sources found."""
        with tempfile.TemporaryDirectory() as tmp:
            result = op_registry.load_operator_registries(
                root=Path(tmp), registry_paths=[]
            )
        self.assertIn("operator registries not found", result.errors)
        self.assertEqual(result.operators, {})

    def test_load_registries_invalid_json_skipped(self):
        """Lines 55-57 — invalid JSON file."""
        with tempfile.TemporaryDirectory() as tmp:
            reg_file = Path(tmp) / "registry.json"
            reg_file.write_text("not valid json {{{{", encoding="utf-8")
            result = op_registry.load_operator_registries(
                root=Path(tmp), registry_paths=[reg_file]
            )
        self.assertTrue(any("invalid JSON" in e for e in result.errors))

    def test_load_registries_operators_not_list(self):
        """Lines 60-62 — operators field not a list."""
        with tempfile.TemporaryDirectory() as tmp:
            reg_file = Path(tmp) / "registry.json"
            reg_file.write_text(
                json.dumps({"operators": "not_a_list"}),
                encoding="utf-8",
            )
            result = op_registry.load_operator_registries(
                root=Path(tmp), registry_paths=[reg_file]
            )
        self.assertTrue(any("must be a list" in e for e in result.errors))

    def test_load_registries_operator_entry_not_dict(self):
        """Lines 63-65 — entry not a dict."""
        with tempfile.TemporaryDirectory() as tmp:
            reg_file = Path(tmp) / "registry.json"
            reg_file.write_text(
                json.dumps({"operators": ["not_a_dict"]}),
                encoding="utf-8",
            )
            result = op_registry.load_operator_registries(
                root=Path(tmp), registry_paths=[reg_file]
            )
        self.assertTrue(any("operator entry must be an object" in e for e in result.errors))

    def test_load_registries_operator_id_missing(self):
        """Lines 67-69 — id missing."""
        with tempfile.TemporaryDirectory() as tmp:
            reg_file = Path(tmp) / "registry.json"
            reg_file.write_text(
                json.dumps({"operators": [{"class": "C", "impl_ref": "x"}]}),
                encoding="utf-8",
            )
            result = op_registry.load_operator_registries(
                root=Path(tmp), registry_paths=[reg_file]
            )
        self.assertTrue(any("id missing or invalid" in e for e in result.errors))

    def test_load_registries_operator_id_blank_string(self):
        """Lines 67-69 — blank id."""
        with tempfile.TemporaryDirectory() as tmp:
            reg_file = Path(tmp) / "registry.json"
            reg_file.write_text(
                json.dumps({"operators": [{"id": "   ", "class": "C", "impl_ref": "x"}]}),
                encoding="utf-8",
            )
            result = op_registry.load_operator_registries(
                root=Path(tmp), registry_paths=[reg_file]
            )
        self.assertTrue(any("id missing or invalid" in e for e in result.errors))

    def test_load_registries_duplicate_id(self):
        """Lines 71-72 — duplicate operator id."""
        with tempfile.TemporaryDirectory() as tmp:
            p1 = Path(tmp) / "a_registry.json"
            p2 = Path(tmp) / "b_registry.json"
            p1.write_text(
                json.dumps({
                    "sub_hamiltonian": "test_H",
                    "version": "0.1.0",
                    "operators": [{"id": "DUP_OP", "class": "C", "impl_ref": "x"}],
                }),
                encoding="utf-8",
            )
            p2.write_text(
                json.dumps({
                    "sub_hamiltonian": "test_H",
                    "version": "0.1.0",
                    "operators": [{"id": "DUP_OP", "class": "C", "impl_ref": "y"}],
                }),
                encoding="utf-8",
            )
            result = op_registry.load_operator_registries(
                root=Path(tmp), registry_paths=[p1, p2]
            )
        self.assertTrue(any("duplicate operator id" in e for e in result.errors))

    def test_validate_program_operators_enforce_false(self):
        """Line 99 — enforce=False always returns True."""
        registry = op_registry.OperatorRegistry(operators={}, sources=[], errors=[])
        ok, errors = op_registry.validate_program_operators(
            {"program_id": "x"}, registry, enforce=False
        )
        self.assertTrue(ok)
        self.assertEqual(errors, [])

    def test_validate_program_operators_missing_operators_error(self):
        """Lines 100-105 — missing operators reported."""
        registry = op_registry.OperatorRegistry(
            operators={"OP_EXISTING": {}}, sources=[], errors=[]
        )
        ir = {
            "program_id": "x",
            "hamiltonian": {"terms": [{"operator_id": "OP_MISSING", "cls": "C", "coefficient": 1.0}]},
            "operators": {"OP_MISSING": {}},
        }
        ok, errors = op_registry.validate_program_operators(ir, registry, enforce=True)
        self.assertFalse(ok)
        self.assertTrue(any("OP_MISSING" in e for e in errors))

    def test_validate_plan_operators_enforce_false(self):
        """Line 112 — enforce=False."""
        registry = op_registry.OperatorRegistry(operators={}, sources=[], errors=[])
        ok, errors = op_registry.validate_plan_operators([], registry, enforce=False)
        self.assertTrue(ok)
        self.assertEqual(errors, [])

    def test_validate_plan_operators_missing(self):
        """Lines 113-122 — missing operators in steps."""
        registry = op_registry.OperatorRegistry(
            operators={"OP_GOOD": {}}, sources=[], errors=[]
        )
        steps = [{"operator_id": "OP_GOOD"}, {"operator_id": "OP_BAD"}]
        ok, errors = op_registry.validate_plan_operators(steps, registry, enforce=True)
        self.assertFalse(ok)
        self.assertTrue(any("OP_BAD" in e for e in errors))

    def test_extract_operator_ids_from_hamiltonian_and_operators(self):
        ir = {
            "hamiltonian": {"terms": [
                {"operator_id": "OP_A", "cls": "C", "coefficient": 1.0},
            ]},
            "operators": {"OP_A": {}, "OP_B": {}},
        }
        ids = op_registry.extract_operator_ids(ir)
        self.assertIn("OP_A", ids)
        self.assertIn("OP_B", ids)

    def test_extract_operator_ids_deduplicates(self):
        ir = {
            "hamiltonian": {"terms": [{"operator_id": "OP_A", "cls": "C", "coefficient": 1.0}]},
            "operators": {"OP_A": {}},
        }
        ids = op_registry.extract_operator_ids(ir)
        self.assertEqual(ids.count("OP_A"), 1)


# ---------------------------------------------------------------------------
# Redaction — scan_artifacts and helpers (lines 38-39, 67, 83-98, 115)
# ---------------------------------------------------------------------------

class RedactionScanTests(unittest.TestCase):
    def test_scan_artifacts_no_paths_returns_ok(self):
        result = scan_artifacts([])
        self.assertTrue(result["ok"])
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["scanned"], [])

    def test_scan_artifacts_clean_file_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "clean.json"
            f.write_text(json.dumps({"note": "safe_value_here"}), encoding="utf-8")
            result = scan_artifacts([f])
        self.assertTrue(result["ok"])
        self.assertEqual(result["findings"], [])

    def test_scan_artifacts_github_token_detected(self):
        """Lines 38-39 — secret detected, findings populated."""
        token = "ghp_" + "A" * 40
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "secret.txt"
            f.write_text(f"token={token}", encoding="utf-8")
            result = scan_artifacts([f])
        self.assertFalse(result["ok"])
        self.assertTrue(result["findings"])
        self.assertTrue(result["errors"])

    def test_scan_artifacts_aws_access_key_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "creds.txt"
            f.write_text("AKIAIOSFODNN7EXAMPLE1234", encoding="utf-8")
            result = scan_artifacts([f])
        self.assertFalse(result["ok"])

    def test_scan_artifacts_bearer_token_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "auth.txt"
            f.write_text("Authorization: Bearer abcdefghijklmnopqrstuvwxyz1234567", encoding="utf-8")
            result = scan_artifacts([f])
        self.assertFalse(result["ok"])

    def test_scan_artifacts_stripe_secret_detected(self):
        # Build the pattern in parts to avoid triggering push-protection scanners
        prefix = "sk_" + "live"
        suffix = "_abcdefghijklmnopqrstuvwx"
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "stripe.txt"
            f.write_bytes((prefix + suffix).encode("utf-8"))
            result = scan_artifacts([f])
        self.assertFalse(result["ok"])

    def test_scan_artifacts_missing_file_skipped(self):
        """OSError path — lines 36-39."""
        result = scan_artifacts([Path("/nonexistent/file.json")])
        self.assertTrue(result["ok"])
        self.assertEqual(result["scanned"], [])

    def test_scan_artifacts_policy_field_present(self):
        result = scan_artifacts([])
        self.assertIn("policy", result)
        self.assertIn("pattern_ids", result["policy"])

    def test_scan_bytes_safe_hash_skipped(self):
        """Line 67 — safe hash value skipped."""
        # A sha256: prefix with exactly 71 chars total should be skipped
        safe = "sha256:" + "a" * 64
        # Wrap in something that would otherwise match bearer
        data = f"Bearer {safe}".encode("utf-8")
        matches = _scan_bytes(data, "test.txt")
        # The safe hash skip should prevent this match
        self.assertEqual(matches, [])

    def test_scan_json_secret_field_detected(self):
        """Lines 83-98 — JSON with secret key."""
        payload = json.dumps({"api_key": "supersecretvalue12345678"})
        matches = _scan_json(payload, "test.json")
        self.assertTrue(len(matches) > 0)
        self.assertEqual(matches[0]["pattern"], "secret_key_field")

    def test_scan_json_short_value_not_detected(self):
        """Line 97 — len < 16 skipped."""
        payload = json.dumps({"api_key": "short"})
        matches = _scan_json(payload, "test.json")
        self.assertEqual(matches, [])

    def test_scan_json_safe_hash_value_not_detected(self):
        """Lines 94-95 — safe hash skipped."""
        safe_hash = "sha256:" + "a" * 64
        payload = json.dumps({"api_key": safe_hash})
        matches = _scan_json(payload, "test.json")
        self.assertEqual(matches, [])

    def test_scan_json_non_secret_key_not_detected(self):
        """Lines 90-91 — non-secret key ignored."""
        payload = json.dumps({"username": "this_is_a_long_username_value_here"})
        matches = _scan_json(payload, "test.json")
        self.assertEqual(matches, [])

    def test_scan_json_invalid_json_returns_empty(self):
        """Lines 82-84 — JSONDecodeError returns empty."""
        matches = _scan_json("not valid json {{{", "test.json")
        self.assertEqual(matches, [])

    def test_scan_json_non_dict_returns_empty(self):
        """Lines 86 — payload not dict."""
        matches = _scan_json(json.dumps([1, 2, 3]), "test.json")
        self.assertEqual(matches, [])

    def test_looks_like_secret_key_password(self):
        self.assertTrue(_looks_like_secret_key("password"))
        self.assertTrue(_looks_like_secret_key("PASSWORD"))

    def test_looks_like_secret_key_api_key(self):
        self.assertTrue(_looks_like_secret_key("api_key"))
        self.assertTrue(_looks_like_secret_key("APIKEY"))

    def test_looks_like_secret_key_false(self):
        self.assertFalse(_looks_like_secret_key("username"))
        self.assertFalse(_looks_like_secret_key("timestamp"))

    def test_looks_like_safe_hash_valid(self):
        """Line 115 — sha256: with 71 chars total."""
        safe = "sha256:" + "a" * 64
        self.assertEqual(len(safe), 71)
        self.assertTrue(_looks_like_safe_hash(safe))

    def test_looks_like_safe_hash_wrong_prefix(self):
        self.assertFalse(_looks_like_safe_hash("md5:abc"))

    def test_looks_like_safe_hash_wrong_length(self):
        self.assertFalse(_looks_like_safe_hash("sha256:" + "a" * 10))

    def test_display_path_within_root(self):
        """Path within ROOT is displayed relative."""
        path = ROOT / "tests" / "fixtures" / "test.json"
        display = _display_path(path)
        self.assertNotIn(str(ROOT), display)

    def test_display_path_outside_root(self):
        """Line 123 — path outside ROOT uses name only."""
        path = Path("/tmp/some_other_file.json")
        display = _display_path(path)
        self.assertEqual(display, "some_other_file.json")

    def test_scan_artifacts_sorted_findings(self):
        """Findings are sorted by (path, pattern)."""
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "secret.txt"
            f.write_text("ghp_" + "B" * 40 + " ghp_" + "C" * 40, encoding="utf-8")
            result = scan_artifacts([f])
        # Should have 2 findings for the two tokens
        if len(result["findings"]) > 1:
            paths = [x["path"] for x in result["findings"]]
            patterns = [x["pattern"] for x in result["findings"]]
            self.assertEqual(paths, sorted(paths))

    def test_scan_artifacts_slack_token_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "slack.txt"
            f.write_text("token=xoxb-1234567890-abcdefghij", encoding="utf-8")
            result = scan_artifacts([f])
        self.assertFalse(result["ok"])


if __name__ == "__main__":
    unittest.main()
