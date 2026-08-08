# Logic — Formal Logic Theorem Prover & Explorer in Python

`logic` is a Python library for formal logic, featuring First-Order Logic (FOL) AST manipulation, term rewriting, automated resolution theorem proving, formula exploration, dependency graph deduction, higher-order logic extensions, and Lean 4 export.

---

## Features
- **First-Order & Second-Order Logic AST**: Full support for parameterized sorts, canonical variable renaming, and substitutions.
- **Resolution Prover with Equality**: Otter/Discount given-clause loop with superposition and natural deduction proof reconstruction.
- **Formula Explorer**: Diversity-guided formula generation and interestingness heuristic ranking.
- **Deducer**: Network-level minimal hypothesis detection and equivalence classification.
- **Lean 4 Export**: High-fidelity translation of formulas, statements, and tactic proofs into Lean 4 code.
- **Interactive HTML Graphs**: Proof DAG and dependency graph visualizer.
- **Automated Documentation & Logging**: Structured logging subsystem and Reflection/AST documentation generator.

---

## Installation

### From GitHub via `pip`

You can install `logic` directly from GitHub using `pip`:

```bash
pip install git+https://github.com/FrancoFantomius/logic.git
```

To install with optional visualization features:

```bash
pip install "logic[vis] @ git+https://github.com/FrancoFantomius/logic.git"
```

### From Source (Development)

Clone the repository and install in editable mode:

```bash
git clone https://github.com/FrancoFantomius/logic.git
cd logic
pip install -e .
```

To install with development and visualization dependencies:

```bash
pip install -e ".[dev,vis]"
```

---

## Quickstart & CLI

> **Syntax Note**: Formulas require `v0`, `v1`, ... for individual variables, `=>` (or `implies` / `→`) for implication, `&` (or `and` / `∧`) for conjunction, `|` (or `or` / `∨`) for disjunction, and `~` (or `not` / `¬`) for negation.

```bash
# Initialize Knowledge Database
python -m logic init --reset

# Prove a Theorem
python -m logic prove "(forall v0 (P(v0) => Q(v0))) => ((forall v0 P(v0)) => (forall v0 Q(v0)))"

# Explore Candidate Formulas
python -m logic explore --strategy mixed --count 20 --top-k 5

# Analyze Network Dependencies
python -m logic analyze

# Export to Lean 4
python -m logic export lean --output theorem.lean --stubs-only

# Export Interactive Proof Graph
python -m logic export graph --type dependency --output network.html

# Generate API Documentation
python -m logic docs --output-dir docs
```

---

## Python API Example

```python
from logic.kb import get_combined_signature
from logic.core.parser import parse_formula, to_string
from logic.prover.engine import TheoremProver
from logic.config import SolverConfig
from logic.utils.logging import setup_logging

# Configure structured logging
setup_logging(log_level="INFO")

# Load logical signature containing predefined predicates & functions
signature = get_combined_signature()

# Configure and instantiate TheoremProver
config = SolverConfig(prover_timeout_sec=5.0, prover_max_steps=500)
prover = TheoremProver(signature=signature, config=config)

# Parse hypothesis and target formula (using 'v0', 'v1', ... for variables)
hypothesis = parse_formula("forall v0, (P(v0) => Q(v0))", signature=signature)
conclusion = parse_formula("(forall v0, P(v0)) => (forall v0, Q(v0))", signature=signature)

# Run resolution theorem prover (returns a ProofDAG on success)
proof_dag = prover.prove(target=conclusion, premises=[hypothesis])

print(f"Proof Found for target: {to_string(proof_dag.conclusion)}")
for step in proof_dag.topological_order():
    print(f"  [{step.id}] {step.rule}: {to_string(step.conclusion)}")
```

---

## Project Architecture

```
logic/
├── core/         # AST, Sorts, Signature, Parser, Substitutions, Rewriting, Database
├── kb/           # Foundational mathematical knowledge bases (Logic, Equality, Numbers, Sets, Groups)
├── prover/       # Resolution Prover, Clausification, Proof Reconstruction
├── explorer/     # Formula Generator, Diversity Metrics, Ranking Heuristics
├── deducer/      # Network Analysis, Minimal Hypotheses, Equivalence Classes
├── exporters/    # Lean 4 Exporter & HTML Interactive Graph Visualizers
├── sol/          # Second-Order Logic (SOL) Extension
└── utils/        # Logging Subsystem & Automated Doc Generator
```

---

## Testing

Run unit tests via Python's standard `unittest`:

```bash
python -m unittest discover -s tests
```
