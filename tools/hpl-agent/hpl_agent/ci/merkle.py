from __future__ import annotations
import hashlib, json

def canonical_json(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()

def hash_leaf(content: dict) -> str:
    return hashlib.sha256(canonical_json(content)).hexdigest()

def hash_pair(left: str, right: str) -> str:
    combined = (left + right).encode()
    return hashlib.sha256(combined).hexdigest()

def compute_root(leaves: list[str]) -> str:
    if not leaves:
        return hashlib.sha256(b"empty").hexdigest()
    if len(leaves) == 1:
        return leaves[0]
    current = list(leaves)
    while len(current) > 1:
        next_level = []
        for i in range(0, len(current), 2):
            left = current[i]
            right = current[i + 1] if i + 1 < len(current) else left
            next_level.append(hash_pair(left, right))
        current = next_level
    return current[0]
