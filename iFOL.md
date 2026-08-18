# Implementation Plan: Intuitionistic First-Order Logic (iFOL / IQC) for `logic-prover`

## Goal

Extend the `constructive/` subsystem from IPC (propositional intuitionistic logic) to
IQC (intuitionistic first-order logic, a.k.a. iFOL), and expose it to users through the
Python API and the CLI.

## Current gaps (verified in code)

- `constructive/common.py:50` — `_is_atomic` treats `Forall`/`Exists` as atomic (they are
  not in the `Not/And/Or/Implies/Iff` exclusion tuple), so quantified formulas are handled
  as if they were atoms everywhere.
- `constructive/common.py:76` — `normalize_formula` recurses only into propositional
  connectives; `_formula_weight` (`:115`) has no quantifier case.
- `constructive/matrix.py:400` — `_decompose` falls through to `ATOM` for `Forall`/`Exists`.
- `constructive/resolution.py:937` — `translate_ipc_to_fol` falls through (`return formula`)
  for quantifiers.
- `constructive/kripke.py:255` — `evaluate` has no `Forall`/`Exists` cases and no per-world
  domains.
- `constructive/tableau.py:748` — `_expand_branch` has no quantifier rules; `_BranchState`
  has no domain store.
- `constructive/ljt.py:352` — `_search` has no quantifier rules.
- `__main__.py` — the CLI never wires in any constructive prover; they are Python-API-only.

Already available (no work needed):
- The parser (`core/parser.py:351`) already parses `forall`/`exists`.
- `core/substitutions.py` already provides capture-avoiding `substitute_formula`.
- The classical FOL engine already proves first-order goals.

---

## Phase 0 — Shared prerequisite fixes (`constructive/common.py`)

1. `_is_atomic`: return `False` for `Forall`/`Exists` (import them in `common.py`).
2. `normalize_formula`: recurse into `Forall.body`/`Exists.body` (keep the quantifier node).
3. `_formula_weight`: define `w(forall x. A) = w(exists x. A) = 1 + w(A)`.
4. Add a `ground_terms(signature, variables, depth)` helper to enumerate ground terms
   (constants + function symbols applied recursively, bounded depth) for instantiation
   rules, and a `fresh_variable`/`fresh_constant` helper using existing `Variable`/`Constant`
   nodes.

Each new/edited function needs a docstring per AGENTS.md rule 6 (short explanation, args
with types/defaults, return type, example).

---

## Phase 1 — LJT for IQC (`constructive/ljt.py`)

Extend `LJTProver._search` with the four quantifier rules (Dyckhoff's calculus has a
published first-order-complete variant):

- `R_Forall` (eigenvariable): `Gamma => forall x. A(x)` reduces to `Gamma => A(c)` with `c`
  fresh (not in `free_variables(Gamma)`).
- `L_Exists` (eigenvariable): `exists x. A(x), Gamma => C` reduces to `A(c), Gamma => C`
  with `c` fresh.
- `L_Forall`: `forall x. A(x), Gamma => C` reduces to `A(t), forall x. A(x), Gamma => C`
  for a candidate ground term `t` (the universal is kept for reuse; backtrack over
  `ground_terms`).
- `R_Exists`: `Gamma => exists x. A(x)` reduces to `Gamma => A(t)` for a candidate `t`
  (backtrack).

Rule names are recorded via the existing `rule` field; `LJTProofTree.is_valid` axiom set is
unchanged. Add a constructor param such as `max_term_depth` for term enumeration. This is
the highest-value, lowest-risk addition.

---

## Phase 2 — First-order Kripke semantics (`constructive/kripke.py`)

- Add `domains: Dict[World, Set[Term]]` to `KripkeModel`; add
  `add_domain_element(world, term)`; enforce domain monotonicity in
  `_enforce_monotonicity` (`w <= w'` implies `D(w) subset D(w')`).
- Extend `evaluate`:
  - `w |= forall x. A` iff for all `w' >= w` and all `t in D(w')`, `w' |= A[t/x]`.
  - `w |= exists x. A` iff exists `t in D(w)`, `w |= A[t/x]`.
- Update `to_dict`/`to_string` to show domains. Depends on Phase 0 (quantifiers must not
  be treated as atoms).

---

## Phase 3 — Tableau for IQC (`constructive/tableau.py`)

