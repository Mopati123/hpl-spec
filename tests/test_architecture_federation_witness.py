import json
from pathlib import Path

from hpl.architecture import build_federation_receipt, validate_member_receipt

ROOT = Path(__file__).parents[1]
REGISTRY = json.loads((ROOT / "federation" / "members.v1.json").read_text(encoding="utf-8"))
CERTIFICATION = json.loads((ROOT / "federation" / "certification.v1.json").read_text(encoding="utf-8"))


def test_anchored_member_receipts_match_registry_and_contract():
    by_architecture = {member["architecture_id"]: member for member in REGISTRY["members"]}
    receipts = CERTIFICATION["member_receipts"]
    assert len(receipts) == len(by_architecture) == 4
    for receipt in receipts:
        validate_member_receipt(
            receipt,
            by_architecture[receipt["architecture_id"]],
            registry_hpl_commit=REGISTRY["hpl_commit"],
        )


def test_anchored_aggregate_is_reproducible_from_member_receipts():
    rebuilt = build_federation_receipt(REGISTRY, CERTIFICATION["member_receipts"])
    assert rebuilt == CERTIFICATION["aggregate_receipt"]
    assert rebuilt["member_count"] == 4
    assert rebuilt["execution_owner"] == "hpl.scheduler"
