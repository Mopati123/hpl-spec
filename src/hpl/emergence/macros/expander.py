"""Macro expansion from surface DSL into axiomatic core forms."""

from __future__ import annotations

from typing import Iterable, List, Set, Tuple

from ...ast import Node, SourceLocation, iter_nodes
from ...errors import MacroExpansionError
from ...trace import TraceCollector


def _collect_symbol_nodes(nodes: Iterable[Node]) -> List[Tuple[str, Node]]:
    seen: Set[str] = set()
    ordered: List[Tuple[str, Node]] = []
    for node in nodes:
        if node.is_atom and isinstance(node.value, str):
            symbol = node.value
            if symbol not in seen:
                seen.add(symbol)
                ordered.append((symbol, node))
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


def expand_program(program: List[Node], trace: TraceCollector | None = None) -> List[Node]:
    if trace:
        trace.record_phase(program, "surface")

    symbols = _collect_symbol_nodes(iter_nodes(Node(program)))
    if not symbols:
        raise MacroExpansionError("Surface program contains no symbols")

    terms: List[Node] = []
    mappings: List[Tuple[Node, Node]] = []
    for symbol, source_node in symbols:
        operator_id = f"SURF_{symbol}"
        term_node = _make_term(operator_id, None)
        terms.append(term_node)
        mappings.append((source_node, term_node))

    hamiltonian = Node([_make_symbol("hamiltonian", None), *terms], None)
    expanded = [hamiltonian]

    if trace:
        trace.record_phase(expanded, "expanded")
        for source_node, term_node in mappings:
            trace.map_nodes(source_node, "surface", term_node, "expanded", "surface_to_expanded")

    return expanded
