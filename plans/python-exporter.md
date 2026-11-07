# Implementation Plan: Python Code Generation from Proof Terms for `logic-prover`

## Goal

Provide a code generation pipeline that translates constructive proofs and proof terms
(`ProofTerm` from `plans/proof-terms.md`) into executable, idiomatic, and type-annotated
**Python code**. 

Under the Curry–Howard correspondence (BHK interpretation), a constructive proof of a
specification formula is a functional program. For instance:
- A proof of `A => B` is a Python function `Callable[[A], B]`.
- A proof of `forall x. exists y. P(x, y)` yields a computable function `def f(x) -> y`.
- A proof of `A & B` yields a tuple `(a, b)`.
- A proof of `A | B` yields a tagged union / branch.
- An induction proof in Heyting arithmetic yields a recursive function or loop (`NatRec`).

This plan extends the proof-term extraction architecture of `plans/proof-terms.md` with a
dedicated `PythonExporter`.

---

## Current gaps (verified in code)

- `exporters/lean_exporter.py` and `exporters/graph_exporter.py` exist, but there is no
  `exporters/python_exporter.py`.
- `plans/proof-terms.md` outlines extraction to simply-typed lambda terms and printers for
  string, LaTeX, and Lean 4, but omits a Python code generation target.
- Constructive proof derivations (`constructive/ljt.py`, `constructive/ha.py`) build
  `LJTProofNode` tree structures, but do not yet emit Python AST or source text.
- No runtime support primitives (e.g., tagged unions for disjunction `Left`/`Right`, or
  recursors for Heyting arithmetic induction).

Already available (no work needed):
- `exporters/lean_exporter.py`: existing blueprint for AST visitor, sanitization, and code
  generation pipelines.
- Python standard library `ast` module: `ast.FunctionDef`, `ast.Match`, `ast.Lambda`,
  `ast.unparse` for synthesizing clean and formatted Python source code without manual string
  concatenation.
- `logic_prover/constructive/ha.py`: constructive Heyting arithmetic solver producing constructive
  derivation trees.
- `core/substitutions.py` and `plans/proof-terms.md`: infrastructure for beta-normalization to
  simplify generated code prior to Python emission.

---

## Phase 0 — Runtime Support & Type Mapping (`exporters/python_runtime.py`)

Define lightweight runtime primitives and type translators mapping constructive logic types to
Python's `typing` system:

1. **Sum Type Primitives (Disjunction `A | B`)**:
   - Provide minimal tagged union wrappers `Left[T]` and `Right[T]` (dataclasses) or support
     standard `typing.Union`.
   - Provide a helper eliminator or support Python 3.10+ `match / case`.
2. **Type Mapping (`type_to_python_annotation`)**:
   - `ArrowType(A, B)` $\to$ `Callable[[A_py], B_py]`
   - `ProdType(A, B)` $\to$ `Tuple[A_py, B_py]`
   - `SumType(A, B)` $\to$ `Union[Left[A_py], Right[B_py]]`
   - `UnitType` $\to$ `None`
   - `VoidType` $\to$ `typing.NoReturn`
   - `Nat` (from HA) $\to$ `int`
   - `AtomType(name)` $\to$ `Any` or a generic `TypeVar`.

Every function needs a docstring per AGENTS.md rule 6.

---

## Phase 1 — Python AST Exporter (`exporters/python_exporter.py`)

Create `PythonExporter` converting `ProofTerm` (from `plans/proof-terms.md`) into Python `ast.AST`:

- `Var(name)` $\to$ `ast.Name(id=name, ctx=ast.Load())`
- `Abs(var, body)` $\to$ `ast.Lambda` for simple lambdas, or top-level `ast.FunctionDef` when
  translating named theorems, including type annotations from `infer_type`.
