# Solver Documentation Portal

Welcome to the formal logic theorem prover, explorer, and deducer library documentation.

## Submodule API Reference

| Module Group | Documentation Link | Documented Classes | Documented Functions |
| :--- | :--- | :--- | :--- |
| `config` | [config](api/config.md) | 1 | 0 |
| `core` | [core](api/core.md) | 45 | 31 |
| `deducer` | [deducer](api/deducer.md) | 1 | 4 |
| `explorer` | [explorer](api/explorer.md) | 4 | 7 |
| `exporters` | [exporters](api/exporters.md) | 2 | 0 |
| `kb` | [kb](api/kb.md) | 0 | 17 |
| `prover` | [prover](api/prover.md) | 8 | 23 |
| `sol` | [sol](api/sol.md) | 6 | 15 |
| `utils` | [utils](api/utils.md) | 7 | 6 |

---

## Architecture Overview

- **`solver.core`**: AST definitions, sort systems, signatures, parser, substitution, rewriting.
- **`solver.prover`**: Resolution theorem prover engine, clause generation, proof DAG reconstruction.
- **`solver.explorer`**: Novel formula generation, heuristic ranking, and diversity filters.
- **`solver.deducer`**: Network dependency analysis and hypothesis minimal subset detection.
- **`solver.exporters`**: Translation to Lean 4 formal code and interactive HTML DAG graph rendering.
- **`solver.kb`**: Knowledge database interface and foundational mathematical axioms.
- **`solver.sol`**: Second-Order Logic (SOL) extensions.
- **`solver.utils`**: Central logging subsystem and automated documentation generator.
