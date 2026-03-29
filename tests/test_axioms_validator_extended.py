"""Extended test coverage for src/hpl/axioms/validator.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from hpl.ast import Node, SourceLocation
from hpl.errors import ValidationError
from hpl.axioms.validator import (
    validate_program,
    _reject_surface_symbols,
    _validate_form,
    _validate_operator,
    _validate_operator_body,
    _validate_arg_list,
    _validate_invariant,
    _validate_scheduler,
    _validate_observer,
    _validate_expression,
    _validate_hamiltonian,
    _validate_term,
    _validate_evolve,
    _validate_measure,
    _validate_handler,
    LAMBDA_SYMBOL,
    SURFACE_SYMBOLS,
)
from hpl.trace import TraceCollector


# ---------------------------------------------------------------------------
# Helpers to build Nodes concisely
# ---------------------------------------------------------------------------

def sym(name: str) -> Node:
    """Atom node holding a string symbol."""
    return Node(value=name)


def num(n) -> Node:
    """Atom node holding a numeric value."""
    return Node(value=n)


def lst(*children: Node) -> Node:
    """List node."""
    return Node(value=list(children))


def loc_sym(name: str, line: int = 1, col: int = 0) -> Node:
    return Node(value=name, location=SourceLocation(line=line, column=col))


# ---------------------------------------------------------------------------
# Minimal valid nodes for each top-level form
# ---------------------------------------------------------------------------

def make_operator(name: str = "my_op") -> Node:
    """(operator <name> (? (<args>) <expr>))"""
    return lst(sym("operator"), sym(name), lst(sym(LAMBDA_SYMBOL), lst(), sym("x")))


def make_invariant(name: str = "my_inv") -> Node:
    """(invariant <name> <expr>)"""
    return lst(sym("invariant"), sym(name), sym("x"))


def make_scheduler(name: str = "my_sched") -> Node:
    return lst(sym("scheduler"), sym(name), sym("x"))


def make_observer(name: str = "my_obs") -> Node:
    return lst(sym("observer"), sym(name), sym("x"))


def make_hamiltonian() -> Node:
    """(hamiltonian (term op_ref 1.0))"""
    return lst(sym("hamiltonian"), lst(sym("term"), sym("H"), num(1.0)))


# ============================================================================
# validate_program
# ============================================================================

class TestValidateProgram(unittest.TestCase):

    def test_empty_program_is_valid(self):
        # An empty list of forms should pass without error.
        validate_program([])

    def test_single_valid_operator_form(self):
        validate_program([make_operator()])

    def test_multiple_valid_forms(self):
        validate_program([make_operator(), make_invariant(), make_scheduler(), make_observer()])

    def test_surface_symbol_at_top_level_rejected(self):
        for sym_name in SURFACE_SYMBOLS:
            with self.subTest(sym_name=sym_name):
                with self.assertRaises(ValidationError):
                    validate_program([lst(sym(sym_name), sym("x"))])

    def test_validate_program_with_trace_collector(self):
        """Covers the trace branch inside validate_program."""
        trace = TraceCollector(program_id="test-prog")
        validate_program([make_operator()], trace=trace)
        # Trace should have recorded the axiomatic phase
        phases = {n.phase for n in trace.nodes}
        self.assertIn("axiomatic", phases)

    def test_validate_program_trace_none(self):
        """Ensure trace=None is handled gracefully."""
        validate_program([make_operator()], trace=None)

    def test_atom_form_raises(self):
        with self.assertRaises(ValidationError) as cm:
            validate_program([sym("bare_atom")])
        self.assertIn("Form must be a list", str(cm.exception))

    def test_empty_list_form_raises(self):
        with self.assertRaises(ValidationError) as cm:
            validate_program([lst()])
        self.assertIn("Form cannot be empty", str(cm.exception))

    def test_form_head_not_symbol_raises(self):
        # Head is a number
        with self.assertRaises(ValidationError) as cm:
            validate_program([lst(num(42), sym("x"))])
        self.assertIn("Form head must be a symbol", str(cm.exception))

    def test_generic_expression_form(self):
        """A form whose head is an unknown symbol falls through to _validate_expression."""
        validate_program([lst(sym("apply"), sym("f"), sym("x"))])


# ============================================================================
# _reject_surface_symbols
# ============================================================================

class TestRejectSurfaceSymbols(unittest.TestCase):

    def test_no_surface_symbol_passes(self):
        _reject_surface_symbols(sym("safe"), [0])

    def test_number_atom_passes(self):
        _reject_surface_symbols(num(3.14), [0])

    def test_surface_symbol_in_nested_list(self):
        node = lst(sym("outer"), lst(sym("defstrategy"), sym("inner")))
        with self.assertRaises(ValidationError):
            _reject_surface_symbols(node, [0])

    def test_all_surface_symbols_rejected(self):
        for sym_name in SURFACE_SYMBOLS:
            with self.subTest(sym_name=sym_name):
                with self.assertRaises(ValidationError):
                    _reject_surface_symbols(sym(sym_name), [0])

    def test_deeply_nested_surface_symbol(self):
        node = lst(sym("a"), lst(sym("b"), lst(sym("params"), sym("c"))))
        with self.assertRaises(ValidationError):
            _reject_surface_symbols(node, [0])


# ============================================================================
# _validate_operator
# ============================================================================

class TestValidateOperator(unittest.TestCase):

    def test_valid_operator(self):
        _validate_operator(make_operator(), [0])

    def test_operator_wrong_element_count(self):
        # (operator name) -- only 2 elements
        node = lst(sym("operator"), sym("op"))
        with self.assertRaises(ValidationError) as cm:
            _validate_operator(node, [0])
        self.assertIn("3 elements", str(cm.exception))

    def test_operator_wrong_element_count_too_many(self):
        node = lst(sym("operator"), sym("op"), sym("x"), sym("extra"))
        with self.assertRaises(ValidationError):
            _validate_operator(node, [0])

    def test_operator_name_not_symbol(self):
        node = lst(sym("operator"), num(99), lst(sym(LAMBDA_SYMBOL), lst(), sym("x")))
        with self.assertRaises(ValidationError) as cm:
            _validate_operator(node, [0])
        self.assertIn("operator name must be a symbol", str(cm.exception))

    def test_operator_body_atom_rejected(self):
        node = lst(sym("operator"), sym("op"), sym("not-a-list"))
        with self.assertRaises(ValidationError) as cm:
            _validate_operator(node, [0])
        self.assertIn("operator body must be a list", str(cm.exception))

    def test_operator_body_wrong_element_count(self):
        node = lst(sym("operator"), sym("op"), lst(sym(LAMBDA_SYMBOL), lst()))
        with self.assertRaises(ValidationError) as cm:
            _validate_operator(node, [0])
        self.assertIn("operator body must have 3 elements", str(cm.exception))

    def test_operator_body_wrong_lambda_symbol(self):
        node = lst(sym("operator"), sym("op"), lst(sym("not-lambda"), lst(), sym("x")))
        with self.assertRaises(ValidationError) as cm:
            _validate_operator(node, [0])
        self.assertIn("lambda symbol", str(cm.exception))

    def test_operator_body_lambda_not_symbol(self):
        # First element of body is a list, not the lambda symbol
        node = lst(sym("operator"), sym("op"), lst(lst(sym("nested")), lst(), sym("x")))
        with self.assertRaises(ValidationError) as cm:
            _validate_operator(node, [0])
        self.assertIn("lambda symbol", str(cm.exception))

    def test_operator_arg_list_atom_rejected(self):
        # arg list is an atom instead of a list
        node = lst(sym("operator"), sym("op"), lst(sym(LAMBDA_SYMBOL), sym("arg"), sym("x")))
        with self.assertRaises(ValidationError) as cm:
            _validate_operator(node, [0])
        self.assertIn("argument list must be a list", str(cm.exception))

    def test_operator_arg_not_symbol(self):
        # arg is a number
        node = lst(sym("operator"), sym("op"), lst(sym(LAMBDA_SYMBOL), lst(num(5)), sym("x")))
        with self.assertRaises(ValidationError) as cm:
            _validate_operator(node, [0])
        self.assertIn("argument must be a symbol", str(cm.exception))

    def test_operator_with_multiple_args(self):
        node = lst(sym("operator"), sym("op"), lst(sym(LAMBDA_SYMBOL), lst(sym("a"), sym("b")), sym("x")))
        _validate_operator(node, [0])


# ============================================================================
# _validate_invariant
# ============================================================================

class TestValidateInvariant(unittest.TestCase):

    def test_valid_invariant(self):
        _validate_invariant(make_invariant(), [0])

    def test_invariant_wrong_element_count(self):
        node = lst(sym("invariant"), sym("inv"))
        with self.assertRaises(ValidationError) as cm:
            _validate_invariant(node, [0])
        self.assertIn("3 elements", str(cm.exception))

    def test_invariant_name_not_symbol(self):
        node = lst(sym("invariant"), num(1), sym("x"))
        with self.assertRaises(ValidationError) as cm:
            _validate_invariant(node, [0])
        self.assertIn("invariant name must be a symbol", str(cm.exception))

    def test_invariant_body_is_expression_list(self):
        node = lst(sym("invariant"), sym("inv"), lst(sym("add"), sym("a"), sym("b")))
        _validate_invariant(node, [0])


# ============================================================================
# _validate_scheduler
# ============================================================================

class TestValidateScheduler(unittest.TestCase):

    def test_valid_scheduler(self):
        _validate_scheduler(make_scheduler(), [0])

    def test_scheduler_wrong_element_count(self):
        node = lst(sym("scheduler"), sym("s"))
        with self.assertRaises(ValidationError) as cm:
            _validate_scheduler(node, [0])
        self.assertIn("3 elements", str(cm.exception))

    def test_scheduler_name_not_symbol(self):
        node = lst(sym("scheduler"), lst(sym("x")), sym("y"))
        with self.assertRaises(ValidationError) as cm:
            _validate_scheduler(node, [0])
        self.assertIn("scheduler name must be a symbol", str(cm.exception))

    def test_scheduler_too_many_elements(self):
        node = lst(sym("scheduler"), sym("s"), sym("x"), sym("extra"))
        with self.assertRaises(ValidationError):
            _validate_scheduler(node, [0])


# ============================================================================
# _validate_observer
# ============================================================================

class TestValidateObserver(unittest.TestCase):

    def test_valid_observer(self):
        _validate_observer(make_observer(), [0])

    def test_observer_wrong_element_count(self):
        node = lst(sym("observer"), sym("o"))
        with self.assertRaises(ValidationError) as cm:
            _validate_observer(node, [0])
        self.assertIn("3 elements", str(cm.exception))

    def test_observer_name_not_symbol(self):
        node = lst(sym("observer"), num(0), sym("x"))
        with self.assertRaises(ValidationError) as cm:
            _validate_observer(node, [0])
        self.assertIn("observer name must be a symbol", str(cm.exception))

    def test_observer_too_many_elements(self):
        node = lst(sym("observer"), sym("o"), sym("x"), sym("y"))
        with self.assertRaises(ValidationError):
            _validate_observer(node, [0])


# ============================================================================
# _validate_expression
# ============================================================================

class TestValidateExpression(unittest.TestCase):

    def test_atom_is_valid_expression(self):
        _validate_expression(sym("x"), [0])
        _validate_expression(num(3), [0])

    def test_empty_list_expression_raises(self):
        with self.assertRaises(ValidationError) as cm:
            _validate_expression(lst(), [0])
        self.assertIn("expression cannot be empty list", str(cm.exception))

    def test_head_not_symbol_raises(self):
        with self.assertRaises(ValidationError) as cm:
            _validate_expression(lst(num(1), sym("x")), [0])
        self.assertIn("expression head must be a symbol", str(cm.exception))

    def test_hamiltonian_expression(self):
        """Covers the hamiltonian branch in _validate_expression."""
        _validate_expression(make_hamiltonian(), [0])

    def test_evolve_expression(self):
        """Covers the evolve branch in _validate_expression."""
        node = lst(sym("evolve"), sym("state"), sym("hamiltonian"))
        _validate_expression(node, [0])

    def test_measure_expression(self):
        """Covers the measure branch in _validate_expression."""
        handler = lst(sym(LAMBDA_SYMBOL), lst(sym("result")), sym("result"))
        node = lst(sym("measure"), sym("state"), sym("obs"), handler)
        _validate_expression(node, [0])

    def test_generic_expression_recurses_into_children(self):
        """Unknown head: children are recursively validated as expressions."""
        # All children are valid atoms
        node = lst(sym("apply"), sym("f"), sym("x"), num(1))
        _validate_expression(node, [0])

    def test_generic_expression_invalid_child_raises(self):
        """Invalid nested expression causes an error."""
        node = lst(sym("apply"), lst())  # empty list child
        with self.assertRaises(ValidationError):
            _validate_expression(node, [0])


# ============================================================================
# _validate_hamiltonian
# ============================================================================

class TestValidateHamiltonian(unittest.TestCase):

    def test_valid_hamiltonian_single_term(self):
        _validate_hamiltonian(make_hamiltonian(), [0])

    def test_valid_hamiltonian_multiple_terms(self):
        node = lst(
            sym("hamiltonian"),
            lst(sym("term"), sym("A"), num(1.0)),
            lst(sym("term"), sym("B"), num(2)),
        )
        _validate_hamiltonian(node, [0])

    def test_hamiltonian_no_terms_raises(self):
        node = lst(sym("hamiltonian"))
        with self.assertRaises(ValidationError) as cm:
            _validate_hamiltonian(node, [0])
        self.assertIn("at least one term", str(cm.exception))

    def test_term_not_list_raises(self):
        node = lst(sym("hamiltonian"), sym("not-a-list"))
        with self.assertRaises(ValidationError) as cm:
            _validate_hamiltonian(node, [0])
        self.assertIn("term must be a list", str(cm.exception))

    def test_term_wrong_element_count(self):
        node = lst(sym("hamiltonian"), lst(sym("term"), sym("A")))
        with self.assertRaises(ValidationError) as cm:
            _validate_hamiltonian(node, [0])
        self.assertIn("term must have 3 elements", str(cm.exception))

    def test_term_wrong_head_symbol(self):
        node = lst(sym("hamiltonian"), lst(sym("wrong"), sym("A"), num(1.0)))
        with self.assertRaises(ValidationError) as cm:
            _validate_hamiltonian(node, [0])
        self.assertIn("term must start with 'term'", str(cm.exception))

    def test_term_head_not_symbol(self):
        node = lst(sym("hamiltonian"), lst(num(1), sym("A"), num(1.0)))
        with self.assertRaises(ValidationError) as cm:
            _validate_hamiltonian(node, [0])
        self.assertIn("term must start with 'term'", str(cm.exception))

    def test_term_operator_ref_not_symbol(self):
        node = lst(sym("hamiltonian"), lst(sym("term"), num(42), num(1.0)))
        with self.assertRaises(ValidationError) as cm:
            _validate_hamiltonian(node, [0])
        self.assertIn("operator-ref must be a symbol", str(cm.exception))

    def test_term_coefficient_not_number(self):
        node = lst(sym("hamiltonian"), lst(sym("term"), sym("A"), sym("not-a-number")))
        with self.assertRaises(ValidationError) as cm:
            _validate_hamiltonian(node, [0])
        self.assertIn("coefficient must be a number", str(cm.exception))

    def test_term_coefficient_is_list_raises(self):
        node = lst(sym("hamiltonian"), lst(sym("term"), sym("A"), lst(sym("x"))))
        with self.assertRaises(ValidationError) as cm:
            _validate_hamiltonian(node, [0])
        self.assertIn("coefficient must be a number", str(cm.exception))

    def test_term_coefficient_integer_ok(self):
        node = lst(sym("hamiltonian"), lst(sym("term"), sym("A"), num(2)))
        _validate_hamiltonian(node, [0])


# ============================================================================
# _validate_evolve
# ============================================================================

class TestValidateEvolve(unittest.TestCase):

    def test_valid_evolve(self):
        node = lst(sym("evolve"), sym("state"), sym("h"))
        _validate_evolve(node, [0])

    def test_evolve_wrong_element_count_too_few(self):
        node = lst(sym("evolve"), sym("state"))
        with self.assertRaises(ValidationError) as cm:
            _validate_evolve(node, [0])
        self.assertIn("3 elements", str(cm.exception))

    def test_evolve_wrong_element_count_too_many(self):
        node = lst(sym("evolve"), sym("state"), sym("h"), sym("extra"))
        with self.assertRaises(ValidationError) as cm:
            _validate_evolve(node, [0])
        self.assertIn("3 elements", str(cm.exception))

    def test_evolve_target_not_symbol(self):
        node = lst(sym("evolve"), num(5), sym("h"))
        with self.assertRaises(ValidationError) as cm:
            _validate_evolve(node, [0])
        self.assertIn("evolve target must be a symbol", str(cm.exception))

    def test_evolve_body_is_hamiltonian(self):
        node = lst(sym("evolve"), sym("state"), make_hamiltonian())
        _validate_evolve(node, [0])

    def test_evolve_body_invalid_expression_raises(self):
        node = lst(sym("evolve"), sym("state"), lst())
        with self.assertRaises(ValidationError):
            _validate_evolve(node, [0])


# ============================================================================
# _validate_measure
# ============================================================================

class TestValidateMeasure(unittest.TestCase):

    def _make_valid_measure(self) -> Node:
        handler = lst(sym(LAMBDA_SYMBOL), lst(sym("r")), sym("r"))
        return lst(sym("measure"), sym("state"), sym("obs"), handler)

    def test_valid_measure(self):
        _validate_measure(self._make_valid_measure(), [0])

    def test_measure_wrong_element_count_too_few(self):
        handler = lst(sym(LAMBDA_SYMBOL), lst(), sym("x"))
        node = lst(sym("measure"), sym("state"), handler)
        with self.assertRaises(ValidationError) as cm:
            _validate_measure(node, [0])
        self.assertIn("4 elements", str(cm.exception))

    def test_measure_wrong_element_count_too_many(self):
        handler = lst(sym(LAMBDA_SYMBOL), lst(), sym("x"))
        node = lst(sym("measure"), sym("s"), sym("obs"), handler, sym("extra"))
        with self.assertRaises(ValidationError) as cm:
            _validate_measure(node, [0])
        self.assertIn("4 elements", str(cm.exception))

    def test_measure_handler_atom_raises(self):
        node = lst(sym("measure"), sym("state"), sym("obs"), sym("not-a-handler"))
        with self.assertRaises(ValidationError) as cm:
            _validate_measure(node, [0])
        self.assertIn("handler must be a list", str(cm.exception))

    def test_measure_handler_wrong_element_count(self):
        handler = lst(sym(LAMBDA_SYMBOL), lst())  # only 2 elements
        node = lst(sym("measure"), sym("state"), sym("obs"), handler)
        with self.assertRaises(ValidationError) as cm:
            _validate_measure(node, [0])
        self.assertIn("handler must have 3 elements", str(cm.exception))

    def test_measure_handler_wrong_lambda_symbol(self):
        handler = lst(sym("not-lambda"), lst(sym("r")), sym("r"))
        node = lst(sym("measure"), sym("state"), sym("obs"), handler)
        with self.assertRaises(ValidationError) as cm:
            _validate_measure(node, [0])
        self.assertIn("lambda symbol", str(cm.exception))

    def test_measure_handler_lambda_is_list_raises(self):
        handler = lst(lst(sym("nested")), lst(sym("r")), sym("r"))
        node = lst(sym("measure"), sym("state"), sym("obs"), handler)
        with self.assertRaises(ValidationError) as cm:
            _validate_measure(node, [0])
        self.assertIn("lambda symbol", str(cm.exception))

    def test_measure_handler_arg_not_symbol(self):
        handler = lst(sym(LAMBDA_SYMBOL), lst(num(9)), sym("r"))
        node = lst(sym("measure"), sym("state"), sym("obs"), handler)
        with self.assertRaises(ValidationError) as cm:
            _validate_measure(node, [0])
        self.assertIn("argument must be a symbol", str(cm.exception))

    def test_measure_handler_body_invalid_expression(self):
        handler = lst(sym(LAMBDA_SYMBOL), lst(sym("r")), lst())
        node = lst(sym("measure"), sym("state"), sym("obs"), handler)
        with self.assertRaises(ValidationError):
            _validate_measure(node, [0])


# ============================================================================
# _validate_handler (standalone)
# ============================================================================

class TestValidateHandler(unittest.TestCase):

    def test_valid_handler_no_args(self):
        handler = lst(sym(LAMBDA_SYMBOL), lst(), sym("unit"))
        _validate_handler(handler, [0])

    def test_valid_handler_with_args(self):
        handler = lst(sym(LAMBDA_SYMBOL), lst(sym("a"), sym("b")), sym("a"))
        _validate_handler(handler, [0])

    def test_handler_is_atom_raises(self):
        with self.assertRaises(ValidationError) as cm:
            _validate_handler(sym("x"), [0])
        self.assertIn("handler must be a list", str(cm.exception))


# ============================================================================
# _validate_arg_list (standalone)
# ============================================================================

class TestValidateArgList(unittest.TestCase):

    def test_empty_arg_list_valid(self):
        _validate_arg_list(lst(), [0])

    def test_single_arg_valid(self):
        _validate_arg_list(lst(sym("x")), [0])

    def test_multiple_args_valid(self):
        _validate_arg_list(lst(sym("x"), sym("y"), sym("z")), [0])

    def test_arg_list_atom_raises(self):
        with self.assertRaises(ValidationError) as cm:
            _validate_arg_list(sym("x"), [0])
        self.assertIn("argument list must be a list", str(cm.exception))

    def test_arg_list_number_arg_raises(self):
        with self.assertRaises(ValidationError) as cm:
            _validate_arg_list(lst(sym("ok"), num(0)), [0])
        self.assertIn("argument must be a symbol", str(cm.exception))

    def test_arg_list_list_arg_raises(self):
        with self.assertRaises(ValidationError) as cm:
            _validate_arg_list(lst(lst(sym("nested"))), [0])
        self.assertIn("argument must be a symbol", str(cm.exception))


# ============================================================================
# ValidationError properties
# ============================================================================

class TestValidationErrorDetails(unittest.TestCase):

    def test_error_captures_location(self):
        node = loc_sym("bad", line=5, col=10)
        try:
            from hpl.axioms.validator import _fail
            _fail("test error", node, [0, 1])
        except ValidationError as e:
            self.assertEqual(e.location.line, 5)
            self.assertEqual(e.location.column, 10)
            self.assertEqual(e.path, [0, 1])
            self.assertIn("test error", str(e))
            self.assertIn("5:10", str(e))

    def test_error_without_location(self):
        node = sym("no-loc")
        try:
            from hpl.axioms.validator import _fail
            _fail("bare error", node, [])
        except ValidationError as e:
            self.assertIn("bare error", str(e))


# ============================================================================
# Integration: full programs through validate_program
# ============================================================================

class TestIntegrationValidateProgram(unittest.TestCase):

    def test_full_valid_program(self):
        hamiltonian = lst(
            sym("hamiltonian"),
            lst(sym("term"), sym("OP_A"), num(1.0)),
            lst(sym("term"), sym("OP_B"), num(-0.5)),
        )
        op = lst(sym("operator"), sym("op_x"), lst(sym(LAMBDA_SYMBOL), lst(sym("q")), hamiltonian))
        inv = lst(sym("invariant"), sym("energy_bounded"), sym("true"))
        sched = lst(sym("scheduler"), sym("round_robin"), sym("default"))
        obs = lst(sym("observer"), sym("measure_all"), sym("z_basis"))
        validate_program([op, inv, sched, obs])

    def test_operator_with_evolve_body(self):
        hamiltonian = lst(sym("hamiltonian"), lst(sym("term"), sym("H"), num(1.0)))
        evolve = lst(sym("evolve"), sym("psi"), hamiltonian)
        op = lst(sym("operator"), sym("evolve_op"), lst(sym(LAMBDA_SYMBOL), lst(), evolve))
        validate_program([op])

    def test_operator_with_measure_body(self):
        handler = lst(sym(LAMBDA_SYMBOL), lst(sym("result")), sym("result"))
        measure = lst(sym("measure"), sym("state"), sym("obs"), handler)
        op = lst(sym("operator"), sym("measure_op"), lst(sym(LAMBDA_SYMBOL), lst(), measure))
        validate_program([op])

    def test_surface_symbol_in_expression_body(self):
        """A surface symbol nested inside an operator body is rejected."""
        bad_body = lst(sym(LAMBDA_SYMBOL), lst(), lst(sym("buy"), sym("x")))
        bad_op = lst(sym("operator"), sym("bad"), bad_body)
        with self.assertRaises(ValidationError):
            validate_program([bad_op])

    def test_nested_apply_expressions(self):
        """Deeply nested generic expressions should all validate."""
        inner = lst(sym("add"), sym("a"), sym("b"))
        middle = lst(sym("mul"), inner, num(2))
        outer = lst(sym("neg"), middle)
        form = lst(sym("invariant"), sym("nested"), outer)
        validate_program([form])


if __name__ == "__main__":
    unittest.main()
