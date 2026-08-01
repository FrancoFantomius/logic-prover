# API Reference: `explorer`

# Module `solver.explorer.filter`

Diversity filter and Bloom-style formula deduplication filter.

---

## Table of Contents
- [Classes](#classes)

---

## Classes

### `class FormulaFilter`

Maintains a set of canonical formula hashes representing already explored, proven, or discarded formulas to prevent duplicate generation. Supports state persistence to disk (JSON formatted hash store).

#### Methods

##### `def __init__(self, storage_path: Optional[str]) -> None`

Initializes the formula deduplication filter and optionally loads state from storage.

**Returns:** `None`

##### `def add(self, formula: Formula) -> None`

Adds formula's canonical hash to the seen filter set.

**Returns:** `None`

##### `def is_seen(self, formula: Formula) -> bool`

Returns True if formula (or an alpha-equivalent variant) has been seen.

**Returns:** `bool`

##### `def save_state(self, filepath: Optional[str]) -> None`

Persists seen hashes and metadata to disk in JSON format.

**Returns:** `None`

##### `def load_state(self, filepath: str) -> None`

Loads seen hashes from a persisted JSON state file.

**Returns:** `None`

##### `def clear(self) -> None`

Clears all stored hashes from the filter.

**Returns:** `None`


---

# Module `solver.explorer.generator`

Formula generator engine implementing diverse candidate exploration strategies.

---

## Table of Contents
- [Classes](#classes)
- [Functions](#functions)

---

## Classes

### `class FormulaExplorer`

Semantically-guided Formula Explorer engine. Generates, evaluates, ranks, and filters candidate conjectures.

#### Methods

##### `def __init__(self, db: KnowledgeDatabase, signature: Signature, config: SolverConfig, prover: Optional[TheoremProver], filter_path: Optional[str]) -> None`

Initializes the candidate formula explorer with database, signature, config, and prover components.

**Returns:** `None`

##### `def generate_candidates(self, strategy: str, max_depth: Optional[int], count: Optional[int]) -> List[Formula]`

Generates candidate formulas using specified semantic strategy: - 'axiom_rewrite': Rewriting & instantiating known axioms. - 'proof_frontier': Extracting & generalizing intermediate proof steps. - 'anti_unification': Computing MSG generalization of theorem pairs. - 'saturation': Bounded resolution/paramodulation inference on seed axioms. - 'lemma_combination': Linking lemmas via implication, conjunction, quantifiers. - 'mixed': Proportionally mixes all strategies.

**Returns:** `List[Formula]`

##### `def rank_and_select(self, candidates: List[Formula], top_k: Optional[int]) -> List[Formula]`

Ranks candidate formulas by multi-metric diversity scores and composite interestingness, filtering out previously seen formulas from FormulaFilter. Adds selected top candidates to the filter state.

**Returns:** `List[Formula]`

---

## Functions

### `def anti_unify_terms(t1: Term, t2: Term, bindings: Dict[Tuple[Term, Term], Variable], var_counter: List[int]) -> Term`

Computes Most Specific Generalization (MSG) of two terms t1 and t2: - If t1 == t2: returns t1 - If t1 = f(s1...sk) and t2 = f(u1...uk) with same func symbol: returns f(anti_unify(s1, u1)...) - Otherwise: assigns or reuses fresh Variable for pair (t1, t2)

**Returns:** `Term`

### `def anti_unify_formulas(f1: Formula, f2: Formula, bindings: Optional[Dict[Tuple[Term, Term], Variable]], var_counter: Optional[List[int]]) -> Optional[Formula]`

Computes Most Specific Generalization (MSG) of two formulas f1 and f2: - If structural connectives/predicates match: anti-unifies recursively. - Universally quantifies all fresh generalization variables introduced. Returns generalized closed formula, or None if structural mismatch is irreconcilable.

**Returns:** `Optional[Formula]`


---

# Module `solver.explorer.heuristics`

Diversity metrics and formula interestingness heuristic scoring.

---

## Table of Contents
- [Classes](#classes)
- [Functions](#functions)

---

## Classes

### `class DiversityMetrics`

#### Methods

##### `def to_dict(self) -> Dict[str, Any]`

Converts metrics to dictionary representation for logging/JSON export.

**Returns:** `Dict[str, Any]`

### `class SymbolCollectorVisitor(ASTVisitor[None])`

Collects symbol occurrences and frequencies across a formula AST.

#### Methods

##### `def __init__(self) -> None`

Initializes state for tracking symbol frequencies, predicate sets, and quantifier depth.

**Returns:** `None`

##### `def visit_variable(self, node: Variable) -> None`

**Returns:** `None`

##### `def visit_constant(self, node: Constant) -> None`

**Returns:** `None`

##### `def visit_function_app(self, node: FunctionApp) -> None`

**Returns:** `None`

##### `def visit_predicate_app(self, node: PredicateApp) -> None`

**Returns:** `None`

##### `def visit_equality(self, node: Equality) -> None`

**Returns:** `None`

##### `def visit_not(self, node: Not) -> None`

**Returns:** `None`

##### `def visit_and(self, node: And) -> None`

**Returns:** `None`

##### `def visit_or(self, node: Or) -> None`

**Returns:** `None`

##### `def visit_implies(self, node: Implies) -> None`

**Returns:** `None`

##### `def visit_iff(self, node: Iff) -> None`

**Returns:** `None`

##### `def visit_forall(self, node: Forall) -> None`

**Returns:** `None`

##### `def visit_exists(self, node: Exists) -> None`

**Returns:** `None`

---

## Functions

### `def calculate_symbol_entropy(formula: Formula) -> float`

Computes the Shannon Entropy H(F) of symbol usage across a formula: H(F) = - sum_{s} p(s) * log2(p(s)) where p(s) = count(s) / total_symbols. High entropy indicates rich, non-repetitive symbol distribution.

**Returns:** `float`

### `def calculate_subtree_penalty(formula: Formula) -> float`

Scans the formula AST for identical subtrees of size >= 2. Applies an exponential penalty sum for each repeated subtree: penalty = sum_{sub, count > 1} (count - 1) * 0.5 * log2(size)

**Returns:** `float`

### `def calculate_diversity_scores(formula: Formula, proof_distance: Optional[int]) -> DiversityMetrics`

Calculates multi-metric diversity scores for a candidate formula.

**Returns:** `DiversityMetrics`

### `def composite_interestingness(metrics: DiversityMetrics, weights: Optional[Dict[str, float]]) -> float`

Combines individual metrics into a normalized scalar composite score: Score = w_entropy * symbol_entropy + w_pred * predicate_diversity + w_quant * quantifier_depth + w_reuse * log(variable_reuse) - w_penalty * repeated_subtree_penalty + size_bonus - size_penalty

**Returns:** `float`

### `def is_redundant_structure(formula: Formula) -> bool`

Syntactically identifies trivial tautologies, redundant self-concatenations, and vacuous formulas: 1. Self-equality: t = t 2. Self-implication: A => A 3. Self-conjunction / disjunction: A ∧ A, A ∨ A 4. Self-equivalence: A <=> A 5. Direct contradiction conjunct: A ∧ ¬A 6. Double negation: ¬¬A 7. Vacuous quantification: ∀x A or ∃x A where x not free in A

**Returns:** `bool`


---
