"""Domain-neutral architecture federation boundary for HPL."""

from .models import ArchitectureIR, ArchitectureSpec
from .compiler import compile_architecture_spec, lower_architecture_ir_to_program_ir
from .federation_contract import (
    EVIDENCE_REQUIRED,
    EXECUTION_OWNER,
    FEDERATION_CONTRACT_ID,
    FEDERATION_CONTRACT_VERSION,
    PROGRAM_IR_COLLAPSE_POLICY,
    RECONCILIATION_REQUIRED,
    federation_contract,
)
from .federation_registry import REGISTRY_ID, REGISTRY_VERSION, validate_federation_registry
from .validation import validate_architecture_ir, validate_architecture_spec

__all__ = [
    "ArchitectureIR",
    "ArchitectureSpec",
    "compile_architecture_spec",
    "lower_architecture_ir_to_program_ir",
    "validate_architecture_ir",
    "validate_architecture_spec",
    "FEDERATION_CONTRACT_ID",
    "FEDERATION_CONTRACT_VERSION",
    "EXECUTION_OWNER",
    "PROGRAM_IR_COLLAPSE_POLICY",
    "EVIDENCE_REQUIRED",
    "RECONCILIATION_REQUIRED",
    "federation_contract",
    "REGISTRY_ID",
    "REGISTRY_VERSION",
    "validate_federation_registry",
]
