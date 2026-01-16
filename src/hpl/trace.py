"""Traceability metadata (tooling-only)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .ast import Node


@dataclass
class TraceNode:
    node_id: str
    phase: str
    path: List[int]
    kind: str
    value: Optional[str]
    location: Optional[Dict[str, int]]


class TraceCollector:
    def __init__(self, program_id: str = "unknown") -> None:
        self.program_id = program_id
        self.nodes: List[TraceNode] = []
        self.mappings: List[Dict[str, str]] = []
        self.ir_terms: List[Dict[str, object]] = []
        self._phase_nodes: Dict[str, Dict[int, str]] = {}
        self._phase_paths: Dict[str, Dict[Tuple[int, ...], str]] = {}
        self._phase_counts: Dict[str, int] = {}
        self._recorded_phases: set[str] = set()

    def record_phase(self, program: List[Node], phase: str) -> None:
        if phase in self._recorded_phases:
            return
        self._recorded_phases.add(phase)
        self._phase_nodes.setdefault(phase, {})
        self._phase_paths.setdefault(phase, {})
        self._phase_counts.setdefault(phase, 0)

        for idx, form in enumerate(program):
            for node, path in _iter_with_path(form, [idx]):
                self._assign_node(node, phase, path)

    def map_nodes(self, source: Node, source_phase: str, target: Node, target_phase: str, step: str) -> None:
        source_id = self._phase_nodes.get(source_phase, {}).get(id(source))
        target_id = self._phase_nodes.get(target_phase, {}).get(id(target))
        if not source_id or not target_id:
            return
        self.mappings.append({"from": source_id, "to": target_id, "step": step})

    def map_by_path(self, source_phase: str, target_phase: str, step: str) -> None:
        source_paths = self._phase_paths.get(source_phase, {})
        target_paths = self._phase_paths.get(target_phase, {})
        if not source_paths or not target_paths:
            return
        for path, target_id in target_paths.items():
            source_id = source_paths.get(path)
            if source_id:
                self.mappings.append({"from": source_id, "to": target_id, "step": step})

    def record_ir_term(self, term_index: int, source_node: Node, source_phase: str, operator_id: str) -> None:
        source_id = self._phase_nodes.get(source_phase, {}).get(id(source_node))
        if not source_id:
            return
        self.ir_terms.append(
            {
                "term_index": term_index,
                "source_node": source_id,
                "operator_id": operator_id,
            }
        )

    def to_dict(self) -> Dict[str, object]:
        return {
            "version": "1.0",
            "program_id": self.program_id,
            "nodes": [node.__dict__ for node in self.nodes],
            "mappings": list(self.mappings),
            "ir_terms": list(self.ir_terms),
        }

    def write_json(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    def _assign_node(self, node: Node, phase: str, path: List[int]) -> None:
        node_key = id(node)
        if node_key in self._phase_nodes[phase]:
            return
        self._phase_counts[phase] += 1
        node_id = f"{phase}:{self._phase_counts[phase]}"
        self._phase_nodes[phase][node_key] = node_id
        self._phase_paths[phase][tuple(path)] = node_id
        location = None
        if node.location:
            location = {"line": node.location.line, "column": node.location.column}
        kind = "list" if node.is_list else "atom"
        value = node.value if isinstance(node.value, str) else None
        self.nodes.append(
            TraceNode(
                node_id=node_id,
                phase=phase,
                path=list(path),
                kind=kind,
                value=value,
                location=location,
            )
        )


def _iter_with_path(node: Node, path: List[int]) -> Iterable[Tuple[Node, List[int]]]:
    yield node, list(path)
    if node.is_list:
        for idx, child in enumerate(node.as_list()):
            yield from _iter_with_path(child, path + [idx])
