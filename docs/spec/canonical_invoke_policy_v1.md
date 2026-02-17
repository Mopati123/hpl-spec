# Canonical Invoke Policy v1

This policy defines deterministic, allowlist-gated canonical operator invocation inside
`src/hpl/runtime`.

## Scope

- Operator IDs: `CANONICAL_EQ09`, `CANONICAL_EQ15`
- Invocation gate: `execution_token.operator_policy.operator_allowlist`
- Runtime effects: `CANONICAL_INVOKE_EQ09`, `CANONICAL_INVOKE_EQ15`

## Rules

1. Invocation is denied unless the operator is present in `operator_allowlist`.
2. Canonical operators must be deterministic for identical input payloads.
3. Invocation outputs are emitted as evidence artifacts and hashed into transcript state.
4. Canonical artifacts are surfaced in bundle manifests via `canonical_invoke_v1`.

## Expected Artifacts

- `canonical_eq09_report.json`
- `canonical_eq15_report.json`
- `admissibility_certificate.json` (from EQ15)
- `delta_s_report.json` with:
  - `canonical_contribution` (canonical name)
  - `delta_s_canonical` (compatibility alias; equal value)

## Determinism

- Canonical JSON serialization (`sort_keys=True`, compact separators)
- No time-dependent fields
- No random seeds or external IO dependencies
