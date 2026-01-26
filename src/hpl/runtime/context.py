"""Runtime context for scheduler-approved execution plans."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PUBLIC_KEY = ROOT / "config" / "keys" / "ci_ed25519.pub"
DEFAULT_TIMESTAMP = "1970-01-01T00:00:00Z"


@dataclass(frozen=True)
class RuntimeContext:
    determinism_mode: str = "deterministic"
    epoch_anchor_path: Optional[Path] = None
    epoch_sig_path: Optional[Path] = None
    ci_pubkey_path: Path = DEFAULT_PUBLIC_KEY
    trace_sink: Optional[Path] = None
    observers: Optional[List[str]] = None
    timestamp: str = DEFAULT_TIMESTAMP
