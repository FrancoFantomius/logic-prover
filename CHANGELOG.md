# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **Classified Axioms & Mathematical Theories Subfolder**: Added `logic_prover.axioms` subfolder unifying and classifying mathematical theories into dedicated modules (`group_theory`, `peano`, `zfc`, `analysis`, `linear_algebra`, `ring_theory`, `order_theory`, `boolean_algebra`, `relations`, `functions`, `equality`, `logic`).
- **Theory Abstraction & Registry**: Introduced the `Theory` dataclass and global theory registry (`get_theory`, `list_theories`, `get_all_theories`) enabling direct theorem proving (`theory.prove()`) with automatic premise management and signature binding.
- **Constructive Resolution with Prefixing and Translation**: Added resolution theorem provers for intuitionistic propositional logic (`logic_prover.constructive.resolution`), including direct clausal prefixed resolution (`PrefixedResolutionProver`) and relational S4 modal translation to First-Order Logic (`TranslationResolutionProver`).
- **Cython Acceleration for Constructive Logic**: Added optional native C compilation for constructive and intuitionistic logic modules (`logic_prover.constructive.common`, `logic_prover.constructive.prefix`, `logic_prover.constructive.matrix`, `logic_prover.constructive.ljt`, `logic_prover.constructive.wallen`, `logic_prover.constructive.resolution`).

### Removed
- **Legacy Knowledge Base Package (`logic_prover.kb`)**: Removed legacy `logic_prover.kb` subpackage in favor of the consolidated, classified `logic_prover.axioms` architecture.
---

## [0.1.4] - 2026-08-15

### Added
- **Cython C-Extension Acceleration**: Optional native C compilation of core bottlenecks (`logic_prover.core.ast`, `logic_prover.core.substitutions`, `logic_prover.core.visitors`, `logic_prover.prover.clausifier`, `logic_prover.prover.rules`, `logic_prover.prover.engine`) with seamless fallback to pure Python when a C compiler is unavailable.
- **Automated Documentation Generator**: Built-in AST and reflection docstring extractor (`logic_prover.utils.doc_generator`) accessible via CLI `logic-prover docs`.
- **Structured Logging Subsystem**: Configurable contextual logging with timestamping, module filters, and formatting (`logic_prover.utils.logging`).
- **Second-Order Logic (SOL) Extension**: AST nodes, substitution engines, and axioms supporting second-order logic constructs (`logic_prover.sol`).
- **Interactive Proof Visualizer**: HTML DAG graph exporter powered by Jinja2 templates (`logic_prover.exporters.graph_exporter`).
- **Formula Exploration Heuristics**: Diversity-guided formula generation, term complexity metrics, and interestingness rank scoring in `logic_prover.explorer`.

### Changed
- Refactored top-level package namespace from `logic` to `logic_prover` for standard PyPI distribution.
- Enhanced test suite coverage (>85%) with property-based testing powered by Hypothesis.
- Optimized given-clause resolution loop (Otter/Discount loop) with enhanced clause indexing and subsumption caching.
- Synchronized package version and public API exports in `logic_prover.__init__`.

### Fixed
- Fixed Lean 4 exporter AST syntax translation, term precedence parenthesization, and variable quantifier scoping.
- Resolved type annotation inconsistencies in parser and sort validator.
- Corrected Windows cross-platform path handling in CLI and documentation generation.

---

## [0.1.3] - 2024-05-20

### Added
- **Network Dependency Deducer**: Minimal hypothesis subset detector and logical equivalence classifier (`logic_prover.deducer`).
- **Lean 4 Exporter**: Initial export module translating first-order formulas and theorem proofs into Lean 4 code stubs.
- **Graph Exporter**: DOT and JSON dependency graph exporter for theories.

### Changed
- Modularized mathematical knowledge bases into dedicated subpackages (`kb.equality`, `kb.groups`, `kb.numbers`, `kb.orders`, `kb.relations`, `kb.sets`).
- Refactored CLI commands for theorem proving, exploration, and database analysis.

---

## [0.1.2] - 2024-03-12

### Added
- Extended foundational knowledge base with group theory, order theory, and set theory axioms.
- Added natural deduction proof reconstruction from resolution DAGs.
- Support for sorted first-order logic signatures with custom sort declarations.

### Changed
- Improved term rewriting engine and equality substitution rules.

---

## [0.1.1] - 2024-02-01

### Added
- Subsumption checking and tautology deletion in resolution prover.
- Parameterized sort unification and variable renaming enhancements.

### Fixed
- Fixed bug in skolemization with deeply nested alternating quantifiers.
- Fixed variable clash during simultaneous substitutions.

---

## [0.1.0] - 2024-01-10

### Added
- Initial public release of `logic-prover`.
- First-Order Logic AST representation with parameterized sorts and type signatures.
- Propositional and first-order formula parser with flexible syntax (Unicode symbols `∀`, `∃`, `→`, `∧`, `∨`, `¬` and ASCII equivalents `forall`, `exists`, `=>`, `&`, `|`, `~`).
- Otter/Discount resolution theorem prover with equality superposition.
- Core CLI interface for theorem proving and database initialization.

[Unreleased]: https://github.com/FrancoFantomius/logic-prover/compare/v0.1.4...HEAD
[0.1.4]: https://github.com/FrancoFantomius/logic-prover/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/FrancoFantomius/logic-prover/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/FrancoFantomius/logic-prover/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/FrancoFantomius/logic-prover/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/FrancoFantomius/logic-prover/releases/tag/v0.1.0
