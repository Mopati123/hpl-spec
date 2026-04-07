from __future__ import annotations
import hashlib, json, datetime
from dataclasses import dataclass

@dataclass
class ConsumptionWitness:
    """Signed delta-S witness: child agent reports consumption to parent."""
    session_id: str
    sub_token_id: str
    steps_consumed: int
    input_tokens_delta: int
    output_tokens_delta: int
    timestamp_iso: str
    signature: str = ""   # Ed25519 hex, filled by signer

    def payload_bytes(self) -> bytes:
        d = {
            "session_id": self.session_id,
            "sub_token_id": self.sub_token_id,
            "steps_consumed": self.steps_consumed,
            "input_tokens_delta": self.input_tokens_delta,
            "output_tokens_delta": self.output_tokens_delta,
            "timestamp_iso": self.timestamp_iso,
        }
        return json.dumps(d, sort_keys=True, separators=(",", ":")).encode()

    def sign(self, signer: Any) -> "ConsumptionWitness":  # Any = Ed25519Signer
        self.signature = signer.sign(self.payload_bytes())
        return self

    def verify(self, signer: Any) -> bool:
        return signer.verify(self.payload_bytes(), self.signature)

    @classmethod
    def create(cls, session_id: str, sub_token_id: str,
               steps: int, input_tokens: int, output_tokens: int) -> "ConsumptionWitness":
        return cls(
            session_id=session_id,
            sub_token_id=sub_token_id,
            steps_consumed=steps,
            input_tokens_delta=input_tokens,
            output_tokens_delta=output_tokens,
            timestamp_iso=datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
        )

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "sub_token_id": self.sub_token_id,
            "steps_consumed": self.steps_consumed,
            "input_tokens_delta": self.input_tokens_delta,
            "output_tokens_delta": self.output_tokens_delta,
            "timestamp_iso": self.timestamp_iso,
            "signature": self.signature,
        }

from typing import Any  # noqa: E402 (needed for forward ref)
