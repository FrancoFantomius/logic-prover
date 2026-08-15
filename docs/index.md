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

- **`logic_prover.core`**: AST definitions, sort systems, signatures, parser, substitution, rewriting.
- **`logic_prover.prover`**: Resolution theorem prover engine, clause generation, proof DAG reconstruction.
- **`logic_prover.explorer`**: Novel formula generation, heuristic ranking, and diversity filters.
- **`logic_prover.deducer`**: Network dependency analysis and hypothesis minimal subset detection.
- **`logic_prover.exporters`**: Translation to Lean 4 formal code and interactive HTML DAG graph rendering.
- **`logic_prover.kb`**: Knowledge database interface and foundational mathematical axioms.
- **`logic_prover.sol`**: Second-Order Logic (SOL) extensions.
- **`logic_prover.utils`**: Central logging subsystem and automated documentation generator.

## Submodule API Reference

| Module Group | Documentation Link | Documented Classes | Documented Functions |
| :--- | :--- | :--- | :--- |
| `utils` | [utils →](api/utils.md) | 7 | 6 |
