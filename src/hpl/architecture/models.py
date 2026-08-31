"""Canonical data models for the ecosystem architecture join.

ArchitectureSpec is the author-facing declarative contract. ArchitectureIR is the
normalized, deterministic pre-execution representation. Neither object grants
execution authority; only the HPL scheduler may do so downstream.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class ArchitectureSpec:
    architecture_id: str
    domain: str
    states: List[Dict[str, Any]]
    observables: List[Dict[str, Any]]
    dynamics: List[Dict[str, Any]]
    proposals: List[Dict[str, Any]]
    constraints: List[Dict[str, Any]]
    invariants: List[Dict[str, Any]]
    authorities: List[Dict[str, Any]]
    effects: List[Dict[str, Any]]
    evidence: List[Dict[str, Any]]
    reconciliation: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, value: Dict[str, Any]) -> "ArchitectureSpec":
        return cls(
            architecture_id=value.get("architecture_id", ""),
            domain=value.get("domain", ""),
            states=list(value.get("states", [])),
            observables=list(value.get("observables", [])),
            dynamics=list(value.get("dynamics", [])),
            proposals=list(value.get("proposals", [])),
            constraints=list(value.get("constraints", [])),
            invariants=list(value.get("invariants", [])),
            authorities=list(value.get("authorities", [])),
            effects=list(value.get("effects", [])),
            evidence=list(value.get("evidence", [])),
            reconciliation=list(value.get("reconciliation", [])),
            metadata=dict(value.get("metadata", {})),
        )


@dataclass(frozen=True)
class ArchitectureIR:
    architecture_id: str
    domain: str
    states: List[Dict[str, Any]]
    observables: List[Dict[str, Any]]
    operators: List[Dict[str, Any]]
    invariants: List[Dict[str, Any]]
    authority: Dict[str, Any]
    evidence_contract: Dict[str, Any]
    reconciliation_contract: Dict[str, Any]
    source_digest: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "architecture_id": self.architecture_id,
            "domain": self.domain,
            "states": self.states,
            "observables": self.observables,
            "operators": self.operators,
            "invariants": self.invariants,
            "authority": self.authority,
            "evidence_contract": self.evidence_contract,
            "reconciliation_contract": self.reconciliation_contract,
            "source_digest": self.source_digest,
        }
