# Implementation Plan and Architecture for `solver` Library

This document outlines the technical architecture and detailed implementation plan for the `solver` Python library. The goal of the library is to model formal logic, manipulate terms and formulas with infinitely indexed variables, explore and generate diverse non-trivial formulas, prove them automatically, analyze relationships between hypotheses and consequences, and export results to LEAN 4 and interactive HTML graphs.

> **Design Principle — FOL-First.**  
> The library targets **First-Order Logic with Sorts** as the first stable milestone. Second-Order Logic (SOL) support is architecturally planned but deferred to the final implementation phase. Every module below is designed to be FOL-complete before SOL extensions are added.

---

## 1. Project Directory Structure

```
solver/
│
├── pyproject.toml               # Python package configuration and dependencies
├── README.md                    # High-level documentation and quickstart guide
├── todo.md                      # Original requirements tracking
├── plan.md                      # Implementation plan (this file)
│
├── solver/                      # Main package directory
│   ├── __init__.py              # Public API exports
│   ├── __main__.py              # CLI entry point (python -m solver)
│   ├── config.py                # Central configuration (SolverConfig dataclass)
│   │
│   ├── core/                    # Core formal language and AST representations
│   │   ├── __init__.py
│   │   ├── ast.py               # AST nodes (Terms, Formulas, Variables v_n, Constants, Functions)
│   │   ├── sorts.py             # Sort / Type system for multi-domain reasoning (with parameterized sorts)
│   │   ├── signature.py         # Signature: declares available symbols, arities, and sorts
│   │   ├── validator.py         # AST validation: arity, sort correctness, bound variables, well-formedness
│   │   ├── visitors.py          # Visitor framework for recursive AST traversals
│   │   ├── parser.py            # Parser and Lexer for formula text conversion
│   │   ├── substitutions.py     # Variable substitutions, alpha-conversion, and FOL unification
│   │   ├── equality.py          # Equality reasoning subsystem (congruence closure)
│   │   ├── rewriter.py          # Term/formula rewriting engine
│   │   ├── exceptions.py        # Custom exception types for the entire library
│   │   └── database.py          # Persistent storage (SQLite) for formulas, axioms, and proved theorems
│   │
│   ├── sol/                     # Second-Order Logic extension (Phase 9)
│   │   ├── __init__.py
│   │   ├── ast_ext.py           # SOL-specific AST nodes (PredicateVariable, FunctionVariable, SOL quantifiers)
│   │   ├── substitutions_ext.py # Higher-order pattern unification and predicate substitution
│   │   └── kb_ext.py            # SOL axioms (Comprehension, Second-order Induction)
│   │
│   ├── kb/                      # Knowledge Base (Axiom Systems)
│   │   ├── __init__.py
│   │   ├── equality.py          # Equality axioms (reflexivity, symmetry, transitivity, congruence)
│   │   ├── logic.py             # First-Order Logic axioms (quantifier laws, propositional schemata)
│   │   └── numbers.py           # Peano axioms and basic arithmetic operations
│   │
│   ├── explorer/                # Formula Generator and Explorer
│   │   ├── __init__.py
│   │   ├── generator.py         # Axiom-rewrite and proof-frontier formula generation
│   │   ├── heuristics.py        # Multi-metric diversity scoring and redundancy checks
│   │   └── filter.py            # Discarded/Seen formula filter (Bloom Filter / Hashset)
│   │
│   ├── prover/                  # Automated Theorem Prover
│   │   ├── __init__.py
│   │   ├── engine.py            # Primary proof search engine (resolution / tableau)
│   │   ├── clausifier.py        # CNF conversion (Skolemization, Tseitin, clause normal form)
│   │   ├── rules.py             # Inference rules for the chosen calculus
│   │   ├── reconstruction.py    # Natural deduction proof reconstruction from resolution traces
│   │   └── proof.py             # Proof DAG data structures
│   │
│   ├── deducer/                 # Hypothesis-Consequence Relationship Analyzer
│   │   ├── __init__.py
│   │   ├── analyzer.py          # Logical dependencies, transitive closures, and minimal hypothesis sets
│   │   └── graph.py             # DependencyGraph data structure
│   │
│   ├── exporters/               # Formats & Visual Exporters
│   │   ├── __init__.py
│   │   ├── lean_exporter.py     # AST & Proof translator to LEAN 4 code
│   │   └── graph_exporter.py    # Proof and dependency graph exporter to interactive HTML/JS
│   │
│   └── utils/                   # General Utilities & Automated Documentation
│       ├── __init__.py
│       ├── logging.py           # Logging configuration and helpers
│       └── doc_generator.py     # Docstring auto-extraction and markdown doc builder
│
├── tests/                       # Unit and integration test suite (pytest)
│   ├── conftest.py              # Shared fixtures
│   ├── test_ast.py
│   ├── test_sorts.py
│   ├── test_signature.py
│   ├── test_validator.py
│   ├── test_visitors.py
│   ├── test_parser.py
│   ├── test_substitutions.py
│   ├── test_equality.py
│   ├── test_rewriter.py
│   ├── test_database.py
│   ├── test_explorer.py
│   ├── test_prover.py
│   ├── test_clausifier.py
│   ├── test_rules.py
│   ├── test_reconstruction.py
│   ├── test_deducer.py
│   └── test_exporters.py
│
└── docs/                        # Auto-generated API documentation
    ├── index.md
    └── api/
```

---

## 2. Core Formal Language Model & Rules

### 2.1 Variables and Symbols

1. **Infinite Indexed Variables $v_n$**: Individual variables are uniquely identified by a non-negative integer index $n \ge 0$ (e.g., $v_0, v_1, v_2, \dots$). Axioms and theorems instantiate specific subsets of these variables.
2. **Variable Kind**: Each variable carries a `kind` distinguishing `individual`, `predicate`, and `function` usage. This simplifies sort-checking and traversal algorithms.
3. **Fixed Functions $f_n$ and Constants $c_n$**: Functions (with explicit arity) and constants are fixed domain symbols. They are **not** treated as quantifiable or substitutable variable slots when dynamically creating new formulas.
4. **Predicates $P_n$, Connectives, and Quantifiers**: Full support for atomic predicates $P(t_1, \dots, t_k)$, equality $t_1 = t_2$, connectives ($\neg, \land, \lor, \implies, \iff$), and quantifiers ($\forall, \exists$).

### 2.2 Sort / Type System

To prevent unsound cross-domain unification (e.g., treating a natural number as a set), every variable, constant, and function carries a **sort annotation**.

- **Sort Hierarchy**:
  - `PrimitiveSort(name)`: Atomic sorts — `Ind` (generic individual), `Nat` (natural numbers), `Bool` (propositions/truth values).
  - `ParameterizedSort(constructor, args)`: Parameterized sorts — e.g., `Set(Nat)`, `Set(Set(Nat))`, `Pair(Nat, Bool)`, `List(Nat)`.
  - `FunctionSort(arg_sorts, return_sort)`: Higher-order function sorts (reserved for SOL phase).
- **Sort compatibility**: Unification only succeeds between terms of compatible sorts. `Ind` acts as a supertype of all individual sorts.
- **Predicate and function sorts**: Each predicate/function declares the sorts of its arguments and (for functions) its return sort via the `Signature`.

### 2.3 Signature

A `Signature` object describes all available symbols in a given logical context:

- **Functions**: name → (arity, argument sorts, return sort)
- **Predicates**: name → (arity, argument sorts)
- **Constants**: name → sort
- **Sorts**: registered sort names and parameterized sort constructors

The signature is used by the parser, validator, and prover to enforce well-formedness.

