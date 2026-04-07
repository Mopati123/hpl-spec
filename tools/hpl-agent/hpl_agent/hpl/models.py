from __future__ import annotations
import json
from dataclasses import dataclass, field

@dataclass
class ParseResult:
    success: bool
    ast_json: dict | None
    errors: list[str]
    source: str

    def to_json(self) -> str:
        return json.dumps({"success": self.success, "ast_json": self.ast_json, "errors": self.errors, "source": self.source})

    @classmethod
    def from_json(cls, s: str) -> "ParseResult":
        d = json.loads(s)
        return cls(**d)

@dataclass
class ValidationResult:
    valid: bool
    violated_axioms: list[str]
    witnesses: list[str]

    def to_json(self) -> str:
        return json.dumps({"valid": self.valid, "violated_axioms": self.violated_axioms, "witnesses": self.witnesses})

    @classmethod
    def from_json(cls, s: str) -> "ValidationResult":
        return cls(**json.loads(s))

@dataclass
class ExecutionPlan:
    token_id: str
    backend: str
    steps: list[dict]
    policy_summary: dict

    def to_json(self) -> str:
        return json.dumps({"token_id": self.token_id, "backend": self.backend, "steps": self.steps, "policy_summary": self.policy_summary})

    @classmethod
    def from_json(cls, s: str) -> "ExecutionPlan":
        return cls(**json.loads(s))

@dataclass
class RuntimeResult:
    success: bool
    output: str
    witness_records: list[dict]
    transcript: list[dict]
    refusal_reasons: list[str]

    def to_json(self) -> str:
        return json.dumps({"success": self.success, "output": self.output, "witness_records": self.witness_records, "transcript": self.transcript, "refusal_reasons": self.refusal_reasons})

    @classmethod
    def from_json(cls, s: str) -> "RuntimeResult":
        return cls(**json.loads(s))

@dataclass
class EvidenceBundle:
    bundle_id: str
    session_id: str
    artifacts: dict
    merkle_root: str
    signature: str | None = None

    def to_json(self) -> str:
        return json.dumps({"bundle_id": self.bundle_id, "session_id": self.session_id, "artifacts": self.artifacts, "merkle_root": self.merkle_root, "signature": self.signature})

    @classmethod
    def from_json(cls, s: str) -> "EvidenceBundle":
        return cls(**json.loads(s))