- `App(fn, arg)` $\to$ `ast.Call(func=fn_ast, args=[arg_ast])`
- `Pair(l, r)` $\to$ `ast.Tuple(elts=[l_ast, r_ast], ctx=ast.Load())`
- `Fst(t)` / `Snd(t)` $\to$ `ast.Subscript` accessing indices `t[0]` and `t[1]`
- `Inl(t)` / `Inr(t)` $\to$ `ast.Call(func=ast.Name(id="Left"|"Right"), args=[t_ast])`
- `Case(scrutinee, v1, left, v2, right)` $\to$ `ast.Match` statement (or `if isinstance(...)` for
  backward compatibility) inspecting whether the scrutinee is `Left` or `Right`.
- `NatRec(base, step, n)` $\to$ Iterative loop or helper recursion:
  ```python
  def _rec(k: int) -> Any:
      acc = base_val
      for i in range(k):
          acc = step_fn(i, acc)
      return acc
  ```
- `Abort(type, t)` $\to$ `ast.Raise` raising `RuntimeError("Unreachable: ex falso quodlibet")`.
- `Refl(t)` $\to$ `None` (proof irrelevance for equality).

---

## Phase 2 — Optimization & Beta-Reduction

Extracted proof terms often contain "administrative redexes" (immediate applications of lambdas
created by cuts or lemma instantiations).

- Before generating Python code, apply `beta_normalize(term)` from `plans/proof-terms.md`.
- Eliminate proof-irrelevant subterms:
  - Formulas in computationally empty sorts (`Prop` with no computational witness) can be
    erased or mapped to `None`.
  - For existential goals `exists x. P(x)`, use `extract_witness` to emit only the computational
    witness computation `x` rather than the full verification trace.

---

## Phase 3 — Module & Function Code Generation API

Provide high-level entry points in `logic_prover/exporters/python_exporter.py`:

- `export_function(term: ProofTerm, name: str, formula_type: Optional[Type] = None) -> str`:
  Generates a standalone, type-hinted Python function definition.
- `export_module(theorems: Sequence[Tuple[str, ProofTerm, Type]]) -> str`:
  Generates a complete `.py` source file including imports (`from typing import ...`),
  the runtime prelude (`Left`, `Right`), and all exported functions.
- Add docstrings to generated Python functions describing the original logical formula proved.

---

## Phase 4 — CLI and Tooling Integration

- Add `--term-format python` option to the constructive proving subcommands in `__main__.py`
  (e.g., `prove-intuitionistic`, `prove-ha`).
- Add `--output <file.py>` to dump synthesized Python programs directly to disk.
- Export `PythonExporter` and `export_function` in `logic_prover/exporters/__init__.py`.

---

## Phase 5 — Tests and Verification (`tests/test_python_exporter.py`)

Follow existing conventions (`unittest`):

1. **Syntactic & Structural Tests**:
   - Verify generated Python AST matches expected structures for identity, pairing, projection,
     and conditional branching.
   - Verify `ast.unparse()` produces syntactically valid Python that passes `compile()`.
2. **End-to-End Execution Tests**:
   - Execute generated code with `exec()` in a sandbox dict and call the generated functions:
     - Identity proof `A => A` applied to `42` returns `42`.
     - Swap proof `(A & B) => (B & A)` applied to `(1, "x")` returns `("x", 1)`.
     - Boolean disjunction resolution returns the expected branch.
     - Peano induction `forall n. 0 + n = n` executes as the identity function on `int`.
3. **Type Annotation Tests**:
   - Verify emitted annotations match `typing` expectations.

---

## Suggested Sequencing

1. Implement `plans/proof-terms.md` Phases 0, 1, and 3 (the `ProofTerm` AST and extraction from
   `LJTProver` must exist first).
2. Phase 0 & Phase 1 — `PythonExporter` translating `ProofTerm` to Python `ast.AST`.
3. Phase 2 — Normalization and proof-irrelevance erasure for clean code.
4. Phase 3 & Phase 4 — High-level module exporter and CLI flag.
5. Phase 5 — Verification tests with runtime execution.
