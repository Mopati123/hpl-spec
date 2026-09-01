"""Deterministic member and federation certification for ArchitectureIR federation."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, Iterable, List

from ..errors import ValidationError
from .compiler import compile_architecture_spec, lower_architecture_ir_to_program_ir
from .federation_contract import federation_contract
from .federation_registry import validate_federation_registry

MEMBER_RECEIPT_VERSION = "1.0.0"
FEDERATION_RECEIPT_VERSION = "1.0.0"
_SHA40_RE = re.compile(r"[0-9a-f]{40}")


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _require_sha40(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or _SHA40_RE.fullmatch(value) is None:
        raise ValidationError(f"{label} requires a lowercase 40-character hexadecimal commit SHA")
    return value


def _merkle_root(leaves: Iterable[str]) -> str:
    level = list(leaves)
    if not level:
        raise ValidationError("federation receipt requires at least one member digest")
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [
            hashlib.sha256(bytes.fromhex(level[i]) + bytes.fromhex(level[i + 1])).hexdigest()
            for i in range(0, len(level), 2)
        ]
    return level[0]


def build_member_receipt(
    spec: Dict[str, Any],
    registry_member: Dict[str, Any],
    *,
    hpl_commit: str,
    repository_commit: str | None = None,
) -> Dict[str, Any]:
    """Compile one domain spec and bind it to an independently observed checkout SHA."""
    hpl_commit = _require_sha40(hpl_commit, label="member certification HPL commit")
    observed_commit = _require_sha40(
        repository_commit if repository_commit is not None else registry_member.get("commit"),
        label="member certification repository commit",
    )
    if spec.get("architecture_id") != registry_member.get("architecture_id"):
        raise ValidationError("member architecture_id does not match federation registry")
    if spec.get("domain") != registry_member.get("domain"):
        raise ValidationError("member domain does not match federation registry")

    architecture_ir = compile_architecture_spec(spec)
    program_ir = lower_architecture_ir_to_program_ir(architecture_ir)
    contract = federation_contract()
    receipt = {
        "receipt_type": "hpl.architecture-federation.member",
        "receipt_version": MEMBER_RECEIPT_VERSION,
        "repository": registry_member["repository"],
        "branch": registry_member["branch"],
        "repository_commit": observed_commit,
        "architecture_path": registry_member["architecture_path"],
        "architecture_id": architecture_ir.architecture_id,
        "domain": architecture_ir.domain,
        "hpl_commit": hpl_commit,
        "federation_contract_id": contract["contract_id"],
        "federation_contract_version": contract["version"],
        "execution_owner": architecture_ir.authority["execution_owner"],
        "source_digest": architecture_ir.source_digest,
        "architecture_ir_digest": _sha256(architecture_ir.to_dict()),
        "program_ir_digest": _sha256(program_ir),
        "collapse_policy": program_ir["scheduler"]["collapse_policy"],
        "evidence_required": architecture_ir.evidence_contract["required"],
        "reconciliation_required": architecture_ir.reconciliation_contract["required"],
    }
    receipt["receipt_sha256"] = _sha256(receipt)
    return receipt


def validate_member_receipt(
    receipt: Dict[str, Any],
    registry_member: Dict[str, Any],
    *,
    registry_hpl_commit: str,
) -> None:
    if receipt.get("receipt_type") != "hpl.architecture-federation.member":
        raise ValidationError("unexpected federation member receipt type")
    if receipt.get("receipt_version") != MEMBER_RECEIPT_VERSION:
        raise ValidationError("unsupported federation member receipt version")
    _require_sha40(registry_hpl_commit, label="federation registry HPL commit")
    _require_sha40(receipt.get("hpl_commit"), label="federation member receipt HPL commit")
    _require_sha40(receipt.get("repository_commit"), label="federation member receipt repository commit")
    _require_sha40(registry_member.get("commit"), label="federation registry member commit")
    for field in (
        "repository",
        "branch",
        "repository_commit",
        "architecture_path",
        "architecture_id",
        "domain",
    ):
        registry_field = "commit" if field == "repository_commit" else field
        if receipt.get(field) != registry_member.get(registry_field):
            raise ValidationError(f"federation member receipt {field} drift")
    if receipt.get("hpl_commit") != registry_hpl_commit:
        raise ValidationError("federation member receipt HPL commit drift")

    contract = federation_contract()
    expected_contract_fields = {
        "federation_contract_id": contract["contract_id"],
        "federation_contract_version": contract["version"],
        "execution_owner": contract["execution_owner"],
        "collapse_policy": contract["program_ir_collapse_policy"],
        "evidence_required": contract["evidence_required"],
        "reconciliation_required": contract["reconciliation_required"],
    }
    for field, expected in expected_contract_fields.items():
        if receipt.get(field) != expected:
            raise ValidationError(f"federation member receipt {field} contract drift")

    supplied_digest = receipt.get("receipt_sha256")
    if not isinstance(supplied_digest, str) or len(supplied_digest) != 64:
        raise ValidationError("federation member receipt digest is malformed")
    unsigned = dict(receipt)
    unsigned.pop("receipt_sha256", None)
    if _sha256(unsigned) != supplied_digest:
        raise ValidationError("federation member receipt digest mismatch")


def build_federation_receipt(
    registry: Dict[str, Any],
    member_receipts: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Validate the exact registry membership set and aggregate it into one Merkle witness."""
    validate_federation_registry(registry)
    by_architecture = {member["architecture_id"]: member for member in registry["members"]}
    if len(member_receipts) != len(by_architecture):
        raise ValidationError("federation receipt set does not match registry cardinality")

    seen = set()
    normalized = []
    for receipt in member_receipts:
        architecture_id = receipt.get("architecture_id")
        if architecture_id in seen:
            raise ValidationError("duplicate federation member receipt")
        member = by_architecture.get(architecture_id)
        if member is None:
            raise ValidationError("federation receipt contains unregistered architecture")
        validate_member_receipt(
            receipt,
            member,
            registry_hpl_commit=registry["hpl_commit"],
        )
        seen.add(architecture_id)
        normalized.append(receipt)

    if seen != set(by_architecture):
        raise ValidationError("federation receipt set is incomplete")

    normalized.sort(key=lambda item: item["architecture_id"])
    leaf_digests = [item["receipt_sha256"] for item in normalized]
    federation = {
        "receipt_type": "hpl.architecture-federation.aggregate",
        "receipt_version": FEDERATION_RECEIPT_VERSION,
        "registry_id": registry["registry_id"],
        "registry_version": registry["registry_version"],
        "registry_sha256": _sha256(registry),
        "hpl_commit": registry["hpl_commit"],
        "federation_contract_id": registry["federation_contract_id"],
        "federation_contract_version": registry["federation_contract_version"],
        "execution_owner": registry["execution_owner"],
        "member_count": len(normalized),
        "members": [
            {
                "architecture_id": item["architecture_id"],
                "repository": item["repository"],
                "repository_commit": item["repository_commit"],
                "receipt_sha256": item["receipt_sha256"],
            }
            for item in normalized
        ],
        "merkle_root": _merkle_root(leaf_digests),
    }
    federation["receipt_sha256"] = _sha256(federation)
    return federation
