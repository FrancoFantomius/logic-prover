# Implementation Plan: Intuitionistic First-Order Logic with Equality (iFOL=) for `logic-prover`

## Goal

Extend the `constructive/` subsystem to reason about `Equality` (`t1 = t2`) constructively:
reflexivity, symmetry, transitivity, congruence, and substitution — for every prover
(LJT, Kripke, tableau, prefixed resolution, relational translation). This closes gap #2 of
`plans/missing.md` and is a prerequisite for the Heyting arithmetic plan
(`plans/heyting-arithmetic.md`).

## Current gaps (verified in code)

- `constructive/common.py:50` — `_is_atomic` returns `True` for `Equality` because `Equality`
  is not in the `(Not, And, Or, Implies, Iff)` exclusion tuple. `=` is therefore treated as an
  uninterpreted atom everywhere.
- `constructive/ljt.py:352` — `_search` has no `L_Refl` / `R_Refl` / substitution / congruence
  rules, so `Gamma => t = t` and `x = y => f(x) = f(y)` are not provable.
- `constructive/kripke.py:255` — `evaluate` has no `Equality` case; an equality can only be
  forced if it was added by hand to `valuations`, never via reflexivity or congruence closure.
- `constructive/tableau.py:448` — `_BranchState` has no equality store; `_expand_branch`
  (`:748`) has no `T_Refl` / substitution / closure rules.
- `constructive/resolution.py:512` — `resolve_prefixed_clauses` only requires `l1.atom == l2.atom`
  and unifies *prefixes*; it never unifies the *terms* inside atoms, so two equational literals
  with distinct-but-unifiable terms never connect. `factor_prefixed_clause` (`:567`) has the
  same limitation.
- `constructive/prefix.py` — unification operates on world prefixes only; no term unification.
- Consequence (stated in `plans/missing.md`): the group law
  `op(inv(a), op(a, b)) = b` cannot be proved, even though it is intuitionistically valid
  in iFOL with equality.

Already available (no work needed):
- `core/equality.py:15` — `CongruenceClosure`: union-find over terms, congruence propagation
  through `FunctionApp`, and `explain` (`:154`) returning a chain of `Equality` steps.
- `core/equality.py:187` — `equality_substitution`: generates all formulas obtained by
  replacing occurrences of `eq.left` with `eq.right` (and vice versa), recursing through
  `Forall`/`Exists` too.
- `core/substitutions.py:347` — `unify_terms`, `:444` `unify_formulas`, `substitute_formula`
  (`:280`) with capture avoidance.
- `prover/rules.py:215` — classical `Paramodulation` inference rule and `prover/engine.py:182`
  reflexivity clause, proving the classical engine already handles equality.
- `axioms/equality.py:34` — the six equality axioms (reflexive, symmetric, transitive,
  unary/binary function congruence, predicate congruence).
- `core/ast.py:135` — `Equality` node; `free_variables`/`bound_variables` handle it correctly.

---

## Phase 0 — Shared helpers (`constructive/common.py`)

1. Keep `Equality` atomic in `_is_atomic` (it *is* an atom; the missing piece is how atoms
   are compared/closed, not their atomicity). Document this explicitly in the docstring.
2. Add `collect_equalities(formula, world=None)` → `Set[Equality]` gathering positive equality
   subformulas (useful for the tableau and resolution closure).
3. Add `congruence_closure(terms: Iterable[Term]) -> CongruenceClosure` a thin wrapper around
   `core.equality.CongruenceClosure` that registers all subterms.
4. Add `ground_terms(signature, variables, depth)` (already planned by `iFOL.md` Phase 0) so
   instantiation rules can enumerate `Constant`/`FunctionApp` candidates for substitution.

Each new/edited function needs a docstring per AGENTS.md rule 6 (short explanation, args with
types/defaults, return type, example).

---

## Phase 1 — LJT with equality (`constructive/ljt.py`)

Add rules to `LJTProver._search` (Dyckhoff's calculus extended with equality, a terminating
variant exists for iFOL=):

- `R_Refl`: `Gamma => t = t` closes immediately (axiom-like leaf).
- `L_Refl`: `t = t, Gamma => C` reduces to `Gamma => C` (delete reflexivity).
- `L_Eq_Subst`: from `s = t, Gamma => C`, pick any antecedent or succedent formula containing
  `s` or `t` and replace one occurrence via `equality_substitution` (`core/equality.py:187`),
  reducing to `s = t, Gamma' => C'`. Add a weight bound (`eq_subst_max`, default e.g. 5) so
  the search stays terminating — this rule reintroduces non-termination risk if unrestricted.
- Record rule names in the existing `rule` field; keep `LJTProofTree.is_valid`'s axiom set
  unchanged (`{"Ax", "L_Bot", "R_Top"}` must grow to include `R_Refl`).

