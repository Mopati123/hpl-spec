from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from ..trace import emit_witness_record


DEFAULT_TIMESTAMP = "1970-01-01T00:00:00Z"


@dataclass(frozen=True)
class DevChangeEventBundle:
    event: Dict[str, object]
    witness_record: Dict[str, object]


def build_dev_change_event(
    mode: str,
    branch: str,
    target_ledger_item: str,
    files_changed: List[str],
    test_results: str,
    tool_outputs: str,
    policy_version: str,
    timestamp: str = DEFAULT_TIMESTAMP,
) -> DevChangeEventBundle:
    if not timestamp:
        timestamp = DEFAULT_TIMESTAMP

    files_digest = _digest_text(_canonical_json(sorted(files_changed)))
    test_digest = _digest_text(test_results or "")
    tool_digest = _digest_text(tool_outputs or "")

    witness_record = emit_witness_record(
        observer_id="papas",
        stage="dev_change",
        artifact_digests={
            "files_changed_digest": files_digest,
            "test_results_digest": test_digest,
            "tool_outputs_digest": tool_digest,
        },
        timestamp=timestamp,
        attestation="dev_change_witness",
    )
    witness_digest = _digest_text(_canonical_json(witness_record))

    change_id = _digest_text(
        "|".join(
            [
                mode,
                branch,
                target_ledger_item,
                files_digest,
                test_digest,
                tool_digest,
                policy_version,
                timestamp,
            ]
        )
    )

    event = {
        "change_id": change_id,
        "timestamp": timestamp,
        "mode": mode,
        "branch": branch,
        "target_ledger_item": target_ledger_item,
        "files_changed_digest": files_digest,
        "test_results_digest": test_digest,
        "tool_outputs_digest": tool_digest,
        "papas_witness_digest": witness_digest,
        "policy_version": policy_version,
    }

    return DevChangeEventBundle(event=event, witness_record=witness_record)


def write_dev_change_event(event: Dict[str, object], path: Path) -> None:
    path.write_text(json.dumps(event, indent=2), encoding="utf-8")


def _canonical_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _digest_text(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"
