# Implementation Plan: Proof-Term Extraction (Curry-Howard) for `logic-prover`

## Goal

Close gap #3 of `plans/missing.md`: turn constructive proofs (LJT, tableau, Wallen, prefixed
resolution) into typed lambda terms under the Curry-Howard / BHK interpretation, extract
witnesses for `exists` and `or`, type-check the resulting terms, and print them (string /
Lean 4). This makes proofs usable as programs.

## Current gaps (verified in code)

- `constructive/ljt.py:85` — `LJTProofNode` stores only `sequent`, `rule`, `premises`; no term
  annotation is attached during `_search` (`:352`).
- `constructive/tableau.py`, `constructive/wallen.py`, `constructive/resolution.py` — proofs are
  refutation trees / DAGs, not lambda terms.
- `prover/reconstruction.py:69` — `reconstruct_proof` converts a resolution trace into a
  natural-deduction `ProofDAG`, but the root step uses `DoubleNegationElimination`
  (`:166`–`:169`), i.e. it is a *classical* reconstruction; there is no constructive term.
- `prover/proof.py:75` — `ProofDAG`/`ProofStep` carry formulas only, no terms.
- No `Or`/`Exists` witness extraction: `proof.dag` and the constructive proof trees store no
  witness terms, so the disjunctive/existential branch actually taken is not recoverable.
- `exporters/lean_exporter.py` — exports formulas/axioms to Lean 4 but has no term printer.

Already available (no work needed):
- `core/visitors.py:252` — `ASTTransformer` for building/transforming new ASTs.
- `core/substitutions.py:280` — capture-avoiding `substitute_formula` for existential
  witnesses and quantifier instantiation in terms.
- `core/parser.py` — `to_string` for formula printing (can be mirrored for terms).
- `exporters/lean_exporter.py` — a Lean output pipeline to extend.
- The LJT rules (`constructive/ljt.py`) have a well-known injective mapping to simply-typed
  lambda terms (Dyckhoff 1992): `R_Imp` → lambda, `L_Imp` → application, `R_And` → pairing,
  `R_Or1/2` → inl/inr, `L_Or` → case, `L_Bot` → `abort`.

---

## Phase 0 — Term AST and type checker (`constructive/terms.py`)

New module defining the simply-typed lambda calculus with sums, products, unit, and void:

- Types: `VarType`, `ArrowType`, `ProdType`, `SumType`, `UnitType`, `VoidType`, `AtomType`.
- Terms: `Var`, `Abs(var, body)`, `App(fun, arg)`, `Pair(l, r)`, `Fst(t)`, `Snd(t)`,
  `Inl(t)`, `Inr(t)`, `Case(scrutinee, var1, left, var2, right)`, `Unit`, `Abort(type, t)`,
  `Refl(term)`, `Subst(eq, fn)` (equality plumbing from `plans/equality.md`).
- `infer_type(term, ctx) -> Type`: bidirectional type checker raising `TypeError` on mismatch.
- `term_to_string(term)`, `term_to_latex(term)`, `term_to_lean(term)`: printers.
- `beta_normalize(term)`: call-by-name reduction with capture-avoiding substitution
  (reuse `core/substitutions.py` for the variable plumbing).

Every function needs a docstring per AGENTS.md rule 6.

---

## Phase 1 — LJT extraction (`constructive/ljt.py`)

- Add a `term: Optional["ProofTerm"]` field to `LJTProofNode` and thread it through `_search`:
  each rule constructs the corresponding lambda term from its premises' terms:
  - `R_Top` → `Unit`; `Ax` → `Var(goal)`; `L_Bot` → `Abort(VoidType, prem)`;
  - `R_Imp` → `Abs(x, t)`; `L_Imp_*` → `App(f, t)`;
  - `R_And` → `Pair(t1, t2)`; `L_And` → pair deconstruction;
  - `R_Or1/2` → `Inl`/`Inr`; `L_Or` → `Case(...)`;
  - quantifier rules from `iFOL.md` Phase 1: `R_Forall` → `Abs`, `L_Forall` → `App(t)`.
