from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from hpl.epoch_witness_protocol import (
    EPOCH_WITNESS_PROTOCOL_ID,
    EPOCH_WITNESS_PROTOCOL_VERSION,
    EpochWitnessStage,
    epoch_witness_catalog,
    resolve_epoch_witness_contract,
    validate_epoch_witness_record,
)


ROOT = Path(__file__).resolve().parents[1]
ANCHOR_EPOCH_PATH = ROOT / "tools" / "anchor_epoch.py"


def _load_anchor_epoch_module():
    spec = importlib.util.spec_from_file_location("anchor_epoch_protocol_test", ANCHOR_EPOCH_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_protocol_identity_is_frozen() -> None:
    assert EPOCH_WITNESS_PROTOCOL_ID == "hpl.epoch-witness"
    assert EPOCH_WITNESS_PROTOCOL_VERSION == "1.0.0"


def test_catalog_has_unique_typed_stage_contracts() -> None:
    catalog = epoch_witness_catalog()
    assert set(catalog) == {stage.value for stage in EpochWitnessStage}
    assert catalog["epoch_anchor"]["attestation"] == "epoch_anchor_witness"
    assert catalog["epoch_anchor"]["role"] == "anchor_attestation"


def test_unknown_stage_is_refused() -> None:
    with pytest.raises(ValueError, match="unknown epoch witness stage"):
        resolve_epoch_witness_contract("epoch_signature_maybe")


def test_anchor_attestation_does_not_overclaim_trust_or_authority() -> None:
    contract = resolve_epoch_witness_contract(EpochWitnessStage.EPOCH_ANCHOR)
    assert contract.proves_anchor_digest is True
    assert contract.proves_signature_presence is False
    assert contract.proves_signature_verification is False
    assert contract.implies_execution_authorization is False


def test_actual_epoch_anchor_witness_conforms_to_protocol() -> None:
    anchor_epoch = _load_anchor_epoch_module()
    anchor = anchor_epoch.build_epoch_anchor(
        epoch_id="protocol-test",
        timestamp="1970-01-01T00:00:00Z",
        git_commit="0" * 40,
        root=ROOT,
        emit_witness=True,
    )

    record = anchor["papas_witness_record"]
    contract = validate_epoch_witness_record(record)
    assert contract.stage is EpochWitnessStage.EPOCH_ANCHOR
    assert record["artifact_digests"].keys() == {"epoch_anchor"}


def test_epoch_anchor_witness_is_deterministic_for_same_anchor_inputs() -> None:
    anchor_epoch = _load_anchor_epoch_module()
    kwargs = {
        "epoch_id": "determinism-test",
        "timestamp": "1970-01-01T00:00:00Z",
        "git_commit": "1" * 40,
        "root": ROOT,
        "emit_witness": True,
    }
    first = anchor_epoch.build_epoch_anchor(**kwargs)
    second = anchor_epoch.build_epoch_anchor(**kwargs)

    assert first["papas_witness_record"] == second["papas_witness_record"]
    assert first["papas_witness_digest"] == second["papas_witness_digest"]