### 2.4 Second-Order Logic Support (Deferred to Phase 9)

> SOL support is architecturally planned but **not implemented until Phase 9**. The AST, substitution, and prover modules are designed with extension points for SOL, but the first stable milestone is FOL with sorts.

When implemented, the SOL extension (`solver/sol/`) will add:

- **Predicate variables $\mathcal{P}_n$**: Quantifiable predicate symbols.
- **Function variables $\mathcal{F}_n$**: Quantifiable function symbols.
- **Second-order quantifiers**: `ForallPred`, `ExistsPred`, `ForallFunc`, `ExistsFunc`.
- **Higher-order pattern unification**: Restricted to higher-order patterns (variables applied to distinct bound variables), not general higher-order unification (which is undecidable).
- **Explicit template matching** for SOL Comprehension Schema instantiation, rather than general higher-order unification.

---

## 3. Module Details & Functions to Implement

### 3.1 `solver/core/ast.py`

Defines immutable data structures (`@dataclass(frozen=True)`) for the Abstract Syntax Tree (AST) representing terms and formulas. All AST nodes are frozen dataclasses, which gives them automatic structural `__eq__` and `__hash__` based on their fields — this is critical for set membership, dictionary keys, and the `FormulaFilter`.

#### Classes & Types:

**Terms:**
- `Term` (Abstract Base Class)
  - `Variable(id: int, sort: Sort = Ind, kind: VariableKind = VariableKind.INDIVIDUAL)`: Represents individual variable $v_n$ with sort annotation and kind.
  - `Constant(name: str, sort: Sort = Ind)`: Represents constant $c_n$.
  - `FunctionApp(func: str, arity: int, args: Tuple[Term, ...], return_sort: Sort = Ind)`: Represents function application $f(t_1, \dots, t_k)$.

**Variable Kinds:**
- `VariableKind(Enum)`: `INDIVIDUAL`, `PREDICATE`, `FUNCTION` — distinguishes variable usage for sort-checking and traversal.

**Formulas:**
- `Formula` (Abstract Base Class)
  - `PredicateApp(pred: str, arity: int, args: Tuple[Term, ...])`: Predicate application.
  - `Equality(left: Term, right: Term)`: Represents $t_1 = t_2$.
  - `Not(operand: Formula)`
  - `And(left: Formula, right: Formula)`
  - `Or(left: Formula, right: Formula)`
  - `Implies(left: Formula, right: Formula)`
  - `Iff(left: Formula, right: Formula)`
  - `Forall(variable: Variable, body: Formula)`: First-order universal quantification.
  - `Exists(variable: Variable, body: Formula)`: First-order existential quantification.

> **Note:** SOL AST nodes (`PredicateVariable`, `FunctionVariable`, `ForallPred`, `ExistsPred`, `ForallFunc`, `ExistsFunc`) are defined in `solver/sol/ast_ext.py` and registered as extensions in Phase 9.

#### Functions to Implement in `ast.py`:
- `free_variables(node: Union[Term, Formula]) -> Set[Variable]`: Returns the set of free individual variables in a term or formula.
- `bound_variables(node: Union[Term, Formula]) -> Set[Variable]`: Returns the set of bound variables in a formula.
- `canonicalize_bound_variables(formula: Formula) -> Formula`: Performs canonical alpha-conversion of **bound variables only** using de Bruijn-style sequential renaming ($v_0, v_1, v_2, \dots$). Free variable identity is preserved. This ensures alpha-equivalent formulas yield identical structural hashes without accidentally identifying non-equivalent formulas.
- `formula_depth(formula: Formula) -> int`: Computes the maximum depth of the AST.
- `formula_size(formula: Formula) -> int`: Computes the total number of AST nodes.

> **Design Decision (from review feedback):** Canonicalization renames **bound variables only**. Free variables retain their original identity. This avoids the dangerous case where `P(x,y)` and `P(y,x)` could be incorrectly identified as alpha-equivalent. De Bruijn indices are used internally for bound variable representation to eliminate alpha-conversion issues entirely.

---

### 3.2 `solver/core/sorts.py`

Defines the sort/type system for multi-domain reasoning with support for parameterized sorts.

#### Classes & Functions:
- `Sort` (Abstract Base Class, frozen dataclass)
  - `PrimitiveSort(name: str)`: Atomic sorts.
  - `ParameterizedSort(constructor: str, args: Tuple[Sort, ...])`: Parameterized sorts (e.g., `Set(Nat)`, `Pair(Nat, Bool)`, `List(Nat)`).
  - `FunctionSort(arg_sorts: Tuple[Sort, ...], return_sort: Sort)`: For SOL phase.
- **Built-in constants**: `Ind = PrimitiveSort("Ind")`, `Nat = PrimitiveSort("Nat")`, `Bool = PrimitiveSort("Bool")`.
- **Parameterized sort constructors**: `SetSort(element: Sort) -> ParameterizedSort`, `ListSort(element: Sort) -> ParameterizedSort`, `PairSort(a: Sort, b: Sort) -> ParameterizedSort`.
- `is_compatible(s1: Sort, s2: Sort) -> bool`: Returns `True` if two sorts can be unified. `Ind` is compatible with all individual sorts. Parameterized sorts require recursive compatibility of their arguments.
- `sort_of_term(term: Term, signature: Signature) -> Sort`: Infers or returns the sort of a term using the signature context.

---

### 3.3 `solver/core/signature.py`

Declares the available symbols in a logical context.

#### Class `Signature`:
- `functions: Dict[str, FunctionDecl]`: Function declarations (name → arity, arg sorts, return sort).
- `predicates: Dict[str, PredicateDecl]`: Predicate declarations (name → arity, arg sorts).
- `constants: Dict[str, Sort]`: Constant declarations (name → sort).
- `sort_constructors: Dict[str, int]`: Parameterized sort constructors (name → arity).
- `register_function(name, arity, arg_sorts, return_sort) -> None`: Register a function symbol.
- `register_predicate(name, arity, arg_sorts) -> None`: Register a predicate symbol.
- `register_constant(name, sort) -> None`: Register a constant.
- `register_sort_constructor(name, arity) -> None`: Register a parameterized sort constructor.
- `lookup_function(name) -> Optional[FunctionDecl]`: Look up a function declaration.
- `lookup_predicate(name) -> Optional[PredicateDecl]`: Look up a predicate declaration.
- `merge(other: Signature) -> Signature`: Merge two signatures (for combining axiom systems).

---

### 3.4 `solver/core/validator.py`

Centralized validation for AST well-formedness. Rather than scattering invariant checks throughout the codebase, all validation runs through this module.

#### Functions:
- `validate_formula(formula: Formula, signature: Signature) -> List[ValidationError]`: Checks a formula for:
  - Predicate/function arity correctness against the signature.
  - Sort correctness of all arguments.
  - No unbound de Bruijn indices (all bound variables are properly scoped).
  - No duplicate binders in the same scope.
  - Well-formedness of nested quantifiers.
- `validate_term(term: Term, signature: Signature) -> List[ValidationError]`: Checks a term for arity and sort correctness.
- `is_well_formed(node: Union[Term, Formula], signature: Signature) -> bool`: Convenience wrapper returning `True` if no validation errors.

---

### 3.5 `solver/core/visitors.py`

A generic visitor framework to eliminate duplicated recursive traversal logic across modules.

#### Classes:
- `ASTVisitor[T]` (Generic Abstract Base Class):
  - `visit_variable(node: Variable) -> T`
  - `visit_constant(node: Constant) -> T`
  - `visit_function_app(node: FunctionApp) -> T`
  - `visit_predicate_app(node: PredicateApp) -> T`
  - `visit_equality(node: Equality) -> T`
  - `visit_not(node: Not) -> T`
  - `visit_and(node: And) -> T`
  - `visit_or(node: Or) -> T`
  - `visit_implies(node: Implies) -> T`
  - `visit_iff(node: Iff) -> T`
  - `visit_forall(node: Forall) -> T`
  - `visit_exists(node: Exists) -> T`
  - `visit(node: Union[Term, Formula]) -> T`: Dispatch method.
- `ASTTransformer(ASTVisitor[Union[Term, Formula]])`: A visitor that returns transformed AST nodes (for substitution, rewriting, etc.).

**Implemented visitors (using the framework):**
- `DepthVisitor`: Computes `formula_depth`.
- `SizeVisitor`: Computes `formula_size`.
- `FreeVariableCollector`: Computes `free_variables`.
- `SubstitutionTransformer`: Implements `substitute_formula` / `substitute_term`.
- `ExportVisitor`: Used by exporters for string translation.

---

### 3.6 `solver/core/exceptions.py`

Defines custom exception types for clear error reporting throughout the library.

#### Exception Classes:
- `SolverError(Exception)`: Base exception for all solver errors.
- `ParseError(SolverError)`: Raised on malformed input to `parse_formula` / `parse_term`.
- `UnificationError(SolverError)`: Raised when unification fails (e.g., occur-check violation, sort mismatch).
- `SortMismatchError(UnificationError)`: Raised when terms of incompatible sorts are unified.
- `ProofTimeoutError(SolverError)`: Raised when the prover exceeds `timeout_sec`.
- `ProofSearchExhaustedError(SolverError)`: Raised when the prover exhausts its search space without finding a proof.
- `InvalidFormulaError(SolverError)`: Raised when a structurally invalid formula is constructed (e.g., wrong arity).
- `ValidationError(SolverError)`: Raised by the validator for AST well-formedness violations.
- `DatabaseError(SolverError)`: Raised on database I/O or integrity failures.

---

### 3.7 `solver/core/parser.py`

Handles conversion from text notation to AST objects and reverse formatting (`to_string`). Uses the `Signature` for symbol resolution and arity checking.

#### Functions to Implement in `parser.py`:
- `parse_formula(text: str, signature: Signature) -> Formula`: Parses string representations (e.g., `"forall v0 : Ind, (P(v0) => Q(v0))"`) into a `Formula` AST. Raises `ParseError` on malformed input.
- `parse_term(text: str, signature: Signature) -> Term`: Parses string representations into a `Term` AST. Raises `ParseError` on malformed input.
- `to_string(node: Union[Term, Formula], notation: str = "infix") -> str`: Formats AST into readable text representations.
- `tokenize(text: str) -> List[Token]`: Helper lexer to tokenize input strings. Raises `ParseError` on unrecognized tokens.

---

### 3.8 `solver/core/substitutions.py`

Provides substitution, alpha-renaming, and **first-order** unification routines used by both the prover engine and the formula generator.

> **Scope Restriction (from review feedback):** Unification in this module is **strictly first-order**. Robinson's algorithm operates on first-order terms only. It does NOT handle predicate variables, function variables, or SOL expressions. Higher-order pattern unification is deferred to `solver/sol/substitutions_ext.py`.

#### Functions to Implement in `substitutions.py`:
- `substitute_term(term: Term, mapping: Dict[Variable, Term]) -> Term`: Replaces variables within a term according to a mapping dictionary. Validates sort compatibility.
- `substitute_formula(formula: Formula, mapping: Dict[Variable, Term]) -> Formula`: Replaces free variables within a formula while preventing variable capture (using de Bruijn shift or explicit renaming). Validates sort compatibility.
- `unify_terms(t1: Term, t2: Term, subst: Optional[Dict[Variable, Term]] = None) -> Dict[Variable, Term]`: Implements Robinson's unification algorithm on **first-order terms** with occur-check. Raises `UnificationError` on failure (including sort mismatches).
- `unify_formulas(f1: Formula, f2: Formula) -> Dict[Variable, Term]`: Unifies atomic predicate expressions (first-order only). Raises `UnificationError` on failure.
- `compose_substitutions(s1: Dict[Variable, Term], s2: Dict[Variable, Term]) -> Dict[Variable, Term]`: Composes two substitutions.
- `apply_substitution(subst: Dict[Variable, Term], term: Term) -> Term`: Applies a substitution to a term (idempotent application).

---

### 3.9 `solver/core/equality.py`

Equality reasoning subsystem. Equality is notoriously difficult and deserves dedicated algorithms rather than being handled via repeated substitution.

> **Design Decision (from review feedback):** Modern provers use congruence closure and superposition rather than naive recursive substitution for equality. This module provides the foundational equality engine.

#### Classes & Functions:
- Class `CongruenceClosure`:
  - `__init__(self)`: Initializes the union-find structure.
  - `add_term(term: Term) -> None`: Registers a term in the congruence graph.
  - `merge(t1: Term, t2: Term) -> None`: Asserts $t_1 = t_2$ and propagates congruence.
  - `are_equal(t1: Term, t2: Term) -> bool`: Checks if two terms are in the same equivalence class.
  - `explain(t1: Term, t2: Term) -> Optional[List[Equality]]`: Returns the chain of equalities that proves $t_1 = t_2$, or `None` if not equal.
- `equality_substitution(eq: Equality, formula: Formula) -> List[Formula]`: Generates all possible results of substituting one side of the equality for the other within a formula.

---

### 3.10 `solver/core/rewriter.py`

Term and formula rewriting engine for simplification, normalization, and proof search.

#### Classes & Functions:
- `RewriteRule(lhs: Union[Term, Formula], rhs: Union[Term, Formula], condition: Optional[Formula] = None)`: A rewrite rule $l \to r$ with optional side condition.
- `rewrite(node: Union[Term, Formula], rule: RewriteRule) -> Optional[Union[Term, Formula]]`: Applies a rewrite rule at the root. Returns `None` if the rule does not match.
- `rewrite_all(node: Union[Term, Formula], rules: List[RewriteRule]) -> Union[Term, Formula]`: Applies all matching rewrite rules bottom-up until a fixed point.
- `normalize(formula: Formula, rules: List[RewriteRule], max_steps: int = 100) -> Formula`: Normalizes a formula using the given rewrite rules.

---

### 3.11 `solver/core/database.py`

Persistent storage for formulas, foundational axioms, and proved theorems backed by **SQLite**.

#### Design:
- All data is stored in a single SQLite database file (path configurable via `SolverConfig.db_path`, default: `solver_data.db`).
- Formulas are serialized to a canonical JSON representation for storage and indexed by their canonical hash.
- **Additional indexed columns** (from review feedback): `ast_hash`, `canonical_string`, `free_variables` (JSON list), `predicate_names` (JSON list), `function_names` (JSON list), `depth`, `size`. These make searching dramatically faster.
- The database schema includes tables: `axioms`, `theorems`, `proofs`, `metadata`.
- All operations are transactional; concurrent reads are supported.

#### Class `KnowledgeDatabase`:
- `__init__(self, db_path: str)`: Opens or creates the SQLite database at `db_path`. Creates schema if not present.
- `add_axiom(name: str, formula: Formula, category: str) -> None`: Registers a new axiom. Raises `DatabaseError` on duplicate names.
- `add_theorem(name: str, formula: Formula, proof: ProofDAG) -> None`: Registers a proved theorem along with its serialized proof DAG.
- `get_axioms(category: Optional[str] = None) -> List[Tuple[str, Formula]]`: Retrieves registered axioms (as name-formula pairs), optionally filtered by category.
- `get_theorems(category: Optional[str] = None) -> List[Tuple[str, Formula]]`: Retrieves proved theorems.
- `get_proof(theorem_name: str) -> Optional[ProofDAG]`: Retrieves the proof DAG for a named theorem.
- `contains_formula(formula: Formula) -> bool`: Checks if a formula (or its canonical form) already exists in the database (as axiom or theorem).
- `search_formulas(predicate_name: Optional[str] = None, max_depth: Optional[int] = None, max_size: Optional[int] = None) -> List[Formula]`: Queries formulas by structural properties using indexed columns.
- `close() -> None`: Closes the database connection.
- Context manager support (`__enter__`, `__exit__`) for use with `with` statements.

---

### 3.12 `solver/kb/` (Foundational Knowledge Base)

Defines formal axiom systems for the core concepts. Each module returns axioms as `List[Tuple[str, Formula]]` (name-formula pairs) for registration in the database.

> **Scope Restriction (from review feedback):** The initial knowledge base focuses on **Equality, Logic, and Peano arithmetic**. Set theory (ZFC), function concepts, and SOL axioms are deferred to later phases. Starting minimal reduces implementation risk while establishing a solid foundation.

#### Modules & Functions:

- `solver/kb/equality.py`:
  - `get_equality_axioms() -> List[Tuple[str, Formula]]`: Returns equality axioms — reflexivity, symmetry, transitivity, and congruence (substitution) schemas.

- `solver/kb/logic.py`:
  - `get_fol_axioms() -> List[Tuple[str, Formula]]`: Returns First-Order Logic axioms (quantifier laws, propositional schemata).

- `solver/kb/numbers.py`:
  - `get_peano_axioms() -> List[Tuple[str, Formula]]`: Returns Peano axioms for natural numbers ($0, S(n), +, \cdot, \le$). Uses `PrimitiveSort("Nat")` for all number variables.

**Deferred to later phases:**
- `solver/kb/groups.py` — Group theory axioms.
- `solver/kb/relations.py` — Relation axioms (reflexivity, transitivity, equivalence relations).
- `solver/kb/orders.py` — Partial and total order axioms.
- `solver/kb/sets.py` — Set theory axioms (minimal, not full ZFC).
- `solver/kb/functions.py` — Function concepts (domain, codomain, injectivity, surjectivity).
- `solver/sol/kb_ext.py` — SOL axioms (Comprehension, Second-order Induction).

---

### 3.13 `solver/explorer/` (Formula Explorer & Generator)

Generates new candidate formulas to be proven. Employs **semantic generation strategies** to produce useful conjectures rather than random syntactic combinations.

> **Design Decision (from review feedback):** Pure weighted-CFG generation over AST node types mostly produces trivial or uninteresting formulas. The explorer instead uses semantically-guided strategies that are closer to how automated theorem provers actually discover useful intermediate formulas.

#### Generation Algorithm (Semantically-Guided Strategies):

1. **Axiom Rewrite Strategy**: Apply rewrite rules, instantiations, and simplifications to existing axioms to derive candidate conjectures.
2. **Proof Frontier Strategy**: From successful proofs, extract intermediate lemmas and generate generalizations or specializations of those lemmas.
3. **Anti-Unification Strategy**: Compute the most specific generalization of pairs of existing theorems to discover common patterns.
4. **Saturation Strategy**: Apply inference rules exhaustively to a small set of axioms (bounded saturation) and collect non-trivial consequences.
5. **Existing Lemma Combination**: Combine existing lemmas using implications, conjunctions, and quantifier variations.
6. **Depth Budget**: Each strategy has a configurable depth limit to prevent explosion.
7. **Sort Constraints**: All generated formulas are validated against the signature for sort-correctness.
8. **Diversity Pressure**: After generating a batch, candidates are ranked by multi-metric diversity scores and deduplicated against the `FormulaFilter`.

#### Modules & Functions:

1. `solver/explorer/heuristics.py`:
   - `calculate_diversity_scores(formula: Formula) -> DiversityMetrics`: Evaluates diversity based on **multiple independent metrics** (rather than a single scalar):
     - `ast_size: int` — Total number of AST nodes.
     - `symbol_entropy: float` — Shannon entropy of symbol usage.
     - `predicate_diversity: int` — Number of distinct predicates used.
     - `quantifier_depth: int` — Maximum nesting depth of quantifiers.
     - `variable_reuse: float` — Ratio of variable references to distinct variables.
     - `repeated_subtree_penalty: float` — Penalty for identical sub-structures.
     - `proof_distance: Optional[int]` — Minimum proof steps from axioms (if known).
   - `composite_interestingness(metrics: DiversityMetrics, weights: Optional[Dict[str, float]] = None) -> float`: Combines individual metrics into a composite score using configurable weights.
   - `is_redundant_structure(formula: Formula) -> bool`: Syntactically identifies trivial tautologies or redundant self-concatenations.

2. `solver/explorer/filter.py`:
   - Class `FormulaFilter`:
     - `add(formula: Formula) -> None`: Stores the canonical hash of a formula into the explored/discarded set.
     - `is_seen(formula: Formula) -> bool`: Checks if a formula (or an alpha-equivalent variant) has already been explored or discarded.
     - `save_state(filepath: str) -> None`: Persists the filter state to disk.
     - `load_state(filepath: str) -> None`: Loads the filter state from disk.

3. `solver/explorer/generator.py`:
   - Class `FormulaExplorer`:
     - `__init__(self, db: KnowledgeDatabase, signature: Signature, config: SolverConfig)`: Initializes the explorer with access to the knowledge base, signature, and configuration.
     - `generate_candidates(strategy: str = "mixed", max_depth: Optional[int] = None, count: Optional[int] = None) -> List[Formula]`: Generates candidate formulas using the specified strategy (`"axiom_rewrite"`, `"proof_frontier"`, `"anti_unification"`, `"saturation"`, `"mixed"`). Parameters default to `config.explorer_max_depth` and `config.explorer_batch_size`.
     - `rank_and_select(candidates: List[Formula], top_k: Optional[int] = None) -> List[Formula]`: Ranks candidates using `composite_interestingness` and filters out formulas present in `FormulaFilter`. Defaults to `config.explorer_top_k`.

---

### 3.14 `solver/prover/` (Automated Theorem Prover)

Searches for formal proofs of target formulas given a set of premises and axioms.

> **Architecture Decision (from review feedback):** Forward search over natural deduction rules suffers from infinite branching factors. The prover is split into two components:
> 1. A **primary resolution-based engine** operating on Clause Normal Form (CNF) for fast automated deduction.
> 2. A **natural deduction proof-reconstruction step** that converts the resolution trace into the human-readable `ProofDAG` and LEAN 4 tactics.
>
> The prover focuses on **FOL with Sorts**. SOL automated proving is deferred to Phase 9 and will be limited to explicit template instantiations rather than general higher-order proof search.

#### 3.14.1 `solver/prover/clausifier.py` — CNF Conversion

Converts formulas to Clause Normal Form for the resolution engine.

- `negate_and_clausify(formula: Formula) -> List[Clause]`: Negates a formula and converts to CNF (for refutation).
- `to_cnf(formula: Formula) -> List[Clause]`: Converts a formula to Clause Normal Form via:
  1. Elimination of `↔` and `⟹`.
  2. Pushing negations inward (NNF).
  3. Skolemization (replacing existential quantifiers with Skolem functions).
  4. Dropping universal quantifiers.
  5. Distribution (CNF conversion).
- `Clause(literals: FrozenSet[Literal])`: A disjunction of literals.
- `Literal(atom: PredicateApp, positive: bool)`: A signed atomic formula.

#### 3.14.2 `solver/prover/rules.py` — Inference Rules

Defines the proof calculus. The primary calculus is **resolution with equality** (superposition for equality reasoning).

**Core Resolution Rules:**
| Rule Name | Description |
|:---|:---|
| Binary Resolution | Resolve two clauses on complementary literals |
| Factoring | Merge duplicate literals within a clause |
| Paramodulation | Equality-based rewriting within clauses |

**Auxiliary rules for proof reconstruction:**
| Rule Name | Premises | Conclusion |
|:---|:---|:---|
| Modus Ponens | $A$, $A \implies B$ | $B$ |
| Universal Instantiation | $\forall x,\; \varphi(x)$ | $\varphi(t)$ for any well-sorted term $t$ |
| Existential Introduction | $\varphi(t)$ | $\exists x,\; \varphi(x)$ |
| And Introduction | $A$, $B$ | $A \land B$ |
| And Elimination | $A \land B$ | $A$ or $B$ |
| Or Introduction | $A$ | $A \lor B$ |
| Or Elimination | $A \lor B$, $A \implies C$, $B \implies C$ | $C$ |
| Double Negation Elimination | $\neg\neg A$ | $A$ |

#### Classes & Functions in `rules.py`:
- `InferenceRule(name: str, apply: Callable)`: Dataclass wrapping a named inference rule.
- `get_resolution_rules() -> List[InferenceRule]`: Returns the core resolution rules.
- `get_reconstruction_rules() -> List[InferenceRule]`: Returns the natural deduction rules used for proof reconstruction.
- `apply_rule(rule: InferenceRule, premises: List[Formula], context: Dict) -> List[Formula]`: Applies a rule to premises, returning all possible conclusions.

#### 3.14.3 `solver/prover/proof.py` — Proof DAG

A proof is a **directed acyclic graph** where nodes are proof steps and edges point from premises to conclusions. Shared sub-proofs (e.g., the same lemma used in multiple branches) are represented once and referenced multiple times.

- Dataclass `ProofStep`:
  - `id: str` (unique identifier for referencing in the DAG)
  - `rule: InferenceRule` (the inference rule applied)
  - `premise_ids: List[str]` (IDs of the ProofSteps used as premises)
  - `conclusion: Formula`
  - `substitutions: Dict[Variable, Term]`
- Class `ProofDAG`:
  - `steps: Dict[str, ProofStep]` (all steps indexed by ID)
  - `root_id: str` (the ID of the final conclusion step)
  - `axiom_ids: Set[str]` (IDs of steps that are axioms/premises, i.e., have no premise_ids)
  - `add_step(step: ProofStep) -> None`: Adds a step to the DAG.
  - `get_step(step_id: str) -> ProofStep`: Retrieves a step by ID.
  - `to_dict() -> dict`: Serializes proof DAG for export and storage.
  - `from_dict(data: dict) -> ProofDAG`: Deserializes a proof DAG from a dictionary. (classmethod)
  - `is_valid() -> bool`: Verifies step-by-step logical validity by checking that each step's conclusion follows from its premises via the declared rule.
  - `topological_order() -> List[ProofStep]`: Returns steps in dependency order (leaves first).

#### 3.14.4 `solver/prover/engine.py` — Proof Search Engine

- Class `TheoremProver`:
  - `__init__(self, signature: Signature, config: SolverConfig)`: Initializes with the signature and configuration.
  - `prove(target: Formula, premises: List[Formula], max_steps: Optional[int] = None, timeout_sec: Optional[float] = None) -> ProofDAG`: Attempts to prove `target` from `premises` using **refutation-based resolution**:
    1. Clausify the negation of the target and the premises into CNF.
    2. Apply resolution, factoring, and paramodulation until the empty clause is derived (proof found) or the search space is exhausted.
    3. Extract the resolution trace.
    4. Reconstruct a natural deduction `ProofDAG` from the resolution trace.
    
    Parameters default to `config.prover_max_steps` and `config.prover_timeout_sec`. Raises `ProofTimeoutError` on timeout, `ProofSearchExhaustedError` if exhausted.

#### 3.14.5 `solver/prover/reconstruction.py` — Proof Reconstruction

Converts resolution traces into human-readable natural deduction proofs.

- `reconstruct_proof(resolution_trace: List[ResolutionStep], original_target: Formula, premises: List[Formula]) -> ProofDAG`: Converts a resolution refutation trace into a natural deduction `ProofDAG` suitable for export and human inspection.
- `simplify_proof(proof: ProofDAG) -> ProofDAG`: Removes redundant steps and simplifies the proof structure.

---

### 3.15 `solver/deducer/` (Hypothesis-Consequence Analyzer)

> **Addressing the Question in `todo.md` ("IS IT REDUNDANT?"):**
> **NO, the Deducer is NOT redundant relative to the Prover.**
> - The **Prover** finds a step-by-step proof path (`ProofDAG`) to establish whether a single target conclusion $C$ follows from premises $H$.
> - The **Deducer** performs network-level analysis across a collection of formulas:
>   1. Computes **transitive closures** of implications across hypotheses and consequences.
>   2. Identifies the **Minimal Premise Set** required to derive a specific target.
>   3. Detects **redundant hypotheses** that carry no causal weight in proving theorems.
>   4. Discovers logical equivalence classes ($A \iff B$) within the Knowledge Base.

> **Scalability Decision (from review feedback):** The dependency graph is built **incrementally from successful proofs** already found by the prover, rather than attempting $O(n^2)$ pairwise proofs. When a proof is found, its premise-conclusion relationships are registered as edges. Explicit pairwise analysis is available as an opt-in batch operation for small formula sets.

#### 3.15.1 `solver/deducer/graph.py` — Dependency Graph

- Class `DependencyGraph`:
  - `nodes: Dict[str, Formula]`: Named formulas as graph nodes.
  - `edges: List[Tuple[str, str, str]]`: Directed edges `(source_name, target_name, relationship)` where relationship is `"implies"`, `"equivalent"`, or `"depends"`.
  - `add_node(name: str, formula: Formula) -> None`: Adds a formula node.
  - `add_edge(source: str, target: str, relationship: str) -> None`: Adds a directed edge.
  - `register_proof(proof: ProofDAG, theorem_name: str) -> None`: Incrementally adds edges from a completed proof's premises to its conclusion.
  - `predecessors(name: str) -> List[str]`: Returns all direct predecessors of a node.
  - `successors(name: str) -> List[str]`: Returns all direct successors of a node.
  - `transitive_closure(name: str) -> Set[str]`: Computes all nodes reachable from the given node.
  - `to_dict() -> dict`: Serializes for export to graph visualizer.

#### 3.15.2 `solver/deducer/analyzer.py` — Analysis Functions

- `analyze_dependencies(formulas: List[Tuple[str, Formula]], prover: TheoremProver, pairwise: bool = False) -> DependencyGraph`: Builds a dependency graph. If `pairwise=True`, attempts all pairwise proofs (expensive). Otherwise, uses existing proof records from the database.
- `find_minimal_hypotheses(target: Formula, available_hypotheses: List[Formula], prover: TheoremProver) -> List[Formula]`: Reduces premises to the minimal sufficient subset for proving the target (greedy removal with re-proof).
- `detect_redundant_hypotheses(hypotheses: List[Formula], target: Formula, prover: TheoremProver) -> List[Formula]`: Identifies hypotheses that can be removed without losing provability.
- `compute_equivalence_classes(formulas: List[Tuple[str, Formula]], prover: TheoremProver) -> List[Set[str]]`: Groups logically equivalent formulas together (bidirectional implication).