- `R_Refl` (from `plans/equality.md`) → `Refl`.
- Add `extract_ljt_term(proof: LJTProofTree) -> ProofTerm` returning `proof.root.term`, and
  `prove_ljt_checked(target, premises) -> (LJTProofTree, ProofTerm, Type)` that also runs
  `infer_type` as a sanity check.

---

## Phase 2 — Tableau / Wallen / prefixed-resolution extraction

Tableaux, Wallen matrices, and prefixed resolution are refutation methods; term extraction is
not direct. Two options (implement both, expose via one dispatcher):

1. *Translation route (recommended, cheap and correct)*: since all constructive provers prove
   the same set of theorems, re-run the goal through `LJTProver` and extract from its tree.
   Provide `extract_term(result) -> Optional[ProofTerm]` that dispatches on the result type
   (`LJTProofTree`, `TableauProofResult`, `WallenProofResult`,
   `PrefixedResolutionProofResult`) and falls back to LJT re-proving.
2. *Direct route (optional, later)*: reconstruct a constructive ND proof from a closed tableau
   branch / connection set without `DoubleNegationElimination`, then map ND to terms. This
   mirrors `prover/reconstruction.py` but stays intuitionistic.

---

## Phase 3 — Witness extraction (BHK)

- `extract_witness(term: ProofTerm, formula: Formula) -> Term`: for an `Exists(v, body)` goal
  proved by `ExistsIntro(witness, ...)`, return `witness`; for a disjunction goal proved via
  `Inl`/`Inr`, return a marker (`1`/`2`) plus the extracted sub-proof witness.
- `extract_program(proof_result, target) -> Tuple[ProofTerm, Optional[Term]]`: returns the
  term and, if the goal was existential/disjunctive, the extracted witness.
- Add a `Witness` result container (dataclass) with `to_dict()`/`to_string()` mirroring the
  other result types.

---

## Phase 4 — Wiring and CLI

- `config.py`: add `intuitionistic_extract_terms: bool = False` to `SolverConfig`.
- `__main__.py`: on the `prove-intuitionistic` subcommand (from `iFOL.md` Phase 6), add
  `--extract-term` and `--term-format {string,lean,latex}`; print the checked term and, for
  existential goals, the witness.
- `exporters/lean_exporter.py`: add `export_term(term, name, type)` emitting a Lean 4
  `def`/`theorem` with the extracted term as its body.
- `constructive/__init__.py`: export `ProofTerm`, `infer_type`, `extract_ljt_term`,
  `extract_witness`, `extract_program`.

---

## Phase 5 — Tests

Follow existing conventions (`unittest`). New tests in `tests/test_proof_terms.py`:

- Typed extraction: `(P => Q) => (P => Q)` (identity), `P => P | Q` (inr),
  `(A & B) => (B & A)` (pair swap), `P => ~~P` (double-negation introduction),
  `forall x. P(x) => exists x. P(x)` — the extracted witness must be the eigenvariable.
- Type checking: `infer_type(term)` matches the target formula's type translation for every
  extracted term; deliberately broken terms raise `TypeError`.
- Witness correctness: for `exists x. R(x)` with witness `a`, `extract_witness` returns `a`;
  for `A | B` the returned disjunct index matches the proof's branch.
- Non-extractability: a classical-only theorem (`P | ~P`) yields no constructive term.

Run `pytest` only after changes (AGENTS.md rule 4); fix the implementation, never the test
(AGENTS.md rule 5).

---

## Suggested sequencing

1. Phase 0 — term AST + checker + printers; pure, no dependency on other plans.
2. Phase 1 — LJT extraction (needs `iFOL.md` Phase 1 and `plans/equality.md` Phase 1 done).
3. Phase 3 — witness extraction on top of Phase 1.
4. Phase 2 — the LJT-translation route first, direct route later.
5. Phase 4 + 5 — usability (Lean output) and regression safety.