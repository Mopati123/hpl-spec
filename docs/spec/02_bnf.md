# HPL Grammar (BNF) ? Bootstrap Spec

## Syntax Layers

This grammar defines the **axiomatic core language** of HPL.

HPL permits additional **surface-level syntax** (e.g. `defstrategy`, `params`, `let`, `if`,
domain-specific operators such as `buy` / `sell`, and infix predicates such as `>`),
provided that:

1. Surface forms are **pure macros**.
2. Surface forms **must fully expand** into the axiomatic forms defined in this BNF.
3. No surface construct may reach IR construction or execution.
4. After macro-expansion, the program **must be expressible entirely** using this grammar.

The macro-expansion phase is therefore a **mandatory semantic boundary**.

<program> ::= <form>+

<form> ::= <definition> | <expression>

<definition> ::= (operator <symbol> <operator-body>)
               | (invariant <symbol> <predicate>)
               | (scheduler <symbol> <rules>)
               | (observer <symbol> <capabilities>)

<expression> ::= (hamiltonian <term>+)
               | (evolve <symbol> <time>)
               | (measure <target> <observable> <handler>)
               | (<symbol> <expression>*)

<term> ::= (term <operator-ref> <coefficient>)

<operator-body> ::= (? (<args>) <expression>)

<handler> ::= (? (<measurement>) <expression>)

**Constraint:** After macro-expansion, only axiomatic forms may remain.