---

### 3.16 `solver/exporters/` (LEAN 4 & HTML Graph Exporters)

#### 3.16.1 `solver/exporters/lean_exporter.py`

> **Scope Decision (from review feedback):** LEAN export is separated into three tiers of increasing difficulty:
> 1. **Formula export** (`export_formula`) — Translates formulas to LEAN 4 syntax. Practical early milestone.
> 2. **Theorem statement export** (`export_theorem_statement`) — Generates `theorem` stubs with `sorry` placeholders. Practical early milestone.
> 3. **Proof export** (`export_proof`) — Converts proofs to LEAN 4 tactic blocks. Uses standard Mathlib tactics (`simp`, `aesop`, `exact`, `have`, `apply`) and LEAN's built-in automation (`aesop` / `decide`) to close proofs, rather than line-by-line low-level translation.

- Class `LeanExporter`:
  - `__init__(self, lean_project_name: str = "Solver", universe_name: str = "u")`: Configures the exporter.
  - `export_preamble(imports: Optional[List[str]] = None) -> str`: Generates the LEAN 4 file header including `import` declarations (defaults to `Mathlib.Tactic`), `universe` declarations, and `namespace` opening.
  - `export_sort(sort: Sort) -> str`: Translates a `Sort` to a LEAN 4 type (e.g., `Nat → ℕ`, `Set(Nat) → Set ℕ`, `Ind → α`).
  - `export_formula(formula: Formula) -> str`: Translates a `Formula` AST into LEAN 4 syntax (e.g., `∀ (v0 : α), P v0 → Q v0`).
  - `export_theorem_statement(name: str, formula: Formula) -> str`: Generates a LEAN 4 `theorem` declaration with `sorry` as proof placeholder.
  - `export_proof(proof: ProofDAG) -> str`: Converts a `ProofDAG` into LEAN 4 tactic proof using structured tactic blocks (`theorem ... := by`, `have`, `apply`, `exact`, `simp`, `aesop`).
  - `export_file(file_path: str, theorems: List[Tuple[str, Formula, Optional[ProofDAG]]]) -> None`: Writes a complete `.lean` source file. Theorems without proofs get `sorry` placeholders.

#### 3.16.2 `solver/exporters/graph_exporter.py`

- Class `GraphExporter`:
  - `export_proof_to_html(proof: ProofDAG, output_path: str) -> None`: Generates a standalone interactive HTML file (using vis.js) rendering the proof DAG.
  - `export_dependency_network_to_html(graph: DependencyGraph, output_path: str) -> None`: Generates an interactive HTML visualization for dependency networks.

---

### 3.17 `solver/config.py` (Central Configuration)

- Dataclass `SolverConfig`:
  - `db_path: str = "solver_data.db"` — Path to the SQLite database file.
  - `explorer_max_depth: int = 4` — Maximum AST depth for generated formulas.
  - `explorer_batch_size: int = 50` — Number of candidates to generate per batch.
  - `explorer_top_k: int = 10` — Number of top candidates to select after ranking.
  - `explorer_strategy: str = "mixed"` — Default generation strategy.
  - `prover_max_steps: int = 1000` — Maximum proof search steps.
  - `prover_timeout_sec: float = 10.0` — Proof search timeout in seconds.
  - `log_level: str = "INFO"` — Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
  - `lean_mathlib_version: str = "latest"` — Target Mathlib version for LEAN export.
  - `@classmethod from_file(cls, path: str) -> SolverConfig`: Loads configuration from a TOML/JSON file.

---

### 3.18 `solver/utils/logging.py` (Logging)

Configures Python's `logging` module for the entire library.

- `setup_logging(config: SolverConfig) -> None`: Configures root logger with the verbosity level from config.
- All modules use `logger = logging.getLogger(__name__)` for hierarchical, filterable logging.
- Key events logged:
  - `DEBUG`: Individual proof steps, formula generation attempts, unification details.
  - `INFO`: Proof found/failed, explorer batch summaries, database operations.
  - `WARNING`: Near-timeout, large search spaces, sort compatibility fallbacks.
  - `ERROR`: Unrecoverable failures, database corruption.

---

### 3.19 `solver/utils/doc_generator.py` (Automated Documentation)

Per requirement: *functions must be documented with docstrings directly in the files, and documentation must be automatically generated from them*.

#### Functions to Implement in `doc_generator.py`:
- `extract_docstrings_from_module(module_path: str) -> List[Dict[str, str]]`: Inspects docstrings via Python's `ast` and `inspect` modules.
- `build_markdown_docs(source_dir: str, output_docs_dir: str) -> None`: Scans the `solver` codebase and rebuilds Markdown documentation files under `docs/api/`.

---

### 3.20 `solver/__main__.py` (CLI Entry Point)

Provides a command-line interface for running the solver pipeline end-to-end.

#### Commands:
- `python -m solver init [--db-path PATH]`: Initialize a new database and populate it with foundational axioms from `kb/`.
- `python -m solver explore [--strategy STR] [--depth N] [--count N] [--top-k N]`: Run the formula explorer and print top candidate formulas.
- `python -m solver prove FORMULA [--premises P1 P2 ...] [--timeout SEC]`: Attempt to prove a formula from given premises.
- `python -m solver analyze [--category CAT] [--pairwise]`: Run the deducer to analyze dependencies across known theorems.
- `python -m solver export lean [--output FILE] [--theorems T1 T2 ...] [--stubs-only]`: Export formulas/proofs to LEAN 4.
- `python -m solver export graph [--output FILE] [--type proof|dependency]`: Export proof or dependency graph to interactive HTML.
- `python -m solver docs [--output-dir DIR]`: Regenerate API documentation from docstrings.

Uses `argparse` for argument parsing. All commands respect `SolverConfig` (loaded from `solver.toml` if present, overridden by CLI flags).

---

## 4. Summary Table of Files and Responsibilities

