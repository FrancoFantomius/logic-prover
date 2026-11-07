# Implementation Plan: Intuitionistic Type Theory / Dependent Types for `logic-prover`

## Goal

Close gap #6 of `plans/missing.md`: add an intuitionistic type-theory layer — a Martin-Löf
style dependent type theory (Pi/Sigma types, universes) bridging toward a minimal Calculus of
Constructions — complementary to the classical second-order `sol` module. The result lets the
`constructive/` subsystem express and check dependent judgments, type-check the Curry-Howard
terms from `plans/proof-terms.md`, and (optionally) move toward identity types / HoTT-lite.

## Current gaps (verified in code)

- `sol/ast_ext.py:15`–`:88` — second-order machinery only: `PredicateVariable`,
  `FunctionVariable`, `ForallPred`, `ExistsPred`, `ForallFunc`, `ExistsFunc`. There are no
  dependent types, no `Pi`/`Sigma` types, no lambda abstraction over terms/types, no universes.
- `sol/` is explicitly classical (`plans/missing.md` states it is "not constructive").
- `core/ast.py` — no `Lambda`, `Pi`, `Sigma`, `Universe`, `Id` nodes; `core/visitors.py` and
  `core/substitutions.py` therefore cannot traverse dependent terms.
- No type checker: nothing in the codebase implements `infer_type`/`check` or
  beta-normalization over terms (only `ho_pattern_unify`/`beta_reduce_*` in
  `sol/substitutions_ext.py`, which operate on second-order predicates, not on lambda terms).
- `exporters/lean_exporter.py` — emits Lean *theorems* from `ProofDAG`s, but there is no
  dependent-term printer, so no dependent output is possible.
- `constructive/` (per `plans/missing.md`) is propositional/first-order only.

Already available (no work needed):
- `core/sorts.py` — `FunctionSort`, `ParameterizedSort`, `Ind`/`Nat`/`Bool` and the
  `is_compatible`/`sort_of_term` machinery that can be lifted to a small type system.
- `sol/substitutions_ext.py` — `ho_pattern_unify` and `beta_reduce_predicate/function` as
  reference implementations for the normalization engine.
- `core/visitors.py:252` — `ASTTransformer` pattern to replicate for the new nodes.
- `plans/proof-terms.md` — its `ProofTerm`/`infer_type` design is the direct precursor; this
  plan generalizes it to dependent types.
- `exporters/lean_exporter.py` — a target printer to extend.

---

## Phase 0 — Dependent term AST (`constructive/tt.py`)

New module (or `constructive/tt/` package) defining the core syntax as frozen dataclasses:

- Contexts: `Context` as a list of `(name, type)` bindings (a telescope).
- Types: `TypeVar(name)`, `Universe(level: int)` (predicative, `U_i : U_{i+1}`),
  `PiType(var, domain, codomain)`, `SigmaType(var, domain, codomain)`,
  `IdType(domain, left, right)` (Phase 3).
- Terms: `Var(name)`, `Lambda(var, body)`, `App(fun, arg)`, `Pair(l, r)`,
  `Proj(t, i)`, `Refl`, `J(...)` (Phase 3).
- Conversion: `beta_normalize(term)` (call-by-name, capture-avoiding substitution reused from
  `core/substitutions.py`), `convertible(t1, t2)`.
- `infer_type(term, ctx) -> Type` and `check(term, type, ctx) -> None`: bidirectional
  type checker with universe cumulativity and the substitution rule for `Pi`/`Sigma`.

Every function needs a docstring per AGENTS.md rule 6 (short explanation, args with
types/defaults, return type, example).

---

## Phase 1 — Curry-Howard bridge (`constructive/tt.py` + `plans/proof-terms.md`)

- Translate the simply-typed `ProofTerm` AST from `plans/proof-terms.md` into `tt` terms:
  `ArrowType` → `PiType`, `ProdType` → `SigmaType`, `SumType` → `Pi` over a boolean, etc.
- Provide `check_proof_term(term, formula_type)` that type-checks any extracted LJT/tableau
  term inside the dependent type system (a stronger guarantee than the simply-typed checker).
- Encode IPC/iFOL formula types as `Pi`-types over the proposition universe so existing
  provers' outputs plug in without changes.

---

## Phase 2 — Dependent quantifiers and context support

- Extend the `constructive/` iFOL prover (from `iFOL.md`) to keep first-class contexts
  (telescopes) alongside the sequent `Gamma => G`, so dependent judgments
  `Gamma |- A : type` and `Gamma |- t : A` can be stated, not just formula sequents.
- Add `Pi`/`Sigma` inference rules to `IKProver`-style ND or to the LJT extension:
  - `R_Pi`: `Gamma, x : A |- B(x)` implies `Gamma |- Pi x : A. B`;
  - `L_Pi` (application), `R_Sigma` (pairing), `L_Sigma` (projection).
- Scope note: full automation of dependent proof search is out of reach; this phase only wires
  the rules and the checker. Mark explicit automation as future work.

---

## Phase 3 — Identity types / HoTT-lite (optional)

- Add `IdType(A, a, b)` and the `J` eliminator with its computation rule.
- Add `path induction` tests (reflexivity, transport `subst`), keeping the scope deliberately
  narrow ("HoTT-lite": identity types + transport, no univalence axiom).

---

## Phase 4 — Lean export (`exporters/lean_exporter.py`)

- Add `export_term(term, name, type, ctx)` producing Lean 4 `def`/`theorem` declarations with
  the dependent term as body, mirroring the existing `LeanExporter` pipeline.
- Emit universe/lambda syntax compatible with Lean 4 (`Π`, `λ`, `∑`, `=`, `∀`).

---

## Phase 5 — Tests and wiring

- `config.py`: add `tt_universe_level: int = 1` to `SolverConfig`.
- `__main__.py`: add a `check-type` subcommand that reads `ctx` + `term : type` and runs
  `infer_type`/`check`; wire `--extract-term --term-format lean` to the new printer.
- `constructive/__init__.py`: export `Universe`, `PiType`, `SigmaType`, `infer_type`,
  `beta_normalize`, `check_proof_term`.
- Tests in `tests/test_tt.py`:
  - Type checking: `Lambda("x", Var("x")) : PiType(A, A)`, the Curry-Howard encoding of
    modus ponens `(A -> B) -> A -> B`, and every `extract_ljt_term` output from the
    proof-terms tests re-checked in `tt`.
  - Rejection: untyped applications, universe violations (`Universe(0) : Universe(0)`),
    ill-formed `J`.
  - Normalization: `beta_normalize` of a Church numeral application reduces to a numeral.
  - HoTT-lite: `Refl` inhabits `IdType(A, a, a)`; transport along a path.

Run `pytest` only after changes (AGENTS.md rule 4); fix the implementation, never the test
(AGENTS.md rule 5).

---

## Suggested sequencing

1. Phase 0 — AST + checker + normalizer; self-contained, no dependencies.
2. Phase 1 — bridge to `plans/proof-terms.md` (needs that plan's Phase 0 done).
3. Phase 4 — Lean printer; makes the layer usable end-to-end.
4. Phase 5 — tests/wiring.
5. Phase 2 and Phase 3 — exploratory; dependent proof automation and HoTT-lite are
   research-phase work with the highest complexity and lowest priority.