Optional strengthening: orient equalities as rewrite rules with a term ordering so
`L_Eq_Subst` only rewrites in one direction (KBO/lexicographic on term structure) — this keeps
the calculus confluent and is the safest way to keep termination.

---

## Phase 2 — First-order Kripke semantics with equality (`constructive/kripke.py`)

- Add `equalities: Dict[World, Set[Equality]]` to `KripkeModel` (world-relative equality,
  monotone like valuations: `w <= w'` implies `E(w) subset E(w')`), with
  `add_equality(world, eq)` and propagation in `_enforce_monotonicity`.
- Extend `evaluate`:
  - `w |= t1 = t2` iff `t1` and `t2` are in the same congruence class of
    `congruence_closure(E(w))` — i.e. reflexivity/congruence hold automatically and
    `add_equality` supplies the non-trivial identities.
  - `Equality` must be evaluated *before* the `_is_atomic` branch.
- Update `to_dict`/`to_string` to render `equalities` per world.

---

## Phase 3 — Tableau with equality (`constructive/tableau.py`)

- Add `equalities: Dict[World, Set[Equality]]` to `_BranchState` (with `copy()` and
  propagation along relations, mirroring `t_formulas`).
- Add rules in `_expand_branch`:
  - `T_Refl`: branch with `T(t = t, w)` is closed.
  - `T_Eq_Subst`: from `T(s = t, w)` and a formula `F` at `w` containing `s`/`t`, branch on the
    substituted variants from `equality_substitution`.
  - Closure: when `T(s = t, w)` and `T(t = u, w)` are both present, add `T(s = u, w)` via the
    congruence-closure store (transitivity is then automatic).
- `_extract_countermodel` must populate `KripkeModel.equalities`.
- New constructor param `eq_subst_max` for the substitution branching limit.

---

## Phase 4 — Prefixed resolution with term unification (`constructive/resolution.py`)

- `resolve_prefixed_clauses` / `factor_prefixed_clause`: in addition to `l1.atom == l2.atom`,
  allow `unify_formulas(l1.atom, l2.atom)` (`core/substitutions.py:444`). Compose the prefix
  substitution with the term substitution; apply both to the resolvent.
- The `_backtrack` "closed under current substitution" check in `PrefixedResolutionProver`
  (`:756`) must also use `unify_formulas` (not plain `==`) and treat two complementary
  equational literals as closed when their terms unify.
- Add a positive-equality closure: from unit clauses `s = t` and `t = u`, derive `s = u`
  (transitivity), and from `s = t` plus any clause containing `s`, derive the clause with
  `t` substituted (paramodulation, reusing the classical rule's helpers in `prover/rules.py`).
- `clausify_prefixed` / `constructive/matrix.py` need no change for equality — `Equality` is
  already atomic; only the connection phase must become term-aware.

---

## Phase 5 — Relational translation with equality (`constructive/resolution.py`)

The translation already handles equality correctly: `translate_ipc_to_fol` returns the
`Equality` node unchanged (`:901`–`903`), which is the right semantics (rigid, world-independent
equality). Remaining work:

- Ensure `get_frame_axioms`/`_extract_predicate_names` never emit monotonicity axioms for `=`
  (it is not a predicate symbol, so no change needed — add a regression test).
- Run the classical FOL engine's built-in superposition (`prover/engine.py`) so the translated
  goal benefits from equality reasoning for free.

---

## Phase 6 — Wiring and tests

- `config.py`: add `iqc_eq_subst_max: int = 5` to `SolverConfig`.
- `constructive/__init__.py`: export new helpers/provers.
- Tests (unittest, mirroring `tests/test_ljt.py` / `tests/test_equality.py`):
  - Valid: `op(inv(a), op(a, b)) = b` from the group axioms
    (`axioms/group_theory.py:49`), `x = y => f(x) = f(y)`, `x = y & y = z => x = z`,
    `(x = y & P(x)) => P(y)`.
  - Invalid: `forall x y. x = y` (two distinct domain elements), `a = b` with an empty
    equality store, and the constructive non-theorem `(a = b => _bot) | a = b`.
  - Equivalence: every prover (LJT / tableau / prefixed / translation) agrees on the valid
    set; Kripke `evaluate` unit tests over equalities.

Run `pytest` only after changes (AGENTS.md rule 4); if a test fails after an implementation
change, fix the implementation, not the test (AGENTS.md rule 5).

---

## Suggested sequencing

1. Phase 0 — unblocks all provers; pure helper work.
2. Phase 1 (LJT) and Phase 2 (Kripke) — native iFOL= with semantics.
3. Phase 3 (tableau) and Phase 4 (prefixed resolution) — countermodels and the direct
   connection method.
4. Phase 5 (translation) — nearly free given the classical engine's superposition.
5. Phase 6 — regression safety and the group-law showcase test.