- Add `domains: Dict[World, Set[Term]]` to `_BranchState` (with `copy()` and propagation
  along relations, like T-formulas).
- Add rules in `_expand_branch`:
  - `F_Forall`: creates a fresh domain element `a` and `F(A[a/x], w)`.
  - `T_Exists`: creates a fresh domain element `a` and `T(A[a/x], w)`.
  - `T_Forall` / `F_Exists`: instantiate with each existing domain element (branching per
    term; mark applied with `(formula, world, term)` in `applied_rules`).
- `_extract_countermodel` must populate `KripkeModel.domains`.
- New constructor params: `max_term_depth` for the `T_Exists`/`F_Forall` term search when
  the "instantiate with existing term" fallback is needed.

---

## Phase 4 — First-order relational translation (`constructive/resolution.py`)

Cheapest route to full IQC since it reuses the classical FOL engine. In
`translate_ipc_to_fol` add:

- `tau(forall x. A, w) = forall w'. (R(w, w') => forall x. tau(A, w'))`
- `tau(exists x. A, w) = exists x. tau(A, w)`
- Recurse into `Forall`/`Exists`, ensuring world-variable IDs do not collide with
  individual variables (reuse the existing `var_counter`).

Update `get_frame_axioms` to accept predicate *arities* (it currently hard-codes unary
`P(x)` at `:983`) and emit monotonicity for arbitrary arity `P'(w, x1..xn)`. Update
`TranslationResolutionProver.prove` to register predicates with the correct arity.

---

## Phase 5 — Wallen matrix + prefixed resolution for IQC

Deepest change; do last.

- `constructive/matrix.py`: handle `Forall`/`Exists` in `_decompose`. Quantifiers introduce
  individual binders alongside world prefixes — add `term_vars`/`term_consts` to `Position`
  and a new `PositionType` (e.g. `DELTA`/`GAMMA`). Rework `get_paths` for these nodes.
- `constructive/prefix.py` + `constructive/resolution.py`: connections must unify *both*
  the prefix (world) and the atom terms. Compose `unify_prefixes` with `unify_terms` (from
  `core/substitutions.py`) and extend `is_admissible` cycle checks to the combined
  prefix + term substitution.
- Extend `clausify_prefixed`/`resolve_prefixed_clauses`/`factor_prefixed_clause` signatures
  accordingly.

---

## Phase 6 — Wiring and CLI

- `config.py`: add `constructive_method: str = "ljt"` and `iqc_max_term_depth: int = 2` to
  `SolverConfig`.
- `__main__.py`: add a subcommand (e.g. `prove-intuitionistic --method ljt|tableau|wallen|translation`)
  that parses the (already quantifier-capable) formula with `get_combined_signature()`, runs
  the selected prover, and prints the result via the existing `to_string()`/`to_ascii()`.
- `constructive/__init__.py`: export any new API functions.
- Update the README architecture section text if a new module is added (no doc
  regeneration, per AGENTS.md rule 1).

---

## Phase 7 — Tests

Follow existing conventions (`unittest`, e.g. `tests/test_ljt.py`). New tests:

- IQC-valid: `forall x. P(x) => exists x. P(x)` (with a non-empty domain),
  `(forall x. (P(x) => Q(x))) => ((forall x. P(x)) => (forall x. Q(x)))`,
  `exists x. forall y. R(x, y) => forall y. exists x. R(x, y)`,
  distributivity `forall x. (A & B(x)) <=> (A & forall x. B(x))` when `x` is not free in `A`.
- IQC-invalid: Markov's principle, first-order excluded middle,
  `forall x. P(x) => exists x. P(x)` without a domain element.
- Kripke `evaluate` unit tests over quantified formulas; translation-path equivalence tests
  vs. LJT/tableau.

Run `pytest` only after changes (AGENTS.md rule 4); if a test fails after an
implementation change, fix the implementation, not the test (AGENTS.md rule 5).

---

## Suggested sequencing

1. Phase 0 — unblocks everything and is a pure correctness fix.
2. Phase 4 (translation) — full IQC soundness via the classical engine.
3. Phase 1 (LJT) and Phase 2+3 (Kripke/tableau) — native IQC + countermodels.
4. Phase 5 (Wallen/prefixed resolution) — highest complexity, lowest priority.
5. Phase 6 + 7 — usability and regression safety.