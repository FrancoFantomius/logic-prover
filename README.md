# Solver Library

**Solver** is a Python library for representing logical formulas, automated theorem proving in Hilbert-style proof systems, local formal verification, integration with the **Lean 4** proof assistant, automated exploration of new logical consequences, and managing First-Order and Second-Order logic theories.

---

## Key Features

- **Logical AST and Parser**: Object-oriented construction of logical formulas (Propositional, First-Order, Second-Order, Equality) with support for Unicode (`∀`, `∃`, `→`, `↔`, `∧`, `∨`, `¬`) and ASCII syntax (`forall`, `exists`, `->`, `<->`, `&`, `|`, `~`).
- **SQLite Theory Database (`TheoryDatabase`)**: Structured and persistent storage of axioms, hypotheses, proved theorems, proof steps, and dependency graphs.
- **Automated Prover (`prove`)**: Forward search algorithm based on Breadth-First Search (BFS) and Modus Ponens with schematic axiom instantiation and lemma reuse.
- **Two-Level Verifier (`verifier`)**:
  1. Structural validation and local logical correctness in Python.
  2. Generation and execution of self-contained **Lean 4** code via the official Lean CLI.
- **Logical Consequence Explorer (`explore_consequences`)**: Automatic generation and saturation of new derivable formulas, with automatic verification and database entry.
- **Ready-to-Use Axiom Libraries (`solver.dependencies`)**: Built-in modules with axioms for propositional calculus, First-Order Logic (FOL) with Leibniz equality, and Second-Order Logic (SOL) with comprehension schema, choice, and mathematical induction.

---

## Installation

Ensure you have Python >= 3.8 installed. To install the library in developer mode:

```bash
pip install -e .
```

To run unit tests:

```bash
python -m unittest discover tests
```

*(Optional)* To enable Lean 4 verification, install the `lean` compiler and make sure it is available in your system `PATH`.

---

## Quick Start Examples

### 1. Creating and Manipulating Formulas

You can construct formulas programmatically using the AST, use Python's overloaded operators (`~`, `>>`, `&`, `|`), or use the parser:

```python
from solver import Var, Implies, parse_formula, formula_to_lean

# Programmatic construction via AST
p = Var("p")
q = Var("q")
formula1 = p >> (q >> p)
print("Formula AST:", formula1)  # (p -> (q -> p))

# String parsing (supports ASCII or Unicode syntax)
formula2 = parse_formula("forall x, (P(x) -> Q(x))")
print("Formula Parser:", formula2)  # (forall x, (P(x) -> Q(x)))

# Conversion to Lean 4 syntax
print("Lean 4:", formula_to_lean(formula2))  # (∀ x, ((P x) → (Q x)))
```

### 2. Database Management and Axioms

Initialize a logical theory by registering propositional calculus axioms:

```python
from solver import TheoryDatabase

db = TheoryDatabase("my_theory.db")

# Manual addition of Hilbert axioms
db.add_axiom("ax1", "A -> (B -> A)")
db.add_axiom("ax2", "(A -> (B -> C)) -> ((A -> B) -> (A -> C))")
db.add_axiom("ax3", "(~A -> ~B) -> (B -> A)")

print("Registered Axioms:", db.get_all_axioms())
```

### 3. Automated Theorem Proving

Generate a formal proof for the thesis $p \to p$ starting from registered axioms:

```python
from solver import TheoryDatabase, prove

db = TheoryDatabase("my_theory.db")
db.add_axiom("ax1", "A -> (B -> A)")
db.add_axiom("ax2", "(A -> (B -> C)) -> ((A -> B) -> (A -> C))")
db.add_axiom("ax3", "(~A -> ~B) -> (B -> A)")

# Proof of (p -> p) without hypotheses
steps = prove(thesis_str="p -> p", hypotheses_strs=[], db=db)

for step in steps:
    print(f"Step {step['step_idx']}: {step['formula_str']} [{step['justification_type']}]")
```

### 4. Local Validation, Lean 4 & Export

Verify the theorem and save it to the database:

```python
from solver import TheoryDatabase, verify_and_save, export_proof

db = TheoryDatabase("my_theory.db")
# (Assuming axioms were loaded and steps generated...)

thm = {
    'name': 'identity_p',
    'thesis_str': 'p -> p',
    'hypotheses': [],
    'steps': steps
}

success, msg = verify_and_save(thm, db)
if success:
    print("Theorem successfully verified!")
    # Export self-contained Lean 4 code
    lean_code = export_proof("identity_p", db)
    print("\n--- Lean 4 Source Code ---")
    print(lean_code)
else:
    print("Verification error:", msg)
```

### 5. Automatic Exploration of New Theorems

Allow the solver to explore and automatically discover new consequences derived from loaded axioms:

```python
from solver import TheoryDatabase, explore_consequences, dependencies

db = TheoryDatabase("explore.db")

# Load all First and Second-Order logic axioms included in the package
dependencies.load_all_logic_axioms(db)

# Generate and explore up to 5 new theorems
new_theorems = explore_consequences(
    db, 
    basic_vars=['p'], 
    max_depth=1, 
    max_theorems=5
)

print(f"Generated and verified {new_theorems} new theorems!")
```

---

## Module Documentation

For a complete guide on each library module, refer to the detailed documentation manual:

**[DOCUMENTATION.md](DOCUMENTATION.md)**

Module | Description
--- | ---
[`solver.formula`](DOCUMENTATION.md#1-solverformula) | AST for propositional formulas, FOL and SOL, parser and transformations
[`solver.database`](DOCUMENTATION.md#2-solverdatabase) | SQLite interface for axioms, theorems, steps, and dependencies
[`solver.prover`](DOCUMENTATION.md#3-solverprover) | Automated proof search algorithm (Forward BFS with Modus Ponens)
[`solver.verifier`](DOCUMENTATION.md#4-solververifier) | Local structural verifier and integration with the Lean 4 compiler
[`solver.explorer`](DOCUMENTATION.md#5-solverexplorer) | Automatic generation and saturation of new theoretical consequences
[`solver.lean_exporter`](DOCUMENTATION.md#6-solverlean_exporter) | AST-to-Lean translator and generator of verifiable Lean 4 source files
[`solver.dependencies`](DOCUMENTATION.md#7-solverdependencies) | Axiom packages for First-Order Logic (FOL) and Second-Order Logic (SOL)
[`solver.deducer`](DOCUMENTATION.md#8-solverdeducer) | Forward deduction engine for deriving logical consequences
[`solver.graph_exporter`](DOCUMENTATION.md#9-solvergraph_exporter) | Proof dependency graph extractor (DOT, JSON, interactive HTML)