| File Path | Primary Responsibility | Key Classes / Functions |
| :--- | :--- | :--- |
| `solver/__main__.py` | CLI entry point | `main`, `argparse` commands |
| `solver/config.py` | Central configuration | `SolverConfig` |
| `solver/core/ast.py` | AST representation & canonicalization (FOL) | `Term`, `Formula`, `Variable`, `VariableKind`, `canonicalize_bound_variables`, `free_variables` |
| `solver/core/sorts.py` | Sort / type system (with parameterized sorts) | `Sort`, `PrimitiveSort`, `ParameterizedSort`, `is_compatible`, `sort_of_term` |
| `solver/core/signature.py` | Symbol declarations | `Signature`, `FunctionDecl`, `PredicateDecl` |
| `solver/core/validator.py` | AST well-formedness checking | `validate_formula`, `validate_term`, `is_well_formed` |
| `solver/core/visitors.py` | Generic AST traversal framework | `ASTVisitor`, `ASTTransformer`, `DepthVisitor`, `SizeVisitor` |
| `solver/core/exceptions.py` | Error types | `ParseError`, `UnificationError`, `ProofTimeoutError`, `ValidationError`, `DatabaseError` |
| `solver/core/parser.py` | Parsing & string serialization | `parse_formula`, `to_string` |
| `solver/core/substitutions.py` | Variable replacement & FOL unification | `substitute_formula`, `unify_terms`, `unify_formulas`, `compose_substitutions` |
| `solver/core/equality.py` | Equality reasoning subsystem | `CongruenceClosure`, `equality_substitution` |
| `solver/core/rewriter.py` | Term/formula rewriting | `RewriteRule`, `rewrite`, `normalize` |
| `solver/core/database.py` | Persistent SQLite storage | `KnowledgeDatabase` |
| `solver/kb/equality.py` | Equality axioms | `get_equality_axioms` |
| `solver/kb/logic.py` | FOL axioms | `get_fol_axioms` |
| `solver/kb/numbers.py` | Peano axioms & basic arithmetic | `get_peano_axioms` |
| `solver/explorer/generator.py` | Semantically-guided formula generation | `FormulaExplorer`, `generate_candidates` |
| `solver/explorer/heuristics.py` | Multi-metric diversity scoring & redundancy checks | `calculate_diversity_scores`, `DiversityMetrics`, `composite_interestingness` |
| `solver/explorer/filter.py` | Seen/discarded formula hashset | `FormulaFilter` |
| `solver/prover/clausifier.py` | CNF conversion | `to_cnf`, `negate_and_clausify`, `Clause`, `Literal` |
| `solver/prover/rules.py` | Inference rules | `InferenceRule`, `get_resolution_rules`, `get_reconstruction_rules` |
| `solver/prover/engine.py` | Resolution-based proof search engine | `TheoremProver`, `prove` |
| `solver/prover/reconstruction.py` | Proof reconstruction from resolution traces | `reconstruct_proof`, `simplify_proof` |
| `solver/prover/proof.py` | Proof DAG data structure | `ProofStep`, `ProofDAG` |
| `solver/deducer/graph.py` | Dependency graph structure | `DependencyGraph` |
| `solver/deducer/analyzer.py` | Relationship & dependency analysis | `find_minimal_hypotheses`, `detect_redundant_hypotheses`, `compute_equivalence_classes` |
| `solver/exporters/lean_exporter.py` | Translation to LEAN 4 format | `LeanExporter`, `export_formula`, `export_theorem_statement`, `export_proof` |
| `solver/exporters/graph_exporter.py` | Interactive HTML graph visualization | `GraphExporter`, `export_proof_to_html` |
| `solver/utils/logging.py` | Logging configuration | `setup_logging` |
| `solver/utils/doc_generator.py` | Automated docstring extraction | `build_markdown_docs` |
| `solver/sol/ast_ext.py` | SOL AST nodes (Phase 9) | `PredicateVariable`, `FunctionVariable`, `ForallPred`, `ExistsPred` |
| `solver/sol/substitutions_ext.py` | Higher-order pattern unification (Phase 9) | `substitute_predicate`, `ho_pattern_unify` |
| `solver/sol/kb_ext.py` | SOL axioms (Phase 9) | `get_sol_axioms` |

---

## 5. Testing Strategy

### 5.1 Tooling
- **Framework**: `pytest` with `pytest-cov` for coverage reporting.
- **Property-based testing**: `hypothesis` library for generating random ASTs and verifying invariants.

### 5.2 Key Invariants to Test

| Module | Invariant | Test Type |
|:---|:---|:---|
| `parser` | Round-trip: `parse(to_string(f)) == f` for all formulas | Property-based |
| `parser` | Rejects malformed syntax with `ParseError` | Unit |
| `ast` | Canonicalization is idempotent: `canonicalize(canonicalize(f)) == canonicalize(f)` | Property-based |
| `ast` | Alpha-equivalent formulas have equal canonical forms | Property-based |
| `ast` | Alpha-equivalence preservation: canonicalization does not change the set of free variables | Property-based |
| `substitutions` | Substitution never captures bound variables | Property-based |
| `substitutions` | Substitution composition: `apply(compose(s1, s2), t) == apply(s1, apply(s2, t))` | Property-based |
| `substitutions` | Unification is commutative: `unify(a, b) == unify(b, a)` (up to ordering) | Property-based |
| `sorts` | Unification rejects sort-incompatible terms | Unit |
| `sorts` | Parameterized sort compatibility is recursive | Unit |
| `signature` | Registered symbols are retrievable; unknown symbols return None | Unit |
| `validator` | Detects arity mismatches, sort errors, unbound variables | Unit |
| `equality` | Congruence closure is transitive and reflexive | Unit + Property-based |
| `prover` | Soundness: if `prove(C, H)` succeeds, then `C` logically follows from `H` | Unit + integration |
| `prover` | `ProofDAG.is_valid()` returns `True` for all produced proofs | Integration |
| `clausifier` | CNF conversion preserves logical equivalence (via model checking on small domains) | Property-based |
| `reconstruction` | Reconstructed proofs pass `ProofDAG.is_valid()` | Integration |
| `proof` | Serialization round-trip: `ProofDAG.from_dict(dag.to_dict()) == dag` | Unit |
| `proof` | Proof minimization: simplified proof is still valid | Integration |
| `database` | Persistence: data survives close/reopen cycle | Integration |
| `database` | `contains_formula` recognizes alpha-equivalent formulas | Unit |
| `database` | Hash stability across Python versions (canonical hash is deterministic) | Unit |
| `database` | Corruption recovery: database handles interrupted writes | Integration |
| `explorer` | No duplicates: generated batch contains no alpha-equivalent pairs | Unit |
| `explorer` | Sort constraints: generated formulas are well-sorted | Property-based |
| `lean_exporter` | Exported LEAN formula syntax is parseable | Integration |
| `lean_exporter` | Exported theorem statements are syntactically valid | Integration |
| `deducer` | Minimal hypothesis set is indeed sufficient for proof | Integration |

### 5.3 Test Files
- `tests/conftest.py` — Shared fixtures: sample formulas, signatures, database setup/teardown, prover instances.
- `tests/test_ast.py` — AST construction, free/bound variables, canonicalization, depth/size.
- `tests/test_sorts.py` — Sort compatibility, sort inference, parameterized sorts.
- `tests/test_signature.py` — Symbol registration, lookup, merge.
- `tests/test_validator.py` — Arity, sort, well-formedness validation.
- `tests/test_visitors.py` — Visitor framework, traversal correctness.
- `tests/test_parser.py` — Parsing, round-trip, error cases, malformed input rejection.
- `tests/test_substitutions.py` — Substitution, capture avoidance, unification, occur-check, composition.
- `tests/test_equality.py` — Congruence closure, equality substitution, explain chains.
- `tests/test_rewriter.py` — Rewrite rules, normalization, fixed-point convergence.
- `tests/test_database.py` — Persistence, query, deduplication, indexed search, corruption recovery.
- `tests/test_explorer.py` — Generation strategies, diversity scoring, filter.
- `tests/test_clausifier.py` — CNF conversion, Skolemization, literal handling.
- `tests/test_rules.py` — Each inference rule in isolation.
- `tests/test_reconstruction.py` — Proof reconstruction from resolution traces.
- `tests/test_prover.py` — End-to-end proofs of known theorems, timeout handling.
- `tests/test_deducer.py` — Dependency analysis, minimal hypotheses, equivalence classes.
- `tests/test_exporters.py` — LEAN syntax validity (formula + statement tiers), HTML output structure.

---

## 6. Implementation Roadmap & Phases

> **Revised Roadmap (incorporating review feedback):** The phases are reordered to establish a solid first-order foundation before adding complex features. Each phase is independently testable and delivers value.

### Phase 1 — AST & Sort System
**Goal**: A working AST with parameterized sorts.

**Deliverables**:
- `ast.py`, `sorts.py`, `exceptions.py`
- Passing tests: `test_ast.py`, `test_sorts.py`

