"""AST node types with source locations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List, Optional, Union


@dataclass(frozen=True)
class SourceLocation:
    line: int
    column: int


@dataclass(frozen=True)
class Node:
    value: Union[str, float, int, List["Node"]]
    location: Optional[SourceLocation] = None

    @property
    def is_list(self) -> bool:
        return isinstance(self.value, list)

    @property
    def is_atom(self) -> bool:
        return not self.is_list

    def as_list(self) -> List["Node"]:
        if not self.is_list:
            raise TypeError("Expected list node")
        return self.value

    def as_atom(self) -> Union[str, float, int]:
        if self.is_list:
            raise TypeError("Expected atom node")
        return self.value

    def to_data(self) -> Any:
        if self.is_list:
            return [child.to_data() for child in self.as_list()]
        return self.as_atom()


def iter_nodes(node: Node) -> Iterable[Node]:
    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        if current.is_list:
            stack.extend(reversed(current.as_list()))
