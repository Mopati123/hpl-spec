from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from typing import Any, Callable
from .evidence_chain import EvidenceChain, FinalizedChain, TurnEvidence
from .signer import Ed25519Signer
from .audit_log import AuditLog

@dataclass
class GovernedTurnResult:
    response: str
    tool_calls_made: list[dict]
    evidence: TurnEvidence
    turn_index: int

@dataclass
class GovernanceAgent:
    engine: Any  # RealQueryEngine — Any to avoid circular import
    signer: Ed25519Signer
    audit_log: AuditLog
    tool_definitions: list[dict]
    tool_executor: Callable[[str, dict], str]
    _chain: EvidenceChain = field(init=False)
    _turn_index: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self._chain = EvidenceChain(session_id=self.engine.session.session_id)
        # Wire the tool executor into the engine
        self.engine.tool_executor = self.tool_executor

    def run_governed_turn(self, prompt: str) -> GovernedTurnResult:
        result = self.engine.submit_message(
            prompt=prompt,
            tool_definitions=self.tool_definitions,
        )

        prev_digest = ""
        if self._chain.leaves:
            prev_dict = self._chain.leaves[-1].to_dict()
            import json as _json
            prev_digest = hashlib.sha256(
                _json.dumps(prev_dict, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()

        evidence = TurnEvidence.create(
            turn_index=self._turn_index,
            session_id=self.engine.session.session_id,
            prompt=prompt,
            response=result.output,
            tool_calls=result.tool_calls_made,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            prev_leaf_digest=prev_digest,
        )
        self._chain.append_turn(evidence)
        self.audit_log.append(evidence)
        self._turn_index += 1

        return GovernedTurnResult(
            response=result.output,
            tool_calls_made=result.tool_calls_made,
            evidence=evidence,
            turn_index=self._turn_index - 1,
        )

    def finalize_session(self) -> FinalizedChain:
        return self._chain.finalize(self.signer)
