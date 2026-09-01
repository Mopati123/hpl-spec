import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from hpl.runtime.engine import _validate_completion_requirements


def _entry(effect_type: str, *, ok: bool = True, artifacts=None):
    return {
        "effect_type": effect_type,
        "ok": ok,
        "artifact_digests": dict(artifacts or {}),
    }


def test_completion_requirements_are_additive_for_tracks_without_reconciliation():
    plan = {"status": "planned", "steps": []}
    assert _validate_completion_requirements(plan, []) == []


def test_required_reconciliation_effect_and_evidence_satisfy_completion():
    plan = {
        "completion_requirements": {
            "required_successful_effects": ["SIM_RECONCILE_TRADE"],
            "required_artifact_digests": ["shadow_reconciliation.json"],
        }
    }
    transcript = [
        _entry(
            "SIM_RECONCILE_TRADE",
            artifacts={"shadow_reconciliation.json": "sha256:abc"},
        )
    ]
    assert _validate_completion_requirements(plan, transcript) == []


def test_missing_required_reconciliation_effect_denies_completion():
    plan = {
        "completion_requirements": {
            "required_successful_effects": ["SIM_RECONCILE_TRADE"],
            "required_artifact_digests": ["shadow_reconciliation.json"],
        }
    }
    transcript = [
        _entry(
            "EMIT_TRADE_REPORT",
            artifacts={"shadow_reconciliation.json": "sha256:not-authoritative"},
        )
    ]
    assert _validate_completion_requirements(plan, transcript) == [
        "completion_effect_missing:SIM_RECONCILE_TRADE"
    ]


def test_failed_reconciliation_does_not_satisfy_effect_or_evidence_requirement():
    plan = {
        "completion_requirements": {
            "required_successful_effects": ["SIM_RECONCILE_TRADE"],
            "required_artifact_digests": ["shadow_reconciliation.json"],
        }
    }
    transcript = [
        _entry(
            "SIM_RECONCILE_TRADE",
            ok=False,
            artifacts={"shadow_reconciliation.json": "sha256:failed"},
        )
    ]
    assert _validate_completion_requirements(plan, transcript) == [
        "completion_effect_missing:SIM_RECONCILE_TRADE",
        "completion_evidence_missing:shadow_reconciliation.json",
    ]


def test_successful_effect_without_required_evidence_denies_completion():
    plan = {
        "completion_requirements": {
            "required_successful_effects": ["SIM_RECONCILE_TRADE"],
            "required_artifact_digests": ["shadow_reconciliation.json"],
        }
    }
    transcript = [_entry("SIM_RECONCILE_TRADE")]
    assert _validate_completion_requirements(plan, transcript) == [
        "completion_evidence_missing:shadow_reconciliation.json"
    ]
