# Missing Features: Constructive Logic Area

This document lists the gaps in the `logic_prover.constructive` subsystem. The
entire module is currently limited to **intuitionistic propositional logic (IPC)**,
even though the broader library (e.g. `logic_prover.prover`, `logic_prover.axioms`)
handles full first-order and higher-order logic classically.

## 1. Intuitionistic First-Order Logic (iFOL)

- No `Forall` / `Exists` proof rules (no `R_All`, `L_All`, `R_Exists`, `L_Exists`).
- No eigenvariable handling, no Skolemization, no Herbrand expansion.
- LJT, labelled tableau, Wallen matrix, prefixed resolution, and the S4
  translation all operate on propositional formulas only.
- `Forall` and `Equality` appear only inside the S4 relational translation
  (`constructive/resolution.py`), where they are used to encode Kripke worlds,
  never as quantifiers to reason with.

## 2. Equality Reasoning

- No congruence, substitution, or transitivity rules for `=`.
- `_is_atomic` (`constructive/common.py`) classifies `Equality` and `Forall`
  nodes as atoms, so the calculus silently skips over them.
- Consequence: equational theorems (e.g. the group law
  `op(inv(a), op(a, b)) = b`) cannot be proved, even though they are
  intuitionistically valid in iFOL with equality.

## 3. Proof-Term Extraction (Curry-Howard)

- Proofs are stored as trees / DAGs, not as lambda terms or natural-deduction
  terms.
- No witness extraction for disjunction or existential formulas under the BHK
  interpretation, so a proof cannot be turned back into a program.

## 4. Intuitionistic Arithmetic

- Peano axioms exist (`axioms/peano.py`) but are only proved with the classical
  first-order resolution `TheoremProver`.
- No Heyting arithmetic (HA) prover, no constructive induction principle.

## 5. Constructive Modal Logics

- Only classical Kripke semantics for IPC and the S4 relational translation are
  implemented.
- No intuitionistic modal logics (IK), no native constructive modal calculi.

## 6. Higher-Order / Dependent Types

- No intuitionistic type theory, Calculus of Constructions, or HoTT.
- The `sol` module is classical second-order logic, not constructive.