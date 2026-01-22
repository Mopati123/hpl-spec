# Effect Types: ETO + λ (v2.3)

## Definitions
- **ETO (Effect Type Obligation):** Declares the allowed effect class for evolution.
- **λ (Lambda Effect):** Declares parameterization and allowable transforms.

## Obligations
1. Every `evolve` MUST declare an ETO and a λ.
2. ETO/λ declarations MUST be statically checkable.
3. ETO/λ mismatches MUST be rejected before execution.

## Notes
ETO + λ define legality of evolution; they do not execute evolution.
