# Implementation Plan: Intuitionistic Modal Logic (IK) for `logic-prover`

## Goal

Close gap #5 of `plans/missing.md`: add intuitionistic modal logic (IK, the constructive
analogue of normal modal logic) to the `constructive/` subsystem — modal AST nodes, parser
support, bi-relational Kripke semantics, a labelled tableau, a sequent calculus, and a
relational FOL translation — alongside the existing classical S4 machinery.

## Current gaps (verified in code)

- `core/ast.py` — no `Box`/`Diamond` formula nodes; the only modal structure is the *classical*
  S4 translation inside `constructive/resolution.py:856` (`translate_ipc_to_fol`), which
  encodes Kripke worlds as `R(w, w')` in FOL, never as modal operators to reason with.
- `core/parser.py:24` — `TokenType` has no `BOX`/`DIAMOND`; no `box`/`diamond`/`□`/`◇` tokens.
- `constructive/kripke.py:71` — `KripkeModel` has a single preorder `<=` (the intuitionistic
  accessibility relation); IK requires *two* relations (`<=` and the modal `R`) satisfying a
  commutation condition.
- `constructive/kripke.py:255` — `evaluate` has no `Box`/`Diamond` cases.
- `constructive/tableau.py:448` — `_BranchState` tracks one relation (`relations`); no second
  accessibility relation or `T_Box`/`F_Box`/`T_Diamond`/`F_Diamond` rules in `_expand_branch`
  (`:748`).
- `constructive/ljt.py:352` — `_search` is propositional intuitionistic only.
- Consequence (per `plans/missing.md`): no intuitionistic modal calculus (IK) exists at all;
  the only modal work is the classical S4 embedding used for IPC.

Already available (no work needed):
- `constructive/kripke.py` — frames/worlds and monotone valuations to extend.
- `constructive/tableau.py` — labelled-tableau engine to extend with a second relation.
- `constructive/resolution.py` — the translation + frame-axiom infrastructure to mirror.
- `core/visitors.py` — visitor/transformer infrastructure that must learn the new nodes
  (same pattern used when `Forall`/`Exists` were added).
- `core/sorts.py` — no new sorts needed; modal operators are formula-to-formula.

---

## Phase 0 — Modal AST nodes (`core/ast.py` + `core/visitors.py`)

1. Add `Box(operand: Formula)` and `Diamond(operand: Formula)` frozen dataclasses to
   `core/ast.py` (pattern: mirror `Not`).
2. Update `free_variables`, `bound_variables`, `formula_depth`, `formula_size`,
   `canonicalize_bound_variables` for the two new nodes (all recurse into `operand`).
3. Update `core/visitors.py` dispatch table plus `ASTTransformer`, `DepthVisitor`,
   `SizeVisitor`, `FreeVariableCollector`, and `ExportVisitor` (`box`/`diamond`, `[]A`/`<>A`,
   `\Box`/`\Diamond` in latex).
4. Update `core/equality.py` `equality_substitution` (`:187`) to recurse into `Box`/`Diamond`
   operands (needed by `plans/equality.md` substitution over modal formulas).
5. Update `sol/ast_ext.py` `free_predicate_variables`/`free_function_variables` etc. so modal
   nodes are transparent to the SOL visitors (`core/visitors.py` already imports SOL nodes).

New nodes must have docstrings per AGENTS.md rule 6.

---

## Phase 1 — Parser support (`core/parser.py`)

- Add `TokenType.BOX`, `TokenType.DIAMOND` and token patterns `□|box` and `◇|diamond`.
- Add precedence and unary parsing (same precedence as `~`); `to_string`/`ExportVisitor`
  already emits `[]A`/`<>A` forms.
- Modal operators are signature-independent (they map any formula to a formula), so no
  `Signature` changes are required.

---

## Phase 2 — IK Kripke semantics (`constructive/kripke.py`)

- Add `modal_relations: Dict[World, Set[World]]` to `KripkeModel` (the accessibility relation
  `R`, reflexive-transitive too), with `add_modal_relation(source, target)`.
- Enforce the IK *commutation* condition: if `w <= w'` and `w R v` then there exists `v'` with
  `w' R v'` and `v <= v'` (add `_enforce_commutation()` called after every relation change).
- Extend `evaluate`:
  - `w |= []A` iff for all `v` with `w R v`, `v |= A`;
  - `w |= <>A` iff there exists `v` with `w R v` and `v |= A`
    (constructive `<>A` is *not* `~[]~A`).
