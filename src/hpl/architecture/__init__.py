"""Domain-neutral architecture federation boundary for HPL."""

from .models import ArchitectureIR, ArchitectureSpec
from .compiler import compile_architecture_spec, lower_architecture_ir_to_program_ir
from .validation import validate_architecture_ir, validate_architecture_spec

__all__ = [
    "ArchitectureIR",
    "ArchitectureSpec",
    "compile_architecture_spec",
    "lower_architecture_ir_to_program_ir",
    "validate_architecture_ir",
    "validate_architecture_spec",
]
