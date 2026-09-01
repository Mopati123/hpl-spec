import copy
import json
from pathlib import Path

import pytest

from hpl.architecture.federation_registry import validate_federation_registry
from hpl.errors import ValidationError

REGISTRY_PATH = Path(__file__).parents[1] / "federation" / "members.v1.json"
CERTIFIED_HPL_ROOT = "9f540740b5c82a2e0375fa8508ca2139fbf994d7"
CERTIFIED_MEMBER_COMMITS = {
    "Mopati123/ApexQuantumICT": "ee4705f9ea2b32eabb898dfa40b5c8917fee582d",
    "Mopati123/pulafeed-prototype": "920807052fdb00581ddd9481fc136cadb246f0fc",
    "Mopati123/easy-banking-os": "56c328eb707d1db84f7d6adfc587f5e5a90a7c93",
    "Mopati123/QuantMuse": "e1742ecae6e2d3b3c0af5d5f9b376a9714582a20",
}


def _registry():
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def test_canonical_federation_registry_is_admissible():
    registry = _registry()
    validate_federation_registry(registry)
    assert registry["execution_owner"] == "hpl.scheduler"
    assert registry["hpl_commit"] == CERTIFIED_HPL_ROOT
    assert len(registry["members"]) == 4
    assert {member["repository"]: member["commit"] for member in registry["members"]} == CERTIFIED_MEMBER_COMMITS


def test_member_architecture_ids_are_unique():
    registry = _registry()
    registry["members"][1]["architecture_id"] = registry["members"][0]["architecture_id"]
    with pytest.raises(ValidationError, match="duplicate federation architecture_id"):
        validate_federation_registry(registry)


def test_member_repositories_are_unique():
    registry = _registry()
    registry["members"][1]["repository"] = registry["members"][0]["repository"]
    with pytest.raises(ValidationError, match="duplicate federation repository"):
        validate_federation_registry(registry)


def test_registry_cannot_reassign_execution_authority():
    registry = _registry()
    registry["execution_owner"] = "domain.scheduler"
    with pytest.raises(ValidationError, match="execution authority drift"):
        validate_federation_registry(registry)


def test_registry_refuses_unpinned_member_commit():
    registry = copy.deepcopy(_registry())
    registry["members"][0]["commit"] = "main"
    with pytest.raises(ValidationError, match="40-character hexadecimal SHA"):
        validate_federation_registry(registry)


def test_registry_refuses_non_hex_member_commit():
    registry = copy.deepcopy(_registry())
    registry["members"][0]["commit"] = "z" * 40
    with pytest.raises(ValidationError, match="40-character hexadecimal SHA"):
        validate_federation_registry(registry)


def test_registry_refuses_non_hex_hpl_commit():
    registry = copy.deepcopy(_registry())
    registry["hpl_commit"] = "z" * 40
    with pytest.raises(ValidationError, match="40-character hexadecimal HPL commit SHA"):
        validate_federation_registry(registry)
