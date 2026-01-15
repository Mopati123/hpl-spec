"""Surface DSL S-expression parser."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, List, Optional

from ...ast import Node, SourceLocation
from ...errors import ParseError


@dataclass(frozen=True)
class Token:
    kind: str
    value: Optional[str]
    location: SourceLocation


TOKEN_RE = re.compile(
    r"""
    (?P<WS>\s+)
  | (?P<COMMENT>;[^\n]*)
  | (?P<LPAREN>\()
  | (?P<RPAREN>\))
  | (?P<ATOM>[^\s();]+)
    """,
    re.VERBOSE,
)


def _tokenize(text: str) -> Iterable[Token]:
    line = 1
    col = 1
    pos = 0

    for match in TOKEN_RE.finditer(text):
        if match.start() != pos:
            raise ParseError("Unexpected character", SourceLocation(line, col))

        value = match.group(0)
        kind = match.lastgroup or "ATOM"
        location = SourceLocation(line, col)

        if kind == "LPAREN":
            yield Token("LPAREN", value, location)
        elif kind == "RPAREN":
            yield Token("RPAREN", value, location)
        elif kind == "ATOM":
            yield Token("ATOM", value, location)

        newline_count = value.count("\n")
        if newline_count:
            line += newline_count
            col = len(value.rsplit("\n", 1)[-1]) + 1
        else:
            col += len(value)

        pos = match.end()

    if pos != len(text):
        raise ParseError("Unexpected character", SourceLocation(line, col))


def _parse_atom(token: Token) -> Node:
    raw = token.value or ""
    try:
        if "." in raw:
            return Node(float(raw), token.location)
        return Node(int(raw), token.location)
    except ValueError:
        return Node(raw, token.location)


def parse_program(text: str) -> List[Node]:
    items: List[Node] = []
    stack: List[List[Node]] = []
    locations: List[SourceLocation] = []

    for token in _tokenize(text):
        if token.kind == "LPAREN":
            stack.append([])
            locations.append(token.location)
            continue
        if token.kind == "RPAREN":
            if not stack:
                raise ParseError("Unexpected ')'", token.location)
            content = stack.pop()
            start_location = locations.pop()
            node = Node(content, start_location)
            if stack:
                stack[-1].append(node)
            else:
                items.append(node)
            continue
        if token.kind == "ATOM":
            node = _parse_atom(token)
            if stack:
                stack[-1].append(node)
            else:
                items.append(node)
            continue

        raise ParseError(f"Unexpected token {token.kind}", token.location)

    if stack:
        raise ParseError("Unclosed '('", locations[-1])
    return items


def parse_file(path: str) -> List[Node]:
    with open(path, "r", encoding="utf-8") as handle:
        return parse_program(handle.read())
