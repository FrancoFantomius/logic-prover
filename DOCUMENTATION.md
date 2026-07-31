# Module Documentation Manual (`solver`)

This document contains the detailed reference guide for each module and subpackage present in the `solver` library.

---

## Table of Contents

1. [solver.formula](#1-solverformula)
2. [solver.database](#2-solverdatabase)
3. [solver.prover](#3-solverprover)
4. [solver.verifier](#4-solververifier)
5. [solver.explorer](#5-solverexplorer)
6. [solver.lean_exporter](#6-solverlean_exporter)
7. [solver.dependencies](#7-solverdependencies)
8. [solver.deducer](#8-solverdeducer)

---

## 1. `solver.formula`

The [`solver.formula`](file:///c:/Users/franc/Programmazione/solver/solver/formula.py) module defines the Abstract Syntax Tree (AST) structure for logical formulas and provides a string-to-AST parser.

### AST Classes

All formulas inherit from the abstract class `Formula`.

- **`Var(name)`**: Represents a propositional or individual variable (e.g., `Var("p")`, `Var("x")`).
- **`Not(formula)`**: Logical negation (`~A` or `Not(A)`).
- **`Implies(left, right)`**: Logical implication (`A -> B` or `A >> B`).
- **`And(left, right)`**: Logical conjunction (`A & B` or `And(A, B)`).
- **`Or(left, right)`**: Logical disjunction (`A | B` or `Or(A, B)`).
- **`Iff(left, right)`**: Double implication / Logical equivalence (`A <-> B` or `Iff(A, B)`).
- **`Forall(var, body)`**: Universal quantifier (`forall x, P(x)` or `Forall("x", P)`).
- **`Exists(var, body)`**: Existential quantifier (`exists x, P(x)` or `Exists("x", P)`).
- **`Equals(left, right)`**: Formal equality (`x = y` or `Equals("x", "y")`).
- **`Pred(name, args)`**: Predicate application (e.g., `Pred("P", [Var("x"), Var("y")])`).

### Python Operator Overloading

You can combine `Formula` instances using native Python syntax:
- `~f` $\rightarrow$ `Not(f)`
- `f1 >> f2` $\rightarrow$ `Implies(f1, f2)`
- `f1 & f2` $\rightarrow$ `And(f1, f2)`
- `f1 | f2` $\rightarrow$ `Or(f1, f2)`

### Main `Formula` Methods

#### `substitute(sub_map)`
Substitutes variables specified in `sub_map` keys (e.g., `{"A": Var("p"), "B": Var("q")}`) with corresponding formulas. Correctly handles variable binding to prevent capture of variables bound by quantifiers.

#### `free_variables()`
Returns a `set` containing the names of all free variables in the formula.

#### `match_schema(schema)`
Compares the current formula against a schema formula (containing meta-variables). If matching succeeds, returns a dictionary `{meta_variable_name: subformula_or_string}`, otherwise returns `None`.

### `parse_formula(s)` Function

Parses a text string into a `Formula` tree.

- **Supported ASCII operators**: `->`, `<->`, `&`, `|`, `~`, `!`, `=`, `forall`, `exists`.
- **Supported Unicode symbols**: `→`, `↔`, `∧`, `∨`, `¬`, `∀`, `∃`.

#### Example Usage:

```python
from solver.formula import parse_formula, Var, Not, Implies

# Using Python operators
A = Var("A")
B = Var("B")
f1 = (~A) >> B
print(f1)  # (~A -> B)

# Parsing from string
f2 = parse_formula("forall x, (P(x) -> (exists y, (x = y)))")
print("Free variables in f2:", f2.free_variables())

# Schema matching
schema = parse_formula("P -> Q")
concrete = parse_formula("(a & b) -> c")
bindings = concrete.match_schema(schema)
print("Match bindings:", bindings)  # {'P': And(Var('a'), Var('b')), 'Q': Var('c')}
```

---

## 2. `solver.database`

The [`solver.database`](file:///c:/Users/franc/Programmazione/solver/solver/database.py) module manages data persistence for theories, axioms, theorems, and proofs using an SQLite database.

### `TheoryDatabase` Class

#### Initialization
```python
db = TheoryDatabase(db_path="theory.db")
```

Upon creation, `init_db()` runs automatically to create the following tables if they do not exist:
1. **`axioms`**: Stores axioms (`id`, `name`, `formula_str`).
2. **`theorems`**: Stores theorem theses (`id`, `name`, `thesis_str`, `lean_code`, `is_verified`).
3. **`theorem_hypotheses`**: Maintains the list of hypotheses associated with each theorem.
4. **`theorem_steps`**: Stores each proof step with justification type (`Axiom`, `Hypothesis`, `MP`, `Lemma`), argument step indices (`arg1`, `arg2`), reference name (`ref_name`), and JSON substitutions.
5. **`dependencies`**: Tracks directed acyclic graph (DAG) dependencies between theorems and lemmas.

### Main Methods

- **`add_axiom(name, formula_str)`**: Inserts a new axiom into the database.
- **`get_axiom(name)`**: Retrieves the formula string for the specified axiom.
- **`get_all_axioms()`**: Returns a dictionary `{name: formula_string}` of all registered axioms.
- **`save_theorem(name, thesis_str, hypotheses, steps, dependencies=None, lean_code=None, is_verified=0)`**: Saves or overwrites a theorem, its hypotheses, steps, and dependencies.
- **`get_theorem(name)`**: Loads a complete theorem structure from the database as a Python dictionary.
- **`get_dependencies_recursive(theorem_name)`**: Returns a topologically sorted list of all lemmas on which the theorem recursively depends.

#### Example Usage:

```python
from solver.database import TheoryDatabase

db = TheoryDatabase("algebra.db")
db.add_axiom("associativity", "forall x, forall y, forall z, (f(f(x, y), z) = f(x, f(y, z)))")

axioms = db.get_all_axioms()
print("Saved axioms:", axioms)
```

---

## 3. `solver.prover`

The [`solver.prover`](file:///c:/Users/franc/Programmazione/solver/solver/prover.py) module provides the algorithm for automated search of formal proofs in Hilbert systems.

### Main Functions

#### `prove(thesis_str, hypotheses_strs, db, exclude_name=None, max_depth=10, max_formulas=1000, timeout_seconds=30)`

Automatically searches for a sequence of deductive steps to prove `thesis_str` starting from `hypotheses_strs`.

**Algorithm**:
1. Extracts subformulas from thesis and hypotheses to build the *Candidate Pool*.
2. Instantiates Hilbert axiom schemas (`ax1`, `ax2`, `ax3`) and previously verified lemmas in `TheoryDatabase` using candidates.
3. Applies a Breadth-First Search (BFS) based on **Modus Ponens (MP)** to derive new formulas until thesis is reached or timeout expires.
4. Calls `reconstruct_proof` to generate a topologically ordered step sequence.

#### `reconstruct_proof(goal, derived, lemma_map=None, db=None)`
Traces back collected justifications to reconstruct the minimal chain of proof steps from the initial axiom/hypothesis up to `goal`.

#### `get_subformulas(formula)`
Recursive helper function extracting all subformulas constituting a `Formula` object.

#### Example Usage:

```python
from solver.database import TheoryDatabase
from solver.prover import prove

db = TheoryDatabase("logic.db")
db.add_axiom("ax1", "A -> (B -> A)")
db.add_axiom("ax2", "(A -> (B -> C)) -> ((A -> B) -> (A -> C))")

# Proves that (p -> (q -> p)) follows directly from axiom 1
steps = prove(thesis_str="p -> (q -> p)", hypotheses_strs=[], db=db)
print("Number of steps found:", len(steps))
```

---

## 4. `solver.verifier`

The [`solver.verifier`](file:///c:/Users/franc/Programmazione/solver/solver/verifier.py) module performs two-level formal proof verification.

### Main Functions

#### `verify_proof_local(thm, db)`
Performs a formal validity check in pure Python environment.
Verifies that each step is justified by:
- **`Axiom`**: Formula must match an axiom schema present in the DB.
- **`Hypothesis`**: Reference `ref_name` (e.g. `h0`) must match the hypothesis exactly.
- **`MP`**: Formula must be the valid conclusion of Modus Ponens applied to the two specified prior steps `arg1` and `arg2`.
- **`Lemma`**: Formula and arguments must match thesis and substituted hypotheses of a verified lemma in the DB.

Returns a tuple `(ok: bool, error_message: str | None)`.

#### `verify_proof_with_lean(thm, db)`
Generates self-contained Lean 4 source code for the theorem (via `solver.lean_exporter`) and compiles it using the CLI executable `lean`.
Returns `(True, lean_code)` if compilation succeeds (exit code 0), otherwise `(False, error_message)`.

#### `verify_and_save(thm, db)`
Executes `verify_proof_local` first. If successful, attempts verification with `verify_proof_with_lean`. If Lean 4 approves the theorem, stores it in `TheoryDatabase` setting `is_verified = 1`.

#### Example Usage:

```python
from solver.database import TheoryDatabase
from solver.verifier import verify_proof_local

db = TheoryDatabase("logic.db")
thm_def = {
    'name': 'demo_thm',
    'thesis_str': 'A -> (B -> A)',
    'hypotheses': [],
    'steps': [
        {
            'step_idx': 0,
            'formula_str': 'A -> (B -> A)',
            'justification_type': 'Axiom',
            'ref_name': 'ax1',
            'substitution_json': {'A': 'A', 'B': 'B'}
        }
    ]
}

is_valid, error = verify_proof_local(thm_def, db)
print("Locally valid proof:", is_valid)
```

---

## 5. `solver.explorer`

The [`solver.explorer`](file:///c:/Users/franc/Programmazione/solver/solver/explorer.py) module offers automated theorem exploration and autonomous discovery capabilities.

### Main Functions

#### `explore_consequences(db, basic_vars=['p'], max_depth=1, max_theorems=20, min_proof_steps=0)`

1. **Generates Candidate Formulas**: Creates a combinatorial set of formulas using variables `basic_vars` up to depth `max_depth` (via `generate_candidates`).
2. **Instantiates Axioms and Lemmas**: Applies candidate formulas to axioms and lemmas present in the DB.
3. **Modus Ponens Saturation**: Runs a BFS loop to derive all possible logical consequences.
4. **Filtering and Saving**: Sorts derived formulas by structural complexity, reconstructs proofs, and executes `verify_and_save` with Lean 4 for each newly discovered theorem.

#### `generate_candidates(basic_vars, max_depth)`
Recursively generates all combinatorial formulas formable from a list of base variables (e.g. `['p', 'q']`).

#### Example Usage:

```python
from solver.database import TheoryDatabase
from solver.dependencies import load_first_order_axioms
from solver.explorer import explore_consequences

db = TheoryDatabase("explore_demo.db")
load_first_order_axioms(db)

# Explore up to 3 new theorems
new_found = explore_consequences(db, basic_vars=['p'], max_depth=1, max_theorems=3)
print(f"Discovered and verified theorems: {new_found}")
```

---

## 6. `solver.lean_exporter`

The [`solver.lean_exporter`](file:///c:/Users/franc/Programmazione/solver/solver/lean_exporter.py) module converts Python AST internal syntax to **Lean 4** formal syntax.

### Main Functions

#### `formula_to_lean(formula)`
Recursively maps a `Formula` AST node into the corresponding string in Lean 4 syntax:
- `Implies(A, B)` $\rightarrow$ `(A → B)`
- `And(A, B)` $\rightarrow$ `(A ∧ B)`
- `Or(A, B)` $\rightarrow$ `(A ∨ B)`
- `Not(A)` $\rightarrow$ `¬(A)`
- `Forall("x", body)` $\rightarrow$ `(∀ x, body)`
- `Exists("x", body)` $\rightarrow$ `(∃ x, body)`
- `Equals(a, b)` $\rightarrow$ `(a = b)`
- `Pred("P", [a, b])` $\rightarrow$ `(P a b)`

#### `export_proof(theorem_name, db)`
Loads the theorem and its dependency graph from the database and generates a complete, self-contained Lean 4 source document (including axiom definitions, preliminary lemmas, and proof steps using `have` and `exact` tactics).

#### Example Usage:

```python
from solver.formula import parse_formula
from solver.lean_exporter import formula_to_lean

f = parse_formula("forall x, (P(x) & Q(x))")
print("Lean 4 syntax:", formula_to_lean(f))
# Prints: (∀ x, ((P x) ∧ (Q x)))
```

---

## 7. `solver.dependencies`

The [`solver.dependencies`](file:///c:/Users/franc/Programmazione/solver/solver/dependencies/__init__.py) subpackage provides predefined axiomatic libraries for mathematical logic.

### Included Modules

#### 1. `solver.dependencies.first_order_logic`
Contains standard axioms for First-Order Logic (FOL):
- **Propositional Calculus**: `fol_k`, `fol_s`, `fol_dn`.
- **Quantifiers**: `fol_ui` (Universal Instantiation), `fol_ug` (Universal Generalization), `fol_eg` (Existential Generalization), `fol_ed` (Existential Elimination).
- **Equality (Leibniz)**: `eq_ref` (Reflexivity), `eq_sym` (Symmetry), `eq_trans` (Transitivity), `eq_subst` (Substitution/Congruence).

Functions: `get_first_order_axioms()`, `load_first_order_axioms(db)`.

#### 2. `solver.dependencies.second_order_logic`
Contains axioms for Second-Order Logic (SOL):
- **Second-Order Quantifiers**: `sol_ui`, `sol_ug`, `sol_eg`, `sol_ed`.
- **Structural**: `sol_comp` (Schema of Comprehension), `sol_choice` (Relational Axiom of Choice).
- **Induction**: `sol_induction` (Second-Order Peano Mathematical Induction Schema).

Functions: `get_second_order_axioms()`, `load_second_order_axioms(db)`.

#### 3. `solver.dependencies.logic`
Unified module aggregating both FOL and SOL.

Functions: `get_all_logic_axioms()`, `load_all_logic_axioms(db)`.

#### Example Usage:

```python
from solver.database import TheoryDatabase
from solver.dependencies import load_all_logic_axioms, get_first_order_axioms

db = TheoryDatabase("fol_sol_demo.db")

# Load all FOL and SOL axioms
load_all_logic_axioms(db)

axioms = db.get_all_axioms()
print(f"Loaded {len(axioms)} axioms into database.")
print("Axiom eq_subst:", axioms.get("eq_subst"))
```

---

## 8. `solver.deducer`

The [`solver.deducer`](file:///c:/Users/franc/Programmazione/solver/solver/deducer.py) module provides the Forward Deduction Engine. Starting from a set of user-provided hypotheses, it applies theory axioms and previously saved theorems/lemmas in the database to derive all possible logical consequences via Modus Ponens and instantiation.

### `Deducer` Class

#### Initialization
```python
deducer = Deducer(db=None, auto_load_axioms=True)
```
- **`db`**: Instance of `TheoryDatabase`. If not provided, an in-memory database is created automatically.
- **`auto_load_axioms`**: If `True`, ensures loading basic logical axioms (e.g. `ax1`, `ax2`, `ax3`).

#### `deduce(hypotheses, max_formulas=200, include_hypotheses=False, timeout_seconds=30.0)` Method
Performs forward search to derive consequences.
- **`hypotheses`**: List of strings (e.g. `["p -> q", "p"]`) or `Formula` instances.
- **`max_formulas`**: Maximum number of formulas to derive.
- **`include_hypotheses`**: If `True`, includes initial hypotheses among results.
- **`timeout_seconds`**: Maximum execution time in seconds.

Returns a list of `Consequence` objects.

### `Consequence` Class
Represents a derived consequence. Key properties:
- **`formula`**: `Formula` object of the consequence.
- **`formula_str`**: String representation of the formula.
- **`proof`**: Ordered list of formal proof steps compatible with `verify_proof_local`.
- **`justification_type`**: Justification type (`'MP'`, `'Axiom'`, `'Lemma'`, `'Hypothesis'`).
- **`is_verified`**: Boolean indicating local validation outcome.

### `deduce_consequences(hypotheses, db=None, max_formulas=200, include_hypotheses=False)` Function
Quick helper function to perform deduction without manually instantiating `Deducer`.

#### Example Usage:

```python
from solver.deducer import Deducer, deduce_consequences

# Example 1: Quick usage with helper function
consequences = deduce_consequences(["p -> q", "q -> r", "p"])
for c in consequences:
    print(f"Derived: {c.formula_str} via {c.justification_type}")
    # Output: 
    # Derived: q via MP
    # Derived: r via MP

# Example 2: Usage with custom database
from solver.database import TheoryDatabase

db = TheoryDatabase("my_theory.db")
deducer = Deducer(db=db)
results = deducer.deduce(hypotheses=["A -> B", "A"])
for res in results:
    print(f"Consequence: {res.formula_str}")
    print(f"Proof steps: {res.proof}")
```
