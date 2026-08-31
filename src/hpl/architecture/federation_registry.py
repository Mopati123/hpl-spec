"""Validation primitives for the cross-repository ArchitectureIR federation registry."""

from __future__ import annotations

from typing import Any, Dict

from ..errors import ValidationError
from .federation_contract import (
    EXECUTION_OWNER,
    FEDERATION_CONTRACT_ID,
    FEDERATION_CONTRACT_VERSION,
)

REGISTRY_ID = "hpl.architecture-federation.members"
REGISTRY_VERSION = "1.0.0"
_REQUIRED_MEMBER_FIELDS = (
    "repository",
    "branch",
    "commit",
    "architecture_path",
    "architecture_id",
    "domain",
)


def validate_federation_registry(registry: Dict[str, Any]) -> None:
    """Refuse registry drift, duplicate identities, and malformed member pins."""
    if not isinstance(registry, dict):
        raise ValidationError("federation registry must be an object")
    if registry.get("registry_id") != REGISTRY_ID:
        raise ValidationError("unexpected federation registry identity")
    if registry.get("registry_version") != REGISTRY_VERSION:
        raise ValidationError("unsupported federation registry version")
    if registry.get("federation_contract_id") != FEDERATION_CONTRACT_ID:
        raise ValidationError("federation registry contract identity drift")
    if registry.get("federation_contract_version") != FEDERATION_CONTRACT_VERSION:
        raise ValidationError("federation registry contract version drift")
    if registry.get("execution_owner") != EXECUTION_OWNER:
        raise ValidationError("federation registry execution authority drift")

    hpl_commit = registry.get("hpl_commit")
    if not isinstance(hpl_commit, str) or len(hpl_commit) != 40:
        raise ValidationError("federation registry must pin a 40-character HPL commit SHA")

    members = registry.get("members")
    if not isinstance(members, list) or not members:
        raise ValidationError("federation registry must contain members")

    repositories = set()
    architecture_ids = set()
    for member in members:
        if not isinstance(member, dict):
            raise ValidationError("federation member must be an object")
        for field in _REQUIRED_MEMBER_FIELDS:
            value = member.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValidationError(f"federation member {field} must be a non-empty string")
        commit = member["commit"]
        if len(commit) != 40:
            raise ValidationError("federation member commit must be a 40-character SHA")
        repository = member["repository"]
        architecture_id = member["architecture_id"]
        if repository in repositories:
            raise ValidationError(f"duplicate federation repository: {repository}")
        if architecture_id in architecture_ids:
            raise ValidationError(f"duplicate federation architecture_id: {architecture_id}")
        repositories.add(repository)
        architecture_ids.add(architecture_id)
