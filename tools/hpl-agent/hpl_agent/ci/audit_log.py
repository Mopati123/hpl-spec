from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from .evidence_chain import TurnEvidence

@dataclass
class AuditLog:
    path: Path

    def __post_init__(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, entry: TurnEvidence) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")

    def replay(self) -> list[TurnEvidence]:
        if not self.path.exists():
            return []
        entries = []
        for line in self.path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            entries.append(TurnEvidence(**d))
        return entries

    def verify_integrity(self) -> bool:
        entries = self.replay()
        for i, entry in enumerate(entries):
            if i == 0:
                if entry.prev_leaf_digest != "":
                    return False
            else:
                import hashlib, json as _json
                prev = entries[i - 1]
                expected = hashlib.sha256(
                    _json.dumps(prev.to_dict(), sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest()
                if entry.prev_leaf_digest != expected:
                    return False
        return True
