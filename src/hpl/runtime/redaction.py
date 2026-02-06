from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple


ROOT = Path(__file__).resolve().parents[3]

_SECRET_PATTERNS: List[Tuple[str, re.Pattern[str]]] = [
    ("private_key_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("openssh_key", re.compile(r"-----BEGIN OPENSSH PRIVATE KEY-----")),
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    (
        "aws_secret_key",
        re.compile(r"(?i)aws_secret_access_key\s*[:=]\s*[A-Za-z0-9/+=]{40}"),
    ),
    ("github_token", re.compile(r"ghp_[A-Za-z0-9]{36,}")),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("stripe_secret", re.compile(r"sk_(live|test)_[A-Za-z0-9]{16,}")),
    ("bearer_token", re.compile(r"Bearer\s+[A-Za-z0-9\-_=]{20,}")),
    (
        "secret_field",
        re.compile(r'(?i)"(api_key|apikey|secret|password)"\s*:\s*"([^"]{16,})"'),
    ),
]


def scan_artifacts(paths: List[Path]) -> Dict[str, object]:
    findings: List[Dict[str, object]] = []
    scanned: List[Dict[str, object]] = []

    for path in sorted(paths, key=lambda item: str(item)):
        try:
            data = path.read_bytes()
        except OSError:
            continue
        display_path = _display_path(path)
        scanned.append({"path": display_path, "digest": _digest_bytes(data)})
        findings.extend(_scan_bytes(data, display_path))

    findings = sorted(findings, key=lambda item: (item["path"], item["pattern"]))
    errors = [f"secret pattern {item['pattern']} in {item['path']}" for item in findings]

    return {
        "ok": not findings,
        "policy": {
            "version": "v1",
            "pattern_ids": [pattern_id for pattern_id, _ in _SECRET_PATTERNS],
        },
        "findings": findings,
        "errors": errors,
        "scanned": scanned,
    }


def _scan_bytes(data: bytes, display_path: str) -> List[Dict[str, object]]:
    text = data.decode("utf-8", errors="ignore")
    matches: List[Dict[str, object]] = []

    for pattern_id, regex in _SECRET_PATTERNS:
        for match in regex.finditer(text):
            value = match.group(0)
            if _looks_like_safe_hash(value):
                continue
            matches.append(
                {
                    "path": display_path,
                    "pattern": pattern_id,
                    "match_digest": _digest_text(value),
                }
            )
    if not matches:
        matches.extend(_scan_json(text, display_path))
    return matches


def _scan_json(text: str, display_path: str) -> List[Dict[str, object]]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return []
    findings: List[Dict[str, object]] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if not isinstance(key, str):
                continue
            if not _looks_like_secret_key(key):
                continue
            if not isinstance(value, str):
                continue
            if _looks_like_safe_hash(value):
                continue
            if len(value) < 16:
                continue
            findings.append(
                {
                    "path": display_path,
                    "pattern": "secret_key_field",
                    "match_digest": _digest_text(value),
                }
            )
    return findings


def _looks_like_secret_key(key: str) -> bool:
    lowered = key.lower()
    return any(token in lowered for token in ("secret", "password", "api_key", "apikey"))


def _looks_like_safe_hash(value: str) -> bool:
    if value.startswith("sha256:") and len(value) == 71:
        return True
    return False


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return path.name


def _digest_text(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _digest_bytes(value: bytes) -> str:
    digest = hashlib.sha256(value).hexdigest()
    return f"sha256:{digest}"
