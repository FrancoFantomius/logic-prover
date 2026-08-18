# Implementation Plan: Heyting Arithmetic (HA) for `logic-prover`

## Goal

Close gap #4 of `plans/missing.md`: add a constructive arithmetic prover for Heyting
arithmetic — iFOL with equality (from `plans/equality.md`) plus the Peano axioms and the
first-order induction schema — replacing the current classical-only treatment of
`axioms/peano.py`. Prove basic number-theoretic theorems constructively and extract their
programs (via `plans/proof-terms.md`).

## Current gaps (verified in code)

- `axioms/peano.py:40` — `get_peano_axioms` defines the seven Peano axioms, but they are only
  proved by the classical first-order `TheoremProver` (`prover/engine.py`); no constructive
  path exists.
- `axioms/peano.py:100` — `peano_le_def` uses `Exists`, so it requires the quantifier support
  of `iFOL.md`; it cannot be proved by the propositional-only `constructive/` subsystem.
- No induction: the only induction machinery is second-order `instantiate_induction` in
  `sol/kb_ext.py` (classical SOL), and it is not wired into any constructive prover.
- The constructive provers (LJT `constructive/ljt.py:352`, tableau `constructive/tableau.py:748`)
  have no `R_Ind` / induction rule.
- Consequence: `forall n. 0 + n = n` and `forall m n. m + n = n + m` are not provable
  constructively, despite being HA-theorems.

Already available (no work needed):
- `axioms/peano.py:15` — `get_peano_signature` (constants `zero`, functions `succ`/`add`/`mul`,
  predicates `le`/`lt`/`eq`, sort `Nat`).
- `axioms/equality.py:34` — the equality axioms and `core/equality.py` congruence closure
  (needed by iFOL=).
- The quantifier rules from `iFOL.md` (LJT, tableau, translation) — HA sits on top of iFOL=.
- `axioms/base.py` — `Theory`/`register_theory` infrastructure for a new `ha_theory`.
- `sol/kb_ext.py` — `instantiate_induction` shows the *form* of the schema to reuse.

---

## Phase 0 — HA theory definitions (`axioms/heyting_arithmetic.py`)

1. Add `get_ha_axioms() -> List[Tuple[str, Formula]]` returning the six equality-free Peano
   axioms (reuse `get_peano_axioms()`, dropping nothing — `peano_le_def` stays) plus the
   induction schema represented as a first-order formula per provable instance:
   `(A(0) & forall n. (A(n) => A(S(n)))) => forall n. A(n)`.
2. Add `get_ha_signature()` (reuse `get_peano_signature()`).
3. Register `ha_theory: Theory` via `register_theory`.
4. Keep `axioms/peano.py` untouched (classical path stays); HA is a separate theory.

Each function needs a docstring per AGENTS.md rule 6.

---

## Phase 1 — Induction in LJT (`constructive/ljt.py`)

Add an `R_Ind` rule to `LJTProver._search` (extending the iFOL= work of `plans/equality.md`):

- `R_Ind`: `Gamma => forall n. A(n)` reduces to two premises:
  - `Gamma => A(zero)` (base case), and
  - `Gamma, A(n) => A(S(n))` with `n` a fresh eigenvariable (step case).
- Record `rule="R_Ind"`; add `"R_Ind"` handling to `LJTProofTree.is_valid`.
- New constructor param `max_ind_depth: int = 3` bounding nested induction, since HA is
  undecidable (first-order Peano is not finitely controlled by Dyckhoff weights alone).
- Phase 0 of `plans/proof-terms.md`: the extracted term for `R_Ind` is a recursor/iterator
  `natrec(base, step, n)`; add `NatRec` to the term AST there.

---

## Phase 2 — Induction in the tableau (`constructive/tableau.py`)

- Extend `_expand_branch` with a `F_Ind` rule: to falsify `forall n. A(n)` at world `w`,
  branch on either `F(A(zero), w)` or `T(A(c), w') & F(A(S(c)), w')` for a fresh domain
  element `c` at `w' >= w`.
- Populate `KripkeModel` accordingly. Caveat (model theory): induction is *not* valid in all
  Kripke models — only in models with standard `Nat` domains — so countermodels produced for
  unprovable goals are models of iFOL= *without* induction. Document this limitation in the
  module docstring and the countermodel printer.

---

## Phase 3 — Classical translation path for HA (`constructive/resolution.py`)

- Extend `TranslationResolutionProver` (or add `HAProver`) to instantiate the induction schema
  for the target's predicate subformulas and add the six Peano axioms + equality axioms as FOL
  premises, then delegate to the classical engine's superposition loop.
- Semi-decidable: cap the number of schema instantiations (constructor param
  `max_induction_instances`, default e.g. 4) and reuse `SolverConfig` timeouts.

---

## Phase 4 — Theorem library and tests

New tests in `tests/test_heyting_arithmetic.py` (unittest, following `tests/test_ljt.py`
conventions):

- Valid (each of LJT-HA, tableau, and translation must prove):
  - `forall n. 0 + n = n` (left identity via induction),
  - `forall n. S(n) <> n` (using `peano_zero_not_succ` + `succ_injective`),
  - `forall m n. m + n = n + m` (commutativity, nested induction — the showcase theorem),
  - `forall n. n <= n` and `forall m n. (m <= n & n <= m) => m = n` via `peano_le_def`.
- Invalid / non-derivable: first-order excluded middle `forall n. (P(n) | ~P(n))`,
  Markov's principle, and unprovable-without-induction `forall n. 0 + n = n` when the
  `R_Ind` rule is disabled.
- Consistency checks: `extract_ljt_term` (from `plans/proof-terms.md`) yields a well-typed
  term for each HA proof; `forall n. 0 + n = n` extracts to a term starting with `NatRec`.

Run `pytest` only after changes (AGENTS.md rule 4); fix the implementation, never the test
(AGENTS.md rule 5).

---

## Phase 5 — Wiring and CLI

- `config.py`: add `ha_max_ind_depth: int = 3` and `ha_max_induction_instances: int = 4` to
  `SolverConfig`.
- `__main__.py`: add `--theory ha` to the `prove-intuitionistic` subcommand (from `iFOL.md`
  Phase 6) so users can prove arithmetic goals with the Peano/equality premises loaded
  automatically.
- `constructive/__init__.py`: export `HAProver`, `get_ha_axioms`, `ha_theory`.

---

## Suggested sequencing

1. Phase 0 — theory definitions; trivial, unblocks tests.
2. Phase 1 — LJT `R_Ind` (requires `iFOL.md` Phase 1 + `plans/equality.md` Phase 1).
3. Phase 4 — theorem library proves the search rules work.
4. Phase 2 — tableau with the documented non-standard-model caveat.
5. Phase 3 — translation path (semi-decidable, useful for cross-checking).
6. Phase 5 — CLI and exports last.