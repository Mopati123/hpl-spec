from __future__ import annotations
import json
import datetime
from dataclasses import dataclass, field, asdict
from pathlib import Path
from .compressor import CompressedState


@dataclass
class Checkpoint:
    session_id: str
    turn_index: int
    timestamp_iso: str
    warm_state: dict          # CompressedState as dict
    hot_messages: list[dict]  # last HOT_MESSAGES at checkpoint time
    input_tokens_at_checkpoint: int
    output_tokens_at_checkpoint: int

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_json(cls, s: str) -> "Checkpoint":
        d = json.loads(s)
        return cls(**d)


class ColdMemoryStore:
    """
    JSON-backed cold memory. One file per session, multiple checkpoints per file.
    """
    def __init__(self, store_dir: Path = Path(".hpl_memory")):
        self.store_dir = store_dir
        self.store_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(self, checkpoint: Checkpoint) -> Path:
        path = self.store_dir / f"{checkpoint.session_id}.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write(checkpoint.to_json().replace("\n", " ") + "\n")
        return path

    def load_latest_checkpoint(self, session_id: str) -> Checkpoint | None:
        path = self.store_dir / f"{session_id}.jsonl"
        if not path.exists():
            return None
        lines = [l.strip() for l in path.read_text().splitlines() if l.strip()]
        if not lines:
            return None
        return Checkpoint.from_json(lines[-1])

    def load_all_checkpoints(self, session_id: str) -> list[Checkpoint]:
        path = self.store_dir / f"{session_id}.jsonl"
        if not path.exists():
            return []
        checkpoints = []
        for line in path.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    checkpoints.append(Checkpoint.from_json(line))
                except Exception:
                    pass
        return checkpoints

    def list_sessions(self) -> list[str]:
        return [p.stem for p in self.store_dir.glob("*.jsonl")]

    @staticmethod
    def make_checkpoint(
        session_id: str,
        turn_index: int,
        warm_state: CompressedState,
        hot_messages: list[dict],
        input_tokens: int,
        output_tokens: int,
    ) -> Checkpoint:
        return Checkpoint(
            session_id=session_id,
            turn_index=turn_index,
            timestamp_iso=datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
            warm_state=warm_state.__dict__,
            hot_messages=hot_messages,
            input_tokens_at_checkpoint=input_tokens,
            output_tokens_at_checkpoint=output_tokens,
        )
