import json
from pathlib import Path

import pytest

from hpl.architecture.federation_certification import (
    build_federation_receipt,
    build_member_receipt,
    validate_member_receipt,
)
from hpl.errors import ValidationError

ROOT = Path(__file__).parents[1]
REGISTRY = json.loads((ROOT / "federation" / "members.v1.json").read_text(encoding="utf-8"))


def _minimal_spec(member):
    return {
        "architecture_id": member["architecture_id"],
        "domain": member["domain"],
        "states": [{"id": "state"}],
        "observables": [{"id": "observe"}],
        "dynamics": [{"id": "evolve"}],
        "proposals": [{"id": "propose"}],
        "constraints": [{"id": "project"}],
        "invariants": [{"id": "scheduler_sovereignty", "expression": "execution_owner == hpl.scheduler"}],
        "authorities": [{"id": "execute", "kind": "execution", "owner": "hpl.scheduler"}],
        "effects": [{"id": "effect"}],
        "evidence": [{"id": "evidence"}],
        "reconciliation": [{"id": "reconcile"}],
        "metadata": {},
    }


def _receipts():
    return [
        build_member_receipt(
            _minimal_spec(member),
            member,
            hpl_commit=REGISTRY["hpl_commit"],
        )
        for member in REGISTRY["members"]
    ]


def test_member_receipt_is_deterministic_and_contract_bound():
    member = REGISTRY["members"][0]
    first = build_member_receipt(_minimal_spec(member), member, hpl_commit=REGISTRY["hpl_commit"])
    second = build_member_receipt(_minimal_spec(member), member, hpl_commit=REGISTRY["hpl_commit"])
    assert first == second
    assert first["execution_owner"] == "hpl.scheduler"
    assert first["evidence_required"] is True
    assert first["reconciliation_required"] is True
    validate_member_receipt(first, member, registry_hpl_commit=REGISTRY["hpl_commit"])


def test_member_receipt_refuses_tampering():
    member = REGISTRY["members"][0]
    receipt = build_member_receipt(_minimal_spec(member), member, hpl_commit=REGISTRY["hpl_commit"])
    receipt["execution_owner"] = "domain.scheduler"
    with pytest.raises(ValidationError, match="execution_owner contract drift"):
        validate_member_receipt(receipt, member, registry_hpl_commit=REGISTRY["hpl_commit"])


def test_federation_receipt_is_order_independent():
    receipts = _receipts()
    first = build_federation_receipt(REGISTRY, receipts)
    second = build_federation_receipt(REGISTRY, list(reversed(receipts)))
    assert first == second
    assert first["member_count"] == 4
    assert len(first["merkle_root"]) == 64
    assert len(first["receipt_sha256"]) == 64


def test_federation_receipt_refuses_missing_member():
    receipts = _receipts()
    with pytest.raises(ValidationError, match="cardinality"):
        build_federation_receipt(REGISTRY, receipts[:-1])


def test_federation_receipt_refuses_duplicate_member():
    receipts = _receipts()
    duplicated = receipts[:-1] + [receipts[0]]
    with pytest.raises(ValidationError, match="duplicate federation member receipt"):
        build_federation_receipt(REGISTRY, duplicated)
