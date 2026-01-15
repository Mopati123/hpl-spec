# Operator Algebra (Commutation Table) ? Spec

Let [A,B] = AB - BA.

## Operator classes
- U: unitary evolution operator
- M: measurement (non-unitary collapse)
- ?: observer identity (authorization gate)
- C: control operators (scheduler, guards, invariants)
- I: I/O coupling
- A: audit operator

## Laws
1. Unitary?Unitary:
   - if [U?,U?]=0 then reorderable/parallelizable
   - else ordered (coupled)

2. Unitary?Measurement:
   - generally [U,M] ? 0 (measurement interrupts evolution)

3. Measurement?Measurement:
   - [M?,M?]=0 iff observables compatible
   - else incompatible

4. Observer?Measurement:
   - measurement is valid iff observer ? is authorized by scheduler

5. Invariant law:
   - invariants must satisfy [Inv, H] = 0
   - violation => execution invalid (halt)

**Constraint:** Provide an explicit commutation table for named operators once operator library is defined.