- Update `to_dict`/`to_string` to render `modal_relations`.

---

## Phase 3 — Labelled tableau for IK (`constructive/tableau.py`)

- Add `modal_relations: Dict[World, Set[World]]` to `_BranchState` (with `copy()` and
  T-formula propagation like the intuitionistic relation).
- Add rules in `_expand_branch`:
  - `T_Box`: `T([]A, w)` yields `T(A, v)` for every fresh `v` with `w R v`;
  - `F_Box`: `F([]A, w)` creates a fresh `v` with `w R v` and `F(A, v)`;
  - `T_Diamond`: `T(<>A, w)` creates a fresh `v` with `w R v` and `T(A, v)`;
  - `F_Diamond`: `F(<>A, w)` yields `F(A, v)` for all `v` reachable by `R`;
  - `Commutation`: when `w <= w'` and `w R v`, assert `w' R v'` and `v <= v'` for a fresh `v'`.
- `_extract_countermodel` populates both `relations` and `modal_relations`.
- New constructor param `max_modal_depth` bounding R-chain length.

---

## Phase 4 — Sequent calculus for IK (`constructive/ljt.py` or `constructive/ik.py`)

IK has a terminating G3-style calculus (Simpson's IK, Nerode's rules):

- Add `R_Box`: `[]Gamma => A` implies `Gamma => []A` (where `[]Gamma` lifts the modal relation);
- `L_Box`: `[]A, []Gamma => A` implies `[]A, []Gamma => C`;
- `R_Diamond`: `Gamma => <>A` from `Gamma => A`;
- `L_Diamond`: `A, Gamma => C` implies `<>A, Gamma => C`.
- Best kept in a new `constructive/ik.py` (a `IKProver`) rather than overloading
  `LJTProver._search`, to avoid destabilizing the decidable IPC/`iFOL` core.
- `R_Box`/`L_Box`/`R_Diamond`/`L_Diamond` must be tracked in the proof-tree `is_valid` logic.

---

## Phase 5 — Relational FOL translation (`constructive/resolution.py`)

- Add `translate_ik_to_fol(formula, world_term, var_counter, ...)` encoding both relations:
  - `tau([]A, w) = forall w'. (R(w, w') => tau(A, w'))`,
  - `tau(<>A, w) = exists w'. (R(w, w') & tau(A, w'))`,
  - reuse the `=`/`&`/`|`/`=>` cases of `translate_ipc_to_fol`.
- Add `get_ik_frame_axioms`: reflexivity/transitivity of `R` *and* of `<=`, plus the
  commutation axiom `forall w w' v. ((<= (w,w') & R(w,v)) => exists v'. (R(w',v') & <= (v,v')))`.
- Reuse `TheoremProver` for the classical refutation, mirroring `TranslationResolutionProver`.

---

## Phase 6 — Wiring, CLI, tests

- `config.py`: add `ik_max_modal_depth: int = 3` to `SolverConfig`.
- `__main__.py`: extend the `prove-intuitionistic --method` subcommand with `ik-ljt`,
  `ik-tableau`, `ik-translation`.
- `constructive/__init__.py`: export `IKProver`, `translate_ik_to_fol`, `get_ik_frame_axioms`,
  and the extended `KripkeModel`/`TableauProver`.
- Tests in `tests/test_ik.py`:
  - Valid: `[]A & []B => [](A & B)`, `<>(A | B) => <>A | <>B`, `[](A => B) => ([]A => []B)`,
    `A => <>A`.
  - Invalid: `<>A => []A`, `[]A | <>~A` (constructive excluded-middle flavour),
    `<>(A & B) => <>A & <>B` is valid but the converse `<>A & <>B => <>(A & B)` is *not*
    (world mismatch — good commutation regression test).
  - Kripke `evaluate` unit tests over `Box`/`Diamond`; cross-prover agreement
    (LJT/tableau/translation).

Run `pytest` only after changes (AGENTS.md rule 4); fix the implementation, never the test
(AGENTS.md rule 5).

---

## Suggested sequencing

1. Phase 0 + 1 — AST + parser; touches many shared files, do first and update all visitors.
2. Phase 2 — semantics; enables model-based testing.
3. Phase 3 — labelled tableau; highest-value new prover.
4. Phase 4 — sequent calculus (new module, low risk to the existing core).
5. Phase 5 — translation (mirrors existing IPC translation).
6. Phase 6 — CLI and regression tests.