# Logic Prover (`logic-prover`)

[![PyPI version](https://img.shields.io/pypi/v/logic-prover.svg)](https://pypi.org/project/logic-prover/)
[![CI](https://github.com/FrancoFantomius/logic-prover/actions/workflows/ci.yml/badge.svg)](https://github.com/FrancoFantomius/logic-prover/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/Docs-francofantomius.com-blue.svg)](https://francofantomius.com/logic-prover/)
[![Changelog](https://img.shields.io/badge/Changelog-Keep_a_Changelog-orange.svg)](CHANGELOG.md)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC_BY--NC_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
[![Python Versions](https://img.shields.io/pypi/pyversions/logic-prover.svg)](https://pypi.org/project/logic-prover/)

`logic-prover` is a formal logic theorem prover, explorer, deducer, and Lean 4 exporter in Python with optional Cython acceleration.

📚 **Full Documentation & API Reference**: [https://francofantomius.com/logic-prover/](https://francofantomius.com/logic-prover/)

---

## Features
- **First-Order & Second-Order Logic AST**: Full support for parameterized sorts, canonical variable renaming, and substitutions.
- **Resolution Prover with Equality**: Otter/Discount given-clause loop with superposition and natural deduction proof reconstruction.
- **Formula Explorer**: Diversity-guided formula generation and interestingness heuristic ranking.
- **Deducer**: Network-level minimal hypothesis detection and equivalence classification.
- **Lean 4 Export**: High-fidelity translation of formulas, statements, and tactic proofs into Lean 4 code.
- **Interactive HTML Graphs**: Proof DAG and dependency graph visualizer.
- **Optional Cython Acceleration**: Core AST, substitutions, and resolution engine compiled to native C extensions for high performance.
- **Automated Documentation & Logging**: Structured logging subsystem and Reflection/AST documentation generator.

---

## Installation

### From PyPI

Install the latest release from [PyPI](https://pypi.org/project/logic-prover/):

```bash
pip install logic-prover
```

To install with visualization support (interactive HTML graphs with Jinja2):

```bash
pip install "logic-prover[vis]"
```

### From GitHub

You can also install the latest development version directly from GitHub:

```bash
pip install git+https://github.com/FrancoFantomius/logic-prover.git
```

### From Source (Development)

Clone the repository and install in editable mode:

```bash
git clone https://github.com/FrancoFantomius/logic-prover.git
cd logic-prover
pip install -e ".[dev,vis]"
```

---

## Quickstart & CLI

> **Syntax Note**: Formulas require `v0`, `v1`, ... for individual variables, `=>` (or `implies` / `→`) for implication, `&` (or `and` / `∧`) for conjunction, `|` (or `or` / `∨`) for disjunction, and `~` (or `not` / `¬`) for negation.

```bash
# Initialize Knowledge Database
logic-prover init --reset

# Prove a Theorem
logic-prover prove "(forall v0 (P(v0) => Q(v0))) => ((forall v0 P(v0)) => (forall v0 Q(v0)))"

# Explore Candidate Formulas
logic-prover explore --strategy mixed --count 20 --top-k 5

# Analyze Network Dependencies
logic-prover analyze

# Export to Lean 4
logic-prover export lean --output theorem.lean --stubs-only

# Export Interactive Proof Graph
logic-prover export graph --type dependency --output network.html

# Generate API Documentation
python utils/doc_generator.py --output-dir docs
```

*(You can also invoke via `python -m logic_prover`)*

---

## Python API Example

```python
import logging
import logic_prover
from logic_prover.kb import get_combined_signature
from logic_prover.core.parser import parse_formula, to_string
from logic_prover.prover.engine import TheoremProver
from logic_prover.config import SolverConfig

# Configure logging
logging.basicConfig(level=logging.INFO)

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

## Documentation

Full interactive documentation, API reference, architecture deep dives, and tutorials are available at:

🌐 **[https://francofantomius.com/logic-prover/](https://francofantomius.com/logic-prover/)**

You can also build the documentation locally using MkDocs:

```bash
pip install "logic-prover[docs]"
mkdocs serve
```

---

## Project Architecture

```
logic_prover/
├── core/         # AST, Sorts, Signature, Parser, Substitutions, Rewriting, Database
├── kb/           # Foundational mathematical knowledge bases (Logic, Equality, Numbers, Sets, Groups)
├── prover/       # Resolution Prover, Clausification, Proof Reconstruction
├── explorer/     # Formula Generator, Diversity Metrics, Ranking Heuristics
├── deducer/      # Network Analysis, Minimal Hypotheses, Equivalence Classes
├── exporters/    # Lean 4 Exporter & HTML Interactive Graph Visualizers
└── sol/          # Second-Order Logic (SOL) Extension

```

---

## Testing

Run unit tests via `pytest`:

```bash
pytest
```

or with Python's built-in `unittest`:

```bash
python -m unittest discover -s tests
```

---

## Contributing & Community

We welcome contributions to `logic-prover`! Please check out the following resources:

- **[Contributing Guidelines](CONTRIBUTING.md)**: Setup instructions, code style, testing, and PR workflow.
- **[Code of Conduct](CODE_OF_CONDUCT.md)**: Community standards and enforcement policies.
- **[Security Policy](SECURITY.md)**: How to report vulnerabilities securely.
- **[Changelog](CHANGELOG.md)**: Release history and version migration notes.

---

## License & Commercial Use

This project is licensed under the **Creative Commons Attribution-NonCommercial 4.0 International Public License (CC BY-NC 4.0)**. See the [LICENSE](LICENSE) file for the full legal text.

### Key Terms:
- **Attribution**: You must give appropriate credit to the author (**Franco Fantomius**), provide a link to the license, and indicate if changes were made.
- **Non-Commercial**: You may freely use, modify, and distribute this software for academic, research, personal, and non-commercial purposes.
- **Commercial Use / Dual Licensing**: Any commercial use, including incorporating this software into commercial software, hosted commercial services, or revenue-generating products, requires **prior written permission and a commercial license agreement** from the author.

For commercial inquiries and licensing agreements, please contact:
**Franco Fantomius** &lt;[mail@francofantomius.com](mailto:mail@francofantomius.com)&gt;
