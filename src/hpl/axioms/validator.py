"""Axiomatic BNF validator."""

from __future__ import annotations

from typing import List

from ..ast import Node
from ..errors import ValidationError
from ..trace import TraceCollector


LAMBDA_SYMBOL = "?"
SURFACE_SYMBOLS = {
    "defstrategy",
    "params",
    "let",
    "if",
    ">",
    "buy",
    "sell",
    "signal",
    "ma-diff",
    "price",
    "window",
    "threshold",
    "size",
}


def _is_symbol(node: Node) -> bool:
    return node.is_atom and isinstance(node.value, str)


def _is_number(node: Node) -> bool:
    return node.is_atom and isinstance(node.value, (int, float))


def _fail(message: str, node: Node, path: List[int]) -> None:
    raise ValidationError(message, node.location, path)


def validate_program(program: List[Node], trace: TraceCollector | None = None) -> None:
    if trace:
        trace.record_phase(program, "axiomatic")
        trace.map_by_path("expanded", "axiomatic", "expanded_to_axiomatic")

    for index, form in enumerate(program):
        _reject_surface_symbols(form, [index])
        _validate_form(form, [index])


def _reject_surface_symbols(node: Node, path: List[int]) -> None:
    if node.is_atom:
        if isinstance(node.value, str) and node.value in SURFACE_SYMBOLS:
            _fail("Surface symbol found after macro expansion", node, path)
        return

    for idx, item in enumerate(node.as_list()):
        _reject_surface_symbols(item, path + [idx])


def _validate_form(node: Node, path: List[int]) -> None:
    if node.is_atom:
        _fail("Form must be a list", node, path)

    if not node.as_list():
        _fail("Form cannot be empty", node, path)

    head = node.as_list()[0]
    if not _is_symbol(head):
        _fail("Form head must be a symbol", head, path + [0])

    head_value = head.value
    if head_value == "operator":
        _validate_operator(node, path)
    elif head_value == "invariant":
        _validate_invariant(node, path)
    elif head_value == "scheduler":
        _validate_scheduler(node, path)
    elif head_value == "observer":
        _validate_observer(node, path)
    else:
        _validate_expression(node, path)


def _validate_operator(node: Node, path: List[int]) -> None:
    items = node.as_list()
    if len(items) != 3:
        _fail("operator form must have 3 elements", node, path)
    if not _is_symbol(items[1]):
        _fail("operator name must be a symbol", items[1], path + [1])
    _validate_operator_body(items[2], path + [2])


def _validate_operator_body(node: Node, path: List[int]) -> None:
    if node.is_atom:
        _fail("operator body must be a list", node, path)
    items = node.as_list()
    if len(items) != 3:
        _fail("operator body must have 3 elements", node, path)
    if not _is_symbol(items[0]) or items[0].value != LAMBDA_SYMBOL:
        _fail("operator body must start with lambda symbol", items[0], path + [0])
    _validate_arg_list(items[1], path + [1])
    _validate_expression(items[2], path + [2])


def _validate_arg_list(node: Node, path: List[int]) -> None:
    if node.is_atom:
        _fail("argument list must be a list", node, path)
    for idx, item in enumerate(node.as_list()):
        if not _is_symbol(item):
            _fail("argument must be a symbol", item, path + [idx])


def _validate_invariant(node: Node, path: List[int]) -> None:
    items = node.as_list()
    if len(items) != 3:
        _fail("invariant form must have 3 elements", node, path)
    if not _is_symbol(items[1]):
        _fail("invariant name must be a symbol", items[1], path + [1])
    _validate_expression(items[2], path + [2])


def _validate_scheduler(node: Node, path: List[int]) -> None:
    items = node.as_list()
    if len(items) != 3:
        _fail("scheduler form must have 3 elements", node, path)
    if not _is_symbol(items[1]):
        _fail("scheduler name must be a symbol", items[1], path + [1])
    _validate_expression(items[2], path + [2])


def _validate_observer(node: Node, path: List[int]) -> None:
    items = node.as_list()
    if len(items) != 3:
        _fail("observer form must have 3 elements", node, path)
    if not _is_symbol(items[1]):
        _fail("observer name must be a symbol", items[1], path + [1])
    _validate_expression(items[2], path + [2])


def _validate_expression(node: Node, path: List[int]) -> None:
    if node.is_atom:
        return

    items = node.as_list()
    if not items:
        _fail("expression cannot be empty list", node, path)

    head = items[0]
    if not _is_symbol(head):
        _fail("expression head must be a symbol", head, path + [0])

    head_value = head.value
    if head_value == "hamiltonian":
        _validate_hamiltonian(node, path)
        return
    if head_value == "evolve":
        _validate_evolve(node, path)
        return
    if head_value == "measure":
        _validate_measure(node, path)
        return

    for idx, item in enumerate(items[1:], start=1):
        _validate_expression(item, path + [idx])


def _validate_hamiltonian(node: Node, path: List[int]) -> None:
    items = node.as_list()
    if len(items) < 2:
        _fail("hamiltonian must include at least one term", node, path)
    for idx, term in enumerate(items[1:], start=1):
        _validate_term(term, path + [idx])


def _validate_term(node: Node, path: List[int]) -> None:
    if node.is_atom:
        _fail("term must be a list", node, path)
    items = node.as_list()
    if len(items) != 3:
        _fail("term must have 3 elements", node, path)
    if not _is_symbol(items[0]) or items[0].value != "term":
        _fail("term must start with 'term'", items[0], path + [0])
    if not _is_symbol(items[1]):
        _fail("operator-ref must be a symbol", items[1], path + [1])
    if not _is_number(items[2]):
        _fail("coefficient must be a number", items[2], path + [2])


def _validate_evolve(node: Node, path: List[int]) -> None:
    items = node.as_list()
    if len(items) != 3:
        _fail("evolve must have 3 elements", node, path)
    if not _is_symbol(items[1]):
        _fail("evolve target must be a symbol", items[1], path + [1])
    _validate_expression(items[2], path + [2])


def _validate_measure(node: Node, path: List[int]) -> None:
    items = node.as_list()
    if len(items) != 4:
        _fail("measure must have 4 elements", node, path)
    _validate_expression(items[1], path + [1])
    _validate_expression(items[2], path + [2])
    _validate_handler(items[3], path + [3])


def _validate_handler(node: Node, path: List[int]) -> None:
    if node.is_atom:
        _fail("handler must be a list", node, path)
    items = node.as_list()
    if len(items) != 3:
        _fail("handler must have 3 elements", node, path)
    if not _is_symbol(items[0]) or items[0].value != LAMBDA_SYMBOL:
        _fail("handler must start with lambda symbol", items[0], path + [0])
    _validate_arg_list(items[1], path + [1])
    _validate_expression(items[2], path + [2])
