from __future__ import annotations
import hashlib, json, datetime
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class TokenScope:
    """Represents the authority scope for a sub-token."""
    allowed_backends: tuple[str, ...]  # subset of parent's backends
    budget_steps: int                  # <= parent budget
    enable_io: bool                    # only True if parent allows it
    enable_net: bool                   # only True if parent allows it
    allow_tool_names: tuple[str, ...]  # subset of parent's tools

    def intersect(self, child_request: "TokenScope") -> "TokenScope":
        """Compute strict intersection — child gets at most what parent has."""
        return TokenScope(
            allowed_backends=tuple(b for b in child_request.allowed_backends if b in self.allowed_backends),
            budget_steps=min(self.budget_steps, child_request.budget_steps),
            enable_io=self.enable_io and child_request.enable_io,
            enable_net=self.enable_net and child_request.enable_net,
            allow_tool_names=tuple(t for t in child_request.allow_tool_names if t in self.allow_tool_names),
        )

    def to_dict(self) -> dict:
        return {
            "allowed_backends": list(self.allowed_backends),
            "budget_steps": self.budget_steps,
            "enable_io": self.enable_io,
            "enable_net": self.enable_net,
            "allow_tool_names": list(self.allow_tool_names),
        }


@dataclass(frozen=True)
class DerivedToken:
    """A sub-token derived from a parent token."""
    token_id: str       # SHA256(parent_token_id || child_scope_canonical_json)
    parent_token_id: str
    child_index: int
    scope: TokenScope
    issued_at: str      # ISO timestamp

    @classmethod
    def derive(cls, parent_token_id: str, child_scope: TokenScope, child_index: int) -> "DerivedToken":
        scope_json = json.dumps(child_scope.to_dict(), sort_keys=True, separators=(",", ":"))
        raw = f"{parent_token_id}||{scope_json}".encode()
        token_id = hashlib.sha256(raw).hexdigest()
        return cls(
            token_id=token_id,
            parent_token_id=parent_token_id,
            child_index=child_index,
            scope=child_scope,
            issued_at=datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
        )

    def to_dict(self) -> dict:
        return {
            "token_id": self.token_id,
            "parent_token_id": self.parent_token_id,
            "child_index": self.child_index,
            "scope": self.scope.to_dict(),
            "issued_at": self.issued_at,
        }


@dataclass
class TokenTree:
    """Manages a parent token and all its derived sub-tokens."""
    root_token_id: str
    root_scope: TokenScope
    children: list[DerivedToken] = field(default_factory=list)
    revoked_token_ids: set[str] = field(default_factory=set)

    def mint_child(self, requested_scope: TokenScope) -> DerivedToken:
        """Derive a child token as intersection of root scope and request."""
        effective_scope = self.root_scope.intersect(requested_scope)
        child = DerivedToken.derive(
            parent_token_id=self.root_token_id,
            child_scope=effective_scope,
            child_index=len(self.children),
        )
        self.children.append(child)
        return child

    def revoke(self, token_id: str) -> None:
        self.revoked_token_ids.add(token_id)

    def is_active(self, token_id: str) -> bool:
        return token_id not in self.revoked_token_ids

    def to_dict(self) -> dict:
        return {
            "root_token_id": self.root_token_id,
            "root_scope": self.root_scope.to_dict(),
            "children": [c.to_dict() for c in self.children],
            "revoked": list(self.revoked_token_ids),
        }
