# QASM Lowering Rules (Subset) ? Spec

Purpose: define deterministic lowering from HPL IR terms to OpenQASM.

## Subset mapping (bootstrap)
- Any term with cls=U maps to a parameterized rotation on q[0], angle = coefficient
  Example: coefficient ? -> `ry(?) q[0];`

- Any term with cls=M maps to measurement:
  `measure q[0] -> c[0];`

**Constraint:** This is intentionally minimal; expand once operator library is defined.
