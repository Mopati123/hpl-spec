"""Macro expansion from surface DSL into axiomatic core forms."""

from __future__ import annotations

from typing import Iterable, List, Set

from ...ast import Node, SourceLocation, iter_nodes
from ...errors import MacroExpansionError


def _collect_symbols(nodes: Iterable[Node]) -> List[str]:
    seen: Set[str] = set()
    ordered: List[str] = []
    for node in nodes:
        if node.is_atom and isinstance(node.value, str):
            symbol = node.value
            if symbol not in seen:
                seen.add(symbol)
                ordered.append(symbol)
    return ordered


def _make_symbol(value: str, location: SourceLocation | None) -> Node:
    return Node(value, location)


def _make_term(operator_id: str, location: SourceLocation | None) -> Node:
    return Node(
        [
            _make_symbol("term", location),
            _make_symbol(operator_id, location),
            Node(1.0, location),
        ],
        location,
    )


def expand_program(program: List[Node]) -> List[Node]:
    symbols = _collect_symbols(iter_nodes(Node(program)))
    if not symbols:
        raise MacroExpansionError("Surface program contains no symbols")

    terms: List[Node] = []
    for symbol in symbols:
        operator_id = f"SURF_{symbol}"
        terms.append(_make_term(operator_id, None))

    hamiltonian = Node([_make_symbol("hamiltonian", None), *terms], None)
    return [hamiltonian]
