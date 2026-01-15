"""Custom errors for parsing, macro expansion, and validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .ast import SourceLocation


@dataclass
class HplError(Exception):
    message: str
    location: Optional[SourceLocation] = None
    path: Optional[List[int]] = None

    def __str__(self) -> str:
        parts = [self.message]
        if self.location:
            parts.append(f"@{self.location.line}:{self.location.column}")
        if self.path:
            parts.append(f"path={self.path}")
        return " ".join(parts)


class ParseError(HplError):
    """Raised when surface parsing fails."""


class MacroExpansionError(HplError):
    """Raised when macro expansion fails."""


class ValidationError(HplError):
    """Raised when axiomatic validation fails."""
