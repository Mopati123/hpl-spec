Deprecated reference folder.

Do not place active reference artifacts here.

Canonical Machine A reference for Track A now lives in:

- `references/phase1/navier_stokes/machine_a_f06023a/`

Reason:

- the previous folder name implied commit `d878e95...` but the embedded
  manifest contract was for `f06023a...`.
- this mismatch caused deterministic contract-check failures across machines.
