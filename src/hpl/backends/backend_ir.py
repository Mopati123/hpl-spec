"""BackendIR data model and deterministic helpers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Dict, List


def canonical_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def digest_text(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def digest_program_ir(program_ir: Dict[str, object]) -> str:
    return digest_text(canonical_json(program_ir))


@dataclass(frozen=True)
class BackendIR:
    backend_target: str
    program_digest: str
    ops: List[Dict[str, object]]
    metadata: Dict[str, object]
    evidence: Dict[str, object]

    def to_dict(self) -> Dict[str, object]:
        return {
            "backend_target": self.backend_target,
            "program_digest": self.program_digest,
            "ops": list(self.ops),
            "metadata": dict(self.metadata),
            "evidence": dict(self.evidence),
        }
