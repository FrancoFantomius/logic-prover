# Logic Documentation Portal

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

- **`logic_prover.core`**: AST definitions, sort systems, signatures, parser, substitution, rewriting.
- **`logic_prover.prover`**: Resolution theorem prover engine, clause generation, proof DAG reconstruction.
- **`logic_prover.explorer`**: Novel formula generation, heuristic ranking, and diversity filters.
- **`logic_prover.deducer`**: Network dependency analysis and hypothesis minimal subset detection.
- **`logic_prover.exporters`**: Translation to Lean 4 formal code and interactive HTML DAG graph rendering.
- **`logic_prover.kb`**: Knowledge database interface and foundational mathematical axioms.
- **`logic_prover.sol`**: Second-Order Logic (SOL) extensions.
- **`logic_prover.utils`**: Central logging subsystem and automated documentation generator.
