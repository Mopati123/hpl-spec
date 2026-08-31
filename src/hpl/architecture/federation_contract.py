"""Stable identity and invariants for the universal architecture federation contract."""

from __future__ import annotations

from typing import Dict, Any

FEDERATION_CONTRACT_ID = "hpl.architecture-federation"
FEDERATION_CONTRACT_VERSION = "1.0.0"
EXECUTION_OWNER = "hpl.scheduler"
PROGRAM_IR_COLLAPSE_POLICY = "architecture_ir_scheduler_sovereignty"
EVIDENCE_REQUIRED = True
RECONCILIATION_REQUIRED = True


def federation_contract() -> Dict[str, Any]:
    """Return the deterministic public compatibility contract for domain adapters."""
    return {
        "contract_id": FEDERATION_CONTRACT_ID,
        "version": FEDERATION_CONTRACT_VERSION,
        "execution_owner": EXECUTION_OWNER,
        "program_ir_collapse_policy": PROGRAM_IR_COLLAPSE_POLICY,
        "evidence_required": EVIDENCE_REQUIRED,
        "reconciliation_required": RECONCILIATION_REQUIRED,
    }
