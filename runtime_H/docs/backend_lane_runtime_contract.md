# Backend Lane Runtime Contract (v2.4)

## RC1 - Lane Declaration
Runtime MUST load a backend lane registry before lowering or execution.

## RC2 - Anchor Verification Gate
Runtime MUST refuse execution if epoch anchor verification fails.

## RC3 - Scheduler Sovereignty
Lowering and execution MUST occur only under scheduler authorization.

## RC4 - Evidence Emission
Runtime MUST emit evidence records for lane selection and lowering decisions.
