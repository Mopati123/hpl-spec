from __future__ import annotations
import datetime, hashlib, json
from dataclasses import dataclass, field
from .merkle import hash_leaf, compute_root
from .signer import Ed25519Signer

@dataclass
class TurnEvidence:
    turn_index: int
    session_id: str
    prompt_digest: str
    response_digest: str
    tool_calls: list[dict]
    input_tokens: int
    output_tokens: int
    timestamp_iso: str
    prev_leaf_digest: str

    def to_dict(self) -> dict:
        return {
            "turn_index": self.turn_index,
            "session_id": self.session_id,
            "prompt_digest": self.prompt_digest,
            "response_digest": self.response_digest,
            "tool_calls": self.tool_calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "timestamp_iso": self.timestamp_iso,
            "prev_leaf_digest": self.prev_leaf_digest,
        }

    @classmethod
    def create(cls, turn_index: int, session_id: str, prompt: str, response: str,
               tool_calls: list[dict], input_tokens: int, output_tokens: int,
               prev_leaf_digest: str = "") -> "TurnEvidence":
        return cls(
            turn_index=turn_index,
            session_id=session_id,
            prompt_digest=hashlib.sha256(prompt.encode()).hexdigest(),
            response_digest=hashlib.sha256(response.encode()).hexdigest(),
            tool_calls=tool_calls,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            timestamp_iso=datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
            prev_leaf_digest=prev_leaf_digest,
        )

@dataclass
class FinalizedChain:
    session_id: str
    merkle_root: str
    signature: str
    leaf_count: int
    bundle_path: str | None = None

@dataclass
class EvidenceChain:
    session_id: str
    leaves: list[TurnEvidence] = field(default_factory=list)
    merkle_root: str | None = None
    signature: str | None = None

    def append_turn(self, turn: TurnEvidence) -> None:
        self.leaves.append(turn)
        self.merkle_root = None  # invalidate cached root

    def _compute_root(self) -> str:
        leaf_hashes = [hash_leaf(leaf.to_dict()) for leaf in self.leaves]
        return compute_root(leaf_hashes)

    def finalize(self, signer: Ed25519Signer) -> FinalizedChain:
        root = self._compute_root()
        self.merkle_root = root
        payload = f"{self.session_id}:{root}".encode()
        self.signature = signer.sign(payload)
        return FinalizedChain(
            session_id=self.session_id,
            merkle_root=root,
            signature=self.signature,
            leaf_count=len(self.leaves),
        )

    def verify(self, signer: Ed25519Signer) -> bool:
        if self.merkle_root is None or self.signature is None:
            return False
        root = self._compute_root()
        if root != self.merkle_root:
            return False
        payload = f"{self.session_id}:{root}".encode()
        return signer.verify(payload, self.signature)
