---
layout: home

hero:
  name: "Logic Prover"
  text: "Logic Documentation Portal & Theorem Prover"
  tagline: High-performance automated reasoning engine, formula generator, and proof reconstructor in Python.
  actions:
    - theme: brand
      text: Explore API Reference
      link: /api/core
    - theme: alt
      text: GitHub Repository
      link: https://github.com/FrancoFantomius/logic-prover

features:
  - title: Resolution Theorem Prover
    details: Complete first-order resolution prover with clause subsumption, heuristics, and proof DAG reconstruction.
    link: /api/prover
  - title: Formula Explorer
    details: Novel candidate generator with heuristic ranking, diversity metrics, and anti-unification.
    link: /api/explorer
  - title: Hypothesis Deducer
    details: Dependency analysis, minimal premise subsets, and equivalence class computation.
    link: /api/deducer
  - title: Lean 4 & Graph Exporters
    details: Translate proven theorems directly into verified Lean 4 code or interactive HTML DAG visualizations.
    link: /api/exporters
  - title: Foundational Knowledge Bases
    details: Built-in axiom libraries spanning propositional logic, equality, Peano arithmetic, sets, and groups.
    link: /api/kb
  - title: Second-Order Logic (SOL)
    details: Extensions for second-order quantification, predicate variables, and higher-order schema instantiation.
    link: /api/sol
---

## Architecture Overview

```mermaid
graph TD
    KB[Knowledge Bases: kb] --> Core[Core AST & Rewriting: core]
    Core --> Prover[Resolution Prover: prover]
    Core --> Explorer[Formula Explorer: explorer]
    Core --> Deducer[Hypothesis Deducer: deducer]
    Prover --> Exporters[Lean 4 & Graph Exporters: exporters]
    Deducer --> Exporters
```

## Submodule Directory

| Module Group | Description | Documentation |
| :--- | :--- | :--- |
| **`core`** | AST hierarchy, sorts, signature unification, substitutions & rewriting | [Read Reference →](/api/core) |
| **`prover`** | Resolution engine, given-clause loop, and proof DAG graph reconstruction | [Read Reference →](/api/prover) |
| **`explorer`** | Candidate formula generation, interestingness ranking & diversity metrics | [Read Reference →](/api/explorer) |
| **`deducer`** | Hypothesis dependency networks and minimal axiom subset detection | [Read Reference →](/api/deducer) |
| **`exporters`** | Lean 4 formal code generation and interactive HTML DAG rendering | [Read Reference →](/api/exporters) |
| **`kb`** | Axiom collections for logic, equality, arithmetic, sets, and groups | [Read Reference →](/api/kb) |
| **`sol`** | Second-Order Logic AST nodes and comprehension axiom schema | [Read Reference →](/api/sol) |
| **`config`** | Solver timeouts, resource bounds, and heuristic weights | [Read Reference →](/api/config) |
| **`utils`** | Structured logging, diagnostic tracing, and AST doc generator | [Read Reference →](/api/utils) |

## Quick Start

```python
from logic_prover.core.parser import parse_formula
from logic_prover.prover import TheoremProver

# Parse premises and target conjecture
p1 = parse_formula("forall x. (Human(x) -> Mortal(x))")
p2 = parse_formula("Human(socrates)")
conjecture = parse_formula("Mortal(socrates)")

# Prove conjecture using resolution
prover = TheoremProver(premises=[p1, p2])
result = prover.prove(conjecture)

print(f"Proved: {result.success}")
print(f"Proof Steps: {len(result.proof_steps)}")
```