**Acceptance Criteria**:
- Can construct, hash, and compare FOL formulas.
- Parameterized sorts (`Set(Nat)`, `Pair(Nat, Bool)`) work correctly.
- Canonicalization of bound variables is idempotent and correct.
- Free variable identity is preserved through canonicalization.

**Dependencies**: None (foundational).

---

### Phase 2 — Signature & Validator
**Goal**: Symbol declarations and centralized AST validation.

**Deliverables**:
- `signature.py`, `validator.py`
- Passing tests: `test_signature.py`, `test_validator.py`

**Acceptance Criteria**:
- Signatures can declare and look up functions, predicates, constants, and sort constructors.
- Validator catches arity mismatches, sort errors, unbound variables, and malformed ASTs.

**Dependencies**: Phase 1.

---

### Phase 3 — Visitor Framework & Parser
**Goal**: Generic AST traversal and text ↔ AST conversion.

**Deliverables**:
- `visitors.py`, `parser.py`
- Passing tests: `test_visitors.py`, `test_parser.py`

**Acceptance Criteria**:
- Visitor framework correctly dispatches to all AST node types.
- Parser round-trips: `parse(to_string(f)) == f` for all valid formulas.
- Parser rejects malformed syntax with clear `ParseError` messages.

**Dependencies**: Phase 1, Phase 2.

---

### Phase 4 — Substitution & Unification
**Goal**: FOL substitution with capture avoidance, Robinson's unification, substitution composition.

**Deliverables**:
- `substitutions.py`
- Passing tests: `test_substitutions.py`

**Acceptance Criteria**:
- Substitution never captures bound variables (de Bruijn shift or explicit renaming).
- Unification is restricted to first-order terms and respects sorts.
- Substitution composition is correct: `apply(compose(s1, s2), t) == apply(s1, apply(s2, t))`.
- Occur-check prevents infinite terms.

**Dependencies**: Phase 1, Phase 3 (visitor framework).

---

### Phase 5 — Equality & Rewriting
**Goal**: Equality reasoning subsystem and term rewriting engine.

**Deliverables**:
- `equality.py`, `rewriter.py`
- Passing tests: `test_equality.py`, `test_rewriter.py`

**Acceptance Criteria**:
- Congruence closure correctly propagates equalities through function applications.
- Rewrite rules can normalize formulas to canonical forms.
- Equality explanation chains are valid.

**Dependencies**: Phase 1, Phase 4.

---

### Phase 6 — Knowledge Base & Database
**Goal**: Foundational axiom sets and persistent storage.

**Deliverables**:
- `kb/equality.py`, `kb/logic.py`, `kb/numbers.py`
- `database.py`
- CLI `init` command.
- Passing tests: `test_database.py`

**Acceptance Criteria**:
- All axioms parse correctly and are well-sorted.
- Database persists across process restarts.
- Indexed columns (`ast_hash`, `depth`, `size`, etc.) enable fast searches.
- `python -m solver init` creates a populated database.

**Dependencies**: Phase 3, Phase 4.

---

### Phase 7 — Prover
**Goal**: A working resolution-based theorem prover with proof reconstruction.

**Deliverables**:
- `prover/clausifier.py`, `prover/rules.py`, `prover/proof.py`, `prover/engine.py`, `prover/reconstruction.py`
- CLI `prove` command.
- Passing tests: `test_clausifier.py`, `test_rules.py`, `test_reconstruction.py`, `test_prover.py`

**Acceptance Criteria**:
- Can prove propositional tautologies, basic FOL theorems (e.g., $\forall x, P(x) \implies \exists x, P(x)$), and at least one non-trivial theorem from the Peano axioms.
- All produced proofs pass `ProofDAG.is_valid()`.
- Reconstructed natural deduction proofs are correct.
- Timeouts and exhaustion raise appropriate exceptions.

**Dependencies**: Phase 4, Phase 5, Phase 6.

---

### Phase 8 — Explorer
**Goal**: Semantically-guided formula generation with multi-metric diversity scoring.

**Deliverables**:
- `explorer/generator.py`, `explorer/heuristics.py`, `explorer/filter.py`
- CLI `explore` command.
- Passing tests: `test_explorer.py`

**Acceptance Criteria**:
- Generates well-sorted, non-trivial, deduplicated candidate formulas.
- Multiple generation strategies (axiom rewrite, proof frontier, saturation) produce qualitatively different candidates.
- Multi-metric diversity scores differentiate trivial from interesting formulas.
- Filter persists state across runs.

**Dependencies**: Phase 6, Phase 7.

---

### Phase 9 — Deducer
**Goal**: Network-level analysis of hypothesis-consequence relationships.

**Deliverables**:
- `deducer/graph.py`, `deducer/analyzer.py`
- CLI `analyze` command.
- Passing tests: `test_deducer.py`

**Acceptance Criteria**:
- Dependency graph is built incrementally from successful proofs.
- Correctly identifies minimal hypothesis sets for known theorems.
- Equivalence class detection is consistent with bidirectional proofs.
- Optional pairwise analysis available for small formula sets.

**Dependencies**: Phase 7 (uses the prover).

---

### Phase 10 — Exporters
**Goal**: LEAN 4 translation (formula + statement + proof tiers) and interactive HTML visualization.

**Deliverables**:
- `exporters/lean_exporter.py`, `exporters/graph_exporter.py`
- CLI `export` commands.
- Passing tests: `test_exporters.py`

**Acceptance Criteria**:
- Exported LEAN formula syntax is parseable.
- Exported theorem statements are syntactically valid LEAN 4.
- Proof export uses Mathlib tactics (`simp`, `aesop`, `exact`, `have`, `apply`).
- `--stubs-only` flag exports theorem stubs with `sorry`.
- HTML visualizations are interactive, self-contained, and render correctly in modern browsers.

**Dependencies**: Phase 7, Phase 9.

---

### Phase 11 — Second-Order Logic Extension
**Goal**: SOL AST nodes, higher-order pattern unification, and SOL axioms.

> **Scope Restriction (from review feedback):** SOL automated proving is limited to explicit template instantiation and higher-order pattern unification (Miller-Pfenning). General higher-order unification is undecidable and is not attempted.

**Deliverables**:
- `sol/ast_ext.py`, `sol/substitutions_ext.py`, `sol/kb_ext.py`
- Integration with existing prover for SOL template instantiation.

**Acceptance Criteria**:
- SOL AST nodes integrate cleanly with the FOL AST.
- Higher-order pattern unification works for patterns (variables applied to distinct bound variables).
- SOL Comprehension Schema can be instantiated via explicit template matching.
- SOL axioms are well-formed and stored in the database.

**Dependencies**: All previous phases.

---

### Phase 12 — Extended Knowledge Base
**Goal**: Additional axiom domains beyond the initial core.

**Deliverables**:
- `kb/groups.py`, `kb/relations.py`, `kb/orders.py`, `kb/sets.py` (minimal, not full ZFC), `kb/functions.py`

**Acceptance Criteria**:
- All axioms are well-sorted and parseable.
- Prover can derive at least one non-trivial theorem from each new axiom domain.

**Dependencies**: Phase 7, Phase 11 (for set theory axioms using SOL).

---

### Phase 13 — Documentation, Logging & Polish
**Goal**: Complete documentation, logging, and CLI polish.

**Deliverables**:
- `utils/logging.py`, `utils/doc_generator.py`, `__main__.py` (final polish)
- Generated `docs/` directory.
- Full `pytest` coverage report.

**Acceptance Criteria**:
- All public functions have docstrings.
- `python -m solver docs` produces correct Markdown documentation.
- Test coverage ≥ 85%.
- All CLI commands work end-to-end with clear help text.

**Dependencies**: All previous phases.
