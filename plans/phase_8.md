# Phase 8 — Explorer Implementation Plan

**Goal**: Implement semantically-guided candidate formula generation with multi-metric diversity scoring, structural redundancy filtering, state persistence, and the CLI `explore` command.

**Deliverables**:
- [solver/explorer/__init__.py](file:///C:/Users/franc/Programmazione/solver/solver/explorer/__init__.py)
- [solver/explorer/heuristics.py](file:///C:/Users/franc/Programmazione/solver/solver/explorer/heuristics.py)
- [solver/explorer/filter.py](file:///C:/Users/franc/Programmazione/solver/solver/explorer/filter.py)
- [solver/explorer/generator.py](file:///C:/Users/franc/Programmazione/solver/solver/explorer/generator.py)
- CLI `explore` command in [solver/__main__.py](file:///C:/Users/franc/Programmazione/solver/solver/__main__.py)
- Passing test suite: [tests/test_explorer.py](file:///C:/Users/franc/Programmazione/solver/tests/test_explorer.py)

---

## 1. Overview & Architectural Goals

Phase 8 introduces the **Formula Explorer**, a subsystem responsible for discovering non-trivial, interesting, and novel conjecture formulas from existing knowledge bases and proof histories.

As highlighted in Section 3.13 of the master plan, pure weighted Context-Free Grammar (CFG) generation over AST node types produces mostly syntactically valid but semantically uninteresting or trivial formulas (e.g., $P(x) \lor \neg P(x)$, $P(x) \land P(x) \land P(x)$). To overcome this limitation, the Explorer relies on **semantically-guided generation strategies** coupled with **multi-metric diversity heuristics** and stateful **hash-based filtering**:

1. **Semantically-Guided Generation Strategies**: Rather than random AST sampling, candidates are derived by rewriting axioms, extracting intermediate lemmas from proof DAG frontiers, computing First-Order Anti-Unification (Most Specific Generalizations), performing bounded saturation via inference rules, and combining existing lemmas.
2. **Multi-Metric Diversity Scoring**: Evaluates candidate quality across independent structural dimensions—including Shannon symbol entropy, AST size, predicate diversity, quantifier depth, variable reuse ratio, repeated subtree penalties, and proof distance—combining them into a composite interestingness score.
3. **Redundancy & State Filtering**: Detects structural tautologies and trivial self-concatenations (`is_redundant_structure`), canonicalizes bound variables, and maintains a persistent hash filter (`FormulaFilter`) to guarantee deduplication across exploration runs.

---

## 2. Prerequisites

The following modules must be completed and fully passing unit/integration tests prior to Phase 8:

1. **Phase 1 — AST & Sort System**:
   - [solver/core/ast.py](file:///C:/Users/franc/Programmazione/solver/solver/core/ast.py): `Term`, `Variable`, `Constant`, `FunctionApp`, `Formula`, `PredicateApp`, `Equality`, `Not`, `And`, `Or`, `Implies`, `Iff`, `Forall`, `Exists`, `free_variables()`, `bound_variables()`, `canonicalize_bound_variables()`, `formula_depth()`, `formula_size()`.
   - [solver/core/sorts.py](file:///C:/Users/franc/Programmazione/solver/solver/core/sorts.py): `Sort`, `PrimitiveSort`, `is_compatible()`, `sort_of_term()`.
2. **Phase 2 — Signature & Validator**:
   - [solver/core/signature.py](file:///C:/Users/franc/Programmazione/solver/solver/core/signature.py): `Signature`.
   - [solver/core/validator.py](file:///C:/Users/franc/Programmazione/solver/solver/core/validator.py): `validate_formula()`, `is_well_formed()`.
3. **Phase 3 — Visitor Framework & Parser**:
   - [solver/core/visitors.py](file:///C:/Users/franc/Programmazione/solver/solver/core/visitors.py): `ASTVisitor`, `ASTTransformer`.
   - [solver/core/parser.py](file:///C:/Users/franc/Programmazione/solver/solver/core/parser.py): `parse_formula()`, `to_string()`.
4. **Phase 4 — Substitution & Unification**:
   - [solver/core/substitutions.py](file:///C:/Users/franc/Programmazione/solver/solver/core/substitutions.py): `substitute_term()`, `substitute_formula()`, `unify_terms()`, `unify_formulas()`.
5. **Phase 5 — Equality & Rewriting**:
   - [solver/core/rewriter.py](file:///C:/Users/franc/Programmazione/solver/solver/core/rewriter.py): `RewriteRule`, `rewrite_all()`, `normalize()`.
6. **Phase 6 — Knowledge Base & Database**:
   - [solver/core/database.py](file:///C:/Users/franc/Programmazione/solver/solver/core/database.py): `KnowledgeDatabase`.
   - [solver/kb/logic.py](file:///C:/Users/franc/Programmazione/solver/solver/kb/logic.py), [solver/kb/equality.py](file:///C:/Users/franc/Programmazione/solver/solver/kb/equality.py), [solver/kb/numbers.py](file:///C:/Users/franc/Programmazione/solver/solver/kb/numbers.py).
7. **Phase 7 — Prover**:
   - [solver/prover/engine.py](file:///C:/Users/franc/Programmazione/solver/solver/prover/engine.py): `TheoremProver`.
   - [solver/prover/clausifier.py](file:///C:/Users/franc/Programmazione/solver/solver/prover/clausifier.py): `to_cnf()`, `Clause`, `Literal`.
   - [solver/prover/rules.py](file:///C:/Users/franc/Programmazione/solver/solver/prover/rules.py): `get_resolution_rules()`, `resolve_clauses()`, `paramodulate()`, `factor_clause()`.
   - [solver/prover/proof.py](file:///C:/Users/franc/Programmazione/solver/solver/prover/proof.py): `ProofDAG`, `ProofStep`.

---

## 3. Files to Create / Modify

| File Path | Action | Description |
| :--- | :--- | :--- |
| [solver/explorer/__init__.py](file:///C:/Users/franc/Programmazione/solver/solver/explorer/__init__.py) | Create | Package initialization and public API exports |
| [solver/explorer/heuristics.py](file:///C:/Users/franc/Programmazione/solver/solver/explorer/heuristics.py) | Create | `DiversityMetrics`, `calculate_symbol_entropy`, `calculate_diversity_scores`, `composite_interestingness`, `is_redundant_structure` |
| [solver/explorer/filter.py](file:///C:/Users/franc/Programmazione/solver/solver/explorer/filter.py) | Create | `FormulaFilter` class with hash-based set storage, state persistence (`save_state`, `load_state`), and canonical lookup |
| [solver/explorer/generator.py](file:///C:/Users/franc/Programmazione/solver/solver/explorer/generator.py) | Create | `FormulaExplorer` class with 5 semantically-guided generation strategies, anti-unification algorithm, ranking, and selection |
| [solver/__main__.py](file:///C:/Users/franc/Programmazione/solver/solver/__main__.py) | Update | Add `explore` CLI subcommand and formatting handler |
| [tests/test_explorer.py](file:///C:/Users/franc/Programmazione/solver/tests/test_explorer.py) | Create | Comprehensive unit, property-based (sort constraints), strategy comparison, and filter persistence tests |

---

## 4. Detailed Module Specifications

### 4.1 `solver/explorer/heuristics.py` (Section 3.13)

Evaluates candidate formula quality across independent metrics and detects syntactically redundant structures.

```python
import math
from dataclasses import dataclass
from typing import Dict, Set, Optional, Tuple, Any, List
from solver.core.ast import (
    Formula, Term, Variable, Constant, FunctionApp,
    PredicateApp, Equality, Not, And, Or, Implies, Iff, Forall, Exists,
    free_variables, bound_variables, formula_size, formula_depth
)
from solver.core.visitors import ASTVisitor

@dataclass(frozen=True)
class DiversityMetrics:
    ast_size: int
    symbol_entropy: float
    predicate_diversity: int
    quantifier_depth: int
    variable_reuse: float
    repeated_subtree_penalty: float
    proof_distance: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converts metrics to dictionary representation for logging/JSON export."""
        return {
            "ast_size": self.ast_size,
            "symbol_entropy": round(self.symbol_entropy, 4),
            "predicate_diversity": self.predicate_diversity,
            "quantifier_depth": self.quantifier_depth,
            "variable_reuse": round(self.variable_reuse, 4),
            "repeated_subtree_penalty": round(self.repeated_subtree_penalty, 4),
            "proof_distance": self.proof_distance,
        }


class SymbolCollectorVisitor(ASTVisitor[None]):
    """Collects symbol occurrences and frequencies across a formula AST."""

    def __init__(self) -> None:
        self.counts: Dict[str, int] = {}
        self.total_symbols: int = 0
        self.predicates: Set[str] = set()
        self.quantifier_depth: int = 0
        self.max_quantifier_depth: int = 0
        self.variable_references: int = 0

    def _record_symbol(self, symbol: str) -> None:
        self.counts[symbol] = self.counts.get(symbol, 0) + 1
        self.total_symbols += 1

    def visit_variable(self, node: Variable) -> None:
        self._record_symbol(f"Var_{node.id}")
        self.variable_references += 1

    def visit_constant(self, node: Constant) -> None:
        self._record_symbol(f"Const_{node.name}")

    def visit_function_app(self, node: FunctionApp) -> None:
        self._record_symbol(f"Func_{node.func}")
        for arg in node.args:
            self.visit(arg)

    def visit_predicate_app(self, node: PredicateApp) -> None:
        self._record_symbol(f"Pred_{node.pred}")
        self.predicates.add(node.pred)
        for arg in node.args:
            self.visit(arg)

    def visit_equality(self, node: Equality) -> None:
        self._record_symbol("Op_Eq")
        self.visit(node.left)
        self.visit(node.right)

    def visit_not(self, node: Not) -> None:
        self._record_symbol("Op_Not")
        self.visit(node.operand)

    def visit_and(self, node: And) -> None:
        self._record_symbol("Op_And")
        self.visit(node.left)
        self.visit(node.right)

    def visit_or(self, node: Or) -> None:
        self._record_symbol("Op_Or")
        self.visit(node.left)
        self.visit(node.right)

    def visit_implies(self, node: Implies) -> None:
        self._record_symbol("Op_Implies")
        self.visit(node.left)
        self.visit(node.right)

    def visit_iff(self, node: Iff) -> None:
        self._record_symbol("Op_Iff")
        self.visit(node.left)
        self.visit(node.right)

    def visit_forall(self, node: Forall) -> None:
        self._record_symbol("Op_Forall")
        self.quantifier_depth += 1
        if self.quantifier_depth > self.max_quantifier_depth:
            self.max_quantifier_depth = self.quantifier_depth
        self.visit(node.variable)
        self.visit(node.body)
        self.quantifier_depth -= 1

    def visit_exists(self, node: Exists) -> None:
        self._record_symbol("Op_Exists")
        self.quantifier_depth += 1
        if self.quantifier_depth > self.max_quantifier_depth:
            self.max_quantifier_depth = self.quantifier_depth
        self.visit(node.variable)
        self.visit(node.body)
        self.quantifier_depth -= 1


def calculate_symbol_entropy(formula: Formula) -> float:
    """
    Computes the Shannon Entropy H(F) of symbol usage across a formula:
    H(F) = - sum_{s} p(s) * log2(p(s))
    where p(s) = count(s) / total_symbols.
    High entropy indicates rich, non-repetitive symbol distribution.
    """
    collector = SymbolCollectorVisitor()
    collector.visit(formula)

    if collector.total_symbols == 0:
        return 0.0

    entropy = 0.0
    for count in collector.counts.values():
        p = count / collector.total_symbols
        if p > 0:
            entropy -= p * math.log2(p)

    return entropy


def calculate_subtree_penalty(formula: Formula) -> float:
    """
    Scans the formula AST for identical subtrees of size >= 2.
    Applies an exponential penalty sum for each repeated subtree:
    penalty = sum_{sub, count > 1} (count - 1) * 0.5
    """
    subtree_counts: Dict[Formula, int] = {}

    def collect_subtrees(node: Formula) -> None:
        if formula_size(node) >= 2:
            subtree_counts[node] = subtree_counts.get(node, 0) + 1

        if isinstance(node, Not):
            collect_subtrees(node.operand)
        elif isinstance(node, (And, Or, Implies, Iff)):
            collect_subtrees(node.left)
            collect_subtrees(node.right)
        elif isinstance(node, (Forall, Exists)):
            collect_subtrees(node.body)

    collect_subtrees(formula)

    penalty = 0.0
    for node, count in subtree_counts.items():
        if count > 1:
            penalty += (count - 1) * 0.5 * math.log2(formula_size(node))

    return penalty


def calculate_diversity_scores(
    formula: Formula,
    proof_distance: Optional[int] = None
) -> DiversityMetrics:
    """
    Calculates multi-metric diversity scores for a candidate formula.
    """
    collector = SymbolCollectorVisitor()
    collector.visit(formula)

    size = formula_size(formula)
    entropy = calculate_symbol_entropy(formula)
    pred_div = len(collector.predicates)
    q_depth = collector.max_quantifier_depth

    all_vars = free_variables(formula) | bound_variables(formula)
    distinct_var_count = len(all_vars)
    if distinct_var_count > 0:
        var_reuse = collector.variable_references / distinct_var_count
    else:
        var_reuse = 1.0

    penalty = calculate_subtree_penalty(formula)

    return DiversityMetrics(
        ast_size=size,
        symbol_entropy=entropy,
        predicate_diversity=pred_div,
        quantifier_depth=q_depth,
        variable_reuse=var_reuse,
        repeated_subtree_penalty=penalty,
        proof_distance=proof_distance
    )


def composite_interestingness(
    metrics: DiversityMetrics,
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Combines individual metrics into a normalized scalar composite score:
    Score = w_entropy * symbol_entropy 
          + w_pred * predicate_diversity 
          + w_quant * quantifier_depth 
          + w_reuse * log(variable_reuse) 
          - w_penalty * repeated_subtree_penalty
          + size_bonus - size_penalty
    """
    default_weights = {
        "entropy": 2.5,
        "predicate": 1.5,
        "quantifier": 1.0,
        "var_reuse": 1.2,
        "penalty": 2.0,
        "proof_distance": 0.5,
    }
    w = {**default_weights, **(weights or {})}

    # AST Size bell curve preference: ideal size between 4 and 15
    if metrics.ast_size < 3:
        size_score = -2.0  # Too trivial
    elif 3 <= metrics.ast_size <= 15:
        size_score = 1.0
    else:
        size_score = max(-3.0, 1.0 - (metrics.ast_size - 15) * 0.2)  # Oversized AST penalty

    score = size_score
    score += w["entropy"] * metrics.symbol_entropy
    score += w["predicate"] * metrics.predicate_diversity
    score += w["quantifier"] * metrics.quantifier_depth
    score += w["var_reuse"] * math.log(metrics.variable_reuse + 1.0)
    score -= w["penalty"] * metrics.repeated_subtree_penalty

    if metrics.proof_distance is not None:
        score += w["proof_distance"] * metrics.proof_distance

    return round(score, 4)


def is_redundant_structure(formula: Formula) -> bool:
    """
    Syntactically identifies trivial tautologies, redundant self-concatenations,
    and vacuous formulas:
    1. Self-equality: t = t
    2. Self-implication: A => A
    3. Self-conjunction / disjunction: A ∧ A, A ∨ A
    4. Self-equivalence: A <=> A
    5. Direct contradiction conjunct: A ∧ ¬A
    6. Double negation: ¬¬A
    7. Vacuous quantification: ∀x A or ∃x A where x not free in A
    """
    if isinstance(formula, Equality):
        if formula.left == formula.right:
            return True

    elif isinstance(formula, Implies):
        if formula.left == formula.right:
            return True
        if is_redundant_structure(formula.left) or is_redundant_structure(formula.right):
            return True

    elif isinstance(formula, (And, Or)):
        if formula.left == formula.right:
            return True
        # Check for A ∧ ¬A or A ∨ ¬A
        if isinstance(formula.right, Not) and formula.right.operand == formula.left:
            return True
        if isinstance(formula.left, Not) and formula.left.operand == formula.right:
            return True
        if is_redundant_structure(formula.left) or is_redundant_structure(formula.right):
            return True

    elif isinstance(formula, Iff):
        if formula.left == formula.right:
            return True
        if is_redundant_structure(formula.left) or is_redundant_structure(formula.right):
            return True

    elif isinstance(formula, Not):
        if isinstance(formula.operand, Not):  # ¬¬A
            return True
        if is_redundant_structure(formula.operand):
            return True

    elif isinstance(formula, (Forall, Exists)):
        free_in_body = free_variables(formula.body)
        if formula.variable not in free_in_body:  # Vacuous binder
            return True
        if is_redundant_structure(formula.body):
            return True

    return False
```

#### Implementation Notes & Algorithms
- **Shannon Symbol Entropy**: Uses `SymbolCollectorVisitor` to traverse all node kinds. A formula with high entropy mixes distinct predicates, function symbols, and connectives without leaning on repetitive AST patterns.
- **Subtree Penalty**: Computes canonical forms of subtrees and penalizes identical repeated subexpressions exponentially ($0.5 \times (k-1) \log_2(\text{size})$).
- **Vacuous Quantifier Detection**: Quantifiers binding variables that do not appear free in the body are flagged as redundant (`is_redundant_structure` returns `True`).

---

### 4.2 `solver/explorer/filter.py` (Section 3.13)

Provides hash-based deduplication and persistent storage across exploration runs.

```python
import json
import hashlib
import os
from typing import Set, Optional, Dict, Any
from solver.core.ast import Formula, canonicalize_bound_variables
from solver.core.exceptions import SolverError, DatabaseError

class FormulaFilter:
    """
    Maintains a set of canonical formula hashes representing already explored,
    proven, or discarded formulas to prevent duplicate generation.
    Supports state persistence to disk (JSON formatted hash store).
    """

    def __init__(self, storage_path: Optional[str] = None) -> None:
        self.seen_hashes: Set[str] = set()
        self.storage_path: Optional[str] = storage_path
        if self.storage_path and os.path.exists(self.storage_path):
            self.load_state(self.storage_path)

    def _compute_hash(self, formula: Formula) -> str:
        """
        Computes deterministic SHA-256 hash of canonicalized formula.
        Uses canonicalize_bound_variables to ensure alpha-equivalent formulas
        yield identical hashes.
        """
        canonical = canonicalize_bound_variables(formula)
        canonical_repr = repr(canonical)
        return hashlib.sha256(canonical_repr.encode("utf-8")).hexdigest()

    def add(self, formula: Formula) -> None:
        """Adds formula's canonical hash to the seen filter set."""
        h = self._compute_hash(formula)
        self.seen_hashes.add(h)

    def is_seen(self, formula: Formula) -> bool:
        """Returns True if formula (or an alpha-equivalent variant) has been seen."""
        h = self._compute_hash(formula)
        return h in self.seen_hashes

    def save_state(self, filepath: Optional[str] = None) -> None:
        """
        Persists seen hashes and metadata to disk in JSON format.
        """
        target_path = filepath or self.storage_path
        if not target_path:
            raise SolverError("Cannot save filter state: no storage_path provided.")

        dir_name = os.path.dirname(target_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        data: Dict[str, Any] = {
            "version": "1.0",
            "count": len(self.seen_hashes),
            "hashes": sorted(list(self.seen_hashes))
        }

        try:
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            raise DatabaseError(f"Failed to save filter state to '{target_path}': {e}")

    def load_state(self, filepath: str) -> None:
        """
        Loads seen hashes from a persisted JSON state file.
        """
        if not os.path.exists(filepath):
            raise DatabaseError(f"Filter state file not found: '{filepath}'")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            hashes = data.get("hashes", [])
            self.seen_hashes.update(hashes)
            self.storage_path = filepath
        except (json.JSONDecodeError, OSError) as e:
            raise DatabaseError(f"Failed to load filter state from '{filepath}': {e}")

    def clear(self) -> None:
        """Clears all stored hashes from the filter."""
        self.seen_hashes.clear()

    def __len__(self) -> int:
        return len(self.seen_hashes)
```

---

### 4.3 `solver/explorer/generator.py` (Section 3.13)

Implements semantically-guided formula generation strategies and First-Order Anti-Unification.

```python
import random
from typing import List, Dict, Set, Optional, Tuple, Any
from solver.config import SolverConfig
from solver.core.ast import (
    Formula, Term, Variable, Constant, FunctionApp, PredicateApp,
    Equality, Not, And, Or, Implies, Iff, Forall, Exists,
    free_variables, bound_variables, canonicalize_bound_variables, formula_depth
)
from solver.core.sorts import Sort, Ind
from solver.core.signature import Signature
from solver.core.validator import validate_formula
from solver.core.substitutions import substitute_formula, substitute_term
from solver.core.database import KnowledgeDatabase
from solver.core.rewriter import RewriteRule, rewrite_all
from solver.prover.engine import TheoremProver
from solver.prover.clausifier import to_cnf, Clause, Literal
from solver.prover.rules import get_resolution_rules, resolve_clauses, paramodulate, factor_clause
from solver.explorer.heuristics import (
    calculate_diversity_scores, composite_interestingness, is_redundant_structure, DiversityMetrics
)
from solver.explorer.filter import FormulaFilter

# --- First-Order Anti-Unification Helper Functions ---

def anti_unify_terms(
    t1: Term,
    t2: Term,
    bindings: Dict[Tuple[Term, Term], Variable],
    var_counter: List[int]
) -> Term:
    """
    Computes Most Specific Generalization (MSG) of two terms t1 and t2:
    - If t1 == t2: returns t1
    - If t1 = f(s1...sk) and t2 = f(u1...uk) with same func symbol: returns f(anti_unify(s1, u1)...)
    - Otherwise: assigns or reuses fresh Variable for pair (t1, t2)
    """
    if t1 == t2:
        return t1

    if (
        isinstance(t1, FunctionApp) and isinstance(t2, FunctionApp)
        and t1.func == t2.func and t1.arity == t2.arity
    ):
        new_args = tuple(
            anti_unify_terms(a1, a2, bindings, var_counter)
            for a1, a2 in zip(t1.args, t2.args)
        )
        return FunctionApp(func=t1.func, arity=t1.arity, args=new_args, return_sort=t1.return_sort)

    pair = (t1, t2)
    if pair not in bindings:
        v_id = var_counter[0]
        var_counter[0] += 1
        bindings[pair] = Variable(id=v_id, sort=t1.sort if hasattr(t1, 'sort') else Ind)

    return bindings[pair]


def anti_unify_formulas(
    f1: Formula,
    f2: Formula,
    bindings: Optional[Dict[Tuple[Term, Term], Variable]] = None,
    var_counter: Optional[List[int]] = None
) -> Optional[Formula]:
    """
    Computes Most Specific Generalization (MSG) of two formulas f1 and f2:
    - If structural connectives/predicates match: anti-unifies recursively.
    - Universally quantifies all fresh generalization variables introduced.
    Returns generalized closed formula, or None if structural mismatch is irreconcilable.
    """
    if bindings is None:
        bindings = {}
    if var_counter is None:
        # Start fresh var IDs above maximum ID in f1 and f2
        all_vars = free_variables(f1) | bound_variables(f1) | free_variables(f2) | bound_variables(f2)
        max_id = max((v.id for v in all_vars), default=-1)
        var_counter = [max_id + 1]

    def recurse(g1: Formula, g2: Formula) -> Optional[Formula]:
        if isinstance(g1, PredicateApp) and isinstance(g2, PredicateApp):
            if g1.pred == g2.pred and g1.arity == g2.arity:
                gen_args = tuple(
                    anti_unify_terms(a1, a2, bindings, var_counter)
                    for a1, a2 in zip(g1.args, g2.args)
                )
                return PredicateApp(pred=g1.pred, arity=g1.arity, args=gen_args)
            return None

        if isinstance(g1, Equality) and isinstance(g2, Equality):
            gen_left = anti_unify_terms(g1.left, g2.left, bindings, var_counter)
            gen_right = anti_unify_terms(g1.right, g2.right, bindings, var_counter)
            return Equality(left=gen_left, right=gen_right)

        if isinstance(g1, Not) and isinstance(g2, Not):
            inner = recurse(g1.operand, g2.operand)
            return Not(inner) if inner else None

        if isinstance(g1, And) and isinstance(g2, And):
            l = recurse(g1.left, g2.left)
            r = recurse(g1.right, g2.right)
            return And(l, r) if (l and r) else None

        if isinstance(g1, Or) and isinstance(g2, Or):
            l = recurse(g1.left, g2.left)
            r = recurse(g1.right, g2.right)
            return Or(l, r) if (l and r) else None

        if isinstance(g1, Implies) and isinstance(g2, Implies):
            l = recurse(g1.left, g2.left)
            r = recurse(g1.right, g2.right)
            return Implies(l, r) if (l and r) else None

        if isinstance(g1, Iff) and isinstance(g2, Iff):
            l = recurse(g1.left, g2.left)
            r = recurse(g1.right, g2.right)
            return Iff(l, r) if (l and r) else None

        return None

    raw_gen = recurse(f1, f2)
    if not raw_gen:
        return None

    # Universally quantify newly introduced generalization variables
    gen_vars = set(bindings.values())
    result = raw_gen
    for gv in sorted(gen_vars, key=lambda v: v.id, reverse=True):
        result = Forall(variable=gv, body=result)

    return result


class FormulaExplorer:
    """
    Semantically-guided Formula Explorer engine.
    Generates, evaluates, ranks, and filters candidate conjectures.
    """

    def __init__(
        self,
        db: KnowledgeDatabase,
        signature: Signature,
        config: SolverConfig,
        prover: Optional[TheoremProver] = None,
        filter_path: Optional[str] = None
    ) -> None:
        self.db = db
        self.signature = signature
        self.config = config
        self.prover = prover or TheoremProver(signature=signature, config=config)
        self.filter = FormulaFilter(storage_path=filter_path or config.db_path + ".filter.json")
        self.rewrite_rules: List[RewriteRule] = []

    def generate_candidates(
        self,
        strategy: str = "mixed",
        max_depth: Optional[int] = None,
        count: Optional[int] = None
    ) -> List[Formula]:
        """
        Generates candidate formulas using specified semantic strategy:
        - 'axiom_rewrite': Rewriting & instantiating known axioms.
        - 'proof_frontier': Extracting & generalizing intermediate proof steps.
        - 'anti_unification': Computing MSG generalization of theorem pairs.
        - 'saturation': Bounded resolution/paramodulation inference on seed axioms.
        - 'lemma_combination': Linking lemmas via implication, conjunction, quantifiers.
        - 'mixed': Proportionally mixes all strategies.
        """
        depth_limit = max_depth or self.config.explorer_max_depth
        target_count = count or self.config.explorer_batch_size

        candidates: List[Formula] = []

        if strategy == "axiom_rewrite":
            candidates = self._generate_axiom_rewrite(depth_limit, target_count)
        elif strategy == "proof_frontier":
            candidates = self._generate_proof_frontier(depth_limit, target_count)
        elif strategy == "anti_unification":
            candidates = self._generate_anti_unification(depth_limit, target_count)
        elif strategy == "saturation":
            candidates = self._generate_saturation(depth_limit, target_count)
        elif strategy == "lemma_combination":
            candidates = self._generate_lemma_combination(depth_limit, target_count)
        elif strategy == "mixed":
            per_strategy = max(1, target_count // 5)
            candidates.extend(self._generate_axiom_rewrite(depth_limit, per_strategy))
            candidates.extend(self._generate_proof_frontier(depth_limit, per_strategy))
            candidates.extend(self._generate_anti_unification(depth_limit, per_strategy))
            candidates.extend(self._generate_saturation(depth_limit, per_strategy))
            candidates.extend(self._generate_lemma_combination(depth_limit, per_strategy))
        else:
            raise ValueError(f"Unknown generation strategy: '{strategy}'")

        # Filter out ill-formed, oversized, or redundant formulas
        valid_candidates: List[Formula] = []
        for f in candidates:
            if formula_depth(f) > depth_limit:
                continue
            if not validate_formula(f, self.signature):
                continue
            if is_redundant_structure(f):
                continue
            valid_candidates.append(canonicalize_bound_variables(f))

        return valid_candidates

    def rank_and_select(
        self,
        candidates: List[Formula],
        top_k: Optional[int] = None
    ) -> List[Formula]:
        """
        Ranks candidate formulas by multi-metric diversity scores and composite
        interestingness, filtering out previously seen formulas from FormulaFilter.
        Adds selected top candidates to the filter state.
        """
        k = top_k or self.config.explorer_top_k
        unseen_candidates: List[Formula] = []

        for f in candidates:
            if not self.filter.is_seen(f):
                unseen_candidates.append(f)

        scored_candidates: List[Tuple[float, Formula]] = []
        for f in unseen_candidates:
            metrics = calculate_diversity_scores(f)
            score = composite_interestingness(metrics)
            scored_candidates.append((score, f))

        scored_candidates.sort(key=lambda item: item[0], reverse=True)

        selected = [f for score, f in scored_candidates[:k]]
        for f in selected:
            self.filter.add(f)

        return selected

    # --- Strategy Implementations ---

    def _generate_axiom_rewrite(self, max_depth: int, count: int) -> List[Formula]:
        """Strategy 1: Rewrite and instantiate existing KB axioms."""
        axioms = [form for name, form in self.db.get_axioms()]
        if not axioms:
            return []

        results: List[Formula] = []
        for ax in axioms:
            if len(results) >= count:
                break
            # Apply term/formula rewriting if rules available
            norm = rewrite_all(ax, self.rewrite_rules) if self.rewrite_rules else ax
            
            # Instantiate free variables with signature terms
            free_vars = list(free_variables(norm))
            if free_vars:
                subst: Dict[Variable, Term] = {}
                for v in free_vars:
                    # Pick constant or variable of matching sort
                    matching_consts = [
                        Constant(c, sort=s) for c, s in self.signature.constants.items()
                        if s == v.sort
                    ]
                    if matching_consts:
                        subst[v] = random.choice(matching_consts)
                instantiated = substitute_formula(norm, subst)
                results.append(instantiated)
            else:
                results.append(norm)

        return results

    def _generate_proof_frontier(self, max_depth: int, count: int) -> List[Formula]:
        """Strategy 2: Extract and generalize intermediate lemmas from proof DAGs."""
        theorems = self.db.get_theorems()
        results: List[Formula] = []

        for name, thm_formula in theorems:
            if len(results) >= count:
                break
            proof_dag = self.db.get_proof(name)
            if not proof_dag:
                continue

            for step in proof_dag.steps.values():
                if step.rule not in ("Axiom", "NegatedGoal", "DoubleNegationElimination"):
                    step_form = step.conclusion
                    if not is_redundant_structure(step_form):
                        results.append(step_form)

        return results

    def _generate_anti_unification(self, max_depth: int, count: int) -> List[Formula]:
        """Strategy 3: Compute Most Specific Generalization of theorem/axiom pairs."""
        formulas = [f for n, f in self.db.get_axioms()] + [f for n, f in self.db.get_theorems()]
        if len(formulas) < 2:
            return []

        results: List[Formula] = []
        for i in range(len(formulas)):
            for j in range(i + 1, len(formulas)):
                if len(results) >= count:
                    break
                gen = anti_unify_formulas(formulas[i], formulas[j])
                if gen and not is_redundant_structure(gen):
                    results.append(gen)

        return results

    def _generate_saturation(self, max_depth: int, count: int) -> List[Formula]:
        """Strategy 4: Exhaustive inference on small seed axiom sets via resolution/paramodulation."""
        axioms = [f for n, f in self.db.get_axioms()]
        if not axioms:
            return []

        seeds = axioms[:min(3, len(axioms))]
        clauses: List[Clause] = []
        for s in seeds:
            clauses.extend(to_cnf(s, signature=self.signature))

        derived_clauses: List[Clause] = list(clauses)
        for i in range(len(clauses)):
            for j in range(i + 1, len(clauses)):
                if len(derived_clauses) >= count + len(clauses):
                    break
                res_out = resolve_clauses(clauses[i], clauses[j])
                for r_clause, subst, lits in res_out:
                    if not r_clause.is_empty and not r_clause.is_tautology:
                        derived_clauses.append(r_clause)

        results: List[Formula] = []
        for c in derived_clauses[len(clauses):]:
            # Convert Clause back to Formula
            if c.is_unit:
                lit = list(c.literals)[0]
                f = lit.atom if lit.positive else Not(lit.atom)
            else:
                lits = list(c.literals)
                f = lits[0].atom if lits[0].positive else Not(lits[0].atom)
                for l in lits[1:]:
                    atom_f = l.atom if l.positive else Not(l.atom)
                    f = Or(f, atom_f)

            # Close free variables with Forall
            for v in sorted(free_variables(f), key=lambda x: x.id, reverse=True):
                f = Forall(variable=v, body=f)

            results.append(f)

        return results

    def _generate_lemma_combination(self, max_depth: int, count: int) -> List[Formula]:
        """Strategy 5: Combine existing lemmas via implications, conjunctions, quantifiers."""
        formulas = [f for n, f in self.db.get_axioms()] + [f for n, f in self.db.get_theorems()]
        if not formulas:
            return []

        results: List[Formula] = []
        for i in range(len(formulas)):
            for j in range(len(formulas)):
                if i == j or len(results) >= count:
                    continue
                f1, f2 = formulas[i], formulas[j]

                # Combination 1: Implication f1 => f2
                results.append(Implies(left=f1, right=f2))

                # Combination 2: Conjunction f1 ∧ f2
                results.append(And(left=f1, right=f2))

                # Combination 3: Equivalence f1 <=> f2
                results.append(Iff(left=f1, right=f2))

        return results
```

#### Anti-Unification Algorithm Specifications
First-order anti-unification finds the least general term/formula that generalizes two inputs:
$$\theta_1(t_g) = t_1 \quad \text{and} \quad \theta_2(t_g) = t_2$$
- `anti_unify_terms` checks structural equivalence recursively down to subterms. When symbols diverge, it maintains a binding map $(t_1, t_2) \mapsto v_{gen}$ so identical divergent pairs reuse the same generalization variable.
- `anti_unify_formulas` matches top-level logical connectives and atomic predicate signatures. When atomic predicates match ($P(s_1, \dots, s_k)$ and $P(u_1, \dots, u_k)$), args are recursively anti-unified. Fresh variables are bound at the outermost scope with universal quantifiers $\forall v_i$.

---

### 4.4 `solver/explorer/__init__.py`

Exposes public symbols for external usage.

```python
from solver.explorer.heuristics import (
    DiversityMetrics,
    calculate_symbol_entropy,
    calculate_diversity_scores,
    composite_interestingness,
    is_redundant_structure
)
from solver.explorer.filter import FormulaFilter
from solver.explorer.generator import (
    FormulaExplorer,
    anti_unify_terms,
    anti_unify_formulas
)

__all__ = [
    "DiversityMetrics",
    "calculate_symbol_entropy",
    "calculate_diversity_scores",
    "composite_interestingness",
    "is_redundant_structure",
    "FormulaFilter",
    "FormulaExplorer",
    "anti_unify_terms",
    "anti_unify_formulas",
]
```

---

### 4.5 CLI `explore` Command Integration (`solver/__main__.py`)

Integrates the explorer into the command line interface:

```python
# Add to solver/__main__.py argument parser:
explore_parser = argparse.ArgumentParser(
    prog="python -m solver explore",
    description="Explore and generate novel candidate formulas."
)
explore_parser.add_argument(
    "--strategy",
    choices=["mixed", "axiom_rewrite", "proof_frontier", "anti_unification", "saturation", "lemma_combination"],
    default="mixed",
    help="Formula generation strategy."
)
explore_parser.add_argument("--depth", type=int, default=4, help="Maximum AST depth limit.")
explore_parser.add_argument("--count", type=int, default=50, help="Number of raw candidates to generate.")
explore_parser.add_argument("--top-k", type=int, default=10, help="Number of top candidates to display.")
explore_parser.add_argument("--filter-file", type=str, default=None, help="Path to persistent filter state JSON file.")

def handle_explore(args: argparse.Namespace) -> None:
    config = SolverConfig()
    db = KnowledgeDatabase(db_path=config.db_path)
    signature = get_combined_signature()

    explorer = FormulaExplorer(
        db=db,
        signature=signature,
        config=config,
        filter_path=args.filter_file
    )

    candidates = explorer.generate_candidates(
        strategy=args.strategy,
        max_depth=args.depth,
        count=args.count
    )

    top_formulas = explorer.rank_and_select(candidates, top_k=args.top_k)

    print(f"--- Formula Explorer Summary ---")
    print(f"Strategy: {args.strategy} | Generated: {len(candidates)} | Top Selected: {len(top_formulas)}")
    print("-" * 50)

    for idx, formula in enumerate(top_formulas, 1):
        metrics = calculate_diversity_scores(formula)
        score = composite_interestingness(metrics)
        form_str = to_string(formula)
        print(f"[{idx}] Score: {score:.2f} | Depth: {metrics.ast_size} | {form_str}")

    if args.filter_file or explorer.filter.storage_path:
        explorer.filter.save_state()
        print(f"Saved filter state ({len(explorer.filter)} formulas seen).")
```

---

## 5. Step-by-Step Implementation Order

Implementation must proceed in the following strict sequential order:

```
Step 1: solver/explorer/heuristics.py
        └── Implement SymbolCollectorVisitor, calculate_symbol_entropy, calculate_diversity_scores, 
            composite_interestingness, and is_redundant_structure.
Step 2: solver/explorer/filter.py
        └── Implement FormulaFilter with _compute_hash, save_state, load_state, and set operations.
Step 3: solver/explorer/generator.py
        └── Implement anti_unify_terms, anti_unify_formulas, FormulaExplorer generator strategies 
            (_generate_axiom_rewrite, _generate_proof_frontier, _generate_anti_unification, 
             _generate_saturation, _generate_lemma_combination), generate_candidates, rank_and_select.
Step 4: solver/explorer/__init__.py
        └── Expose public symbols.
Step 5: solver/__main__.py CLI explore integration
        └── Implement explore subcommand argument parsing and handle_explore display formatting.
Step 6: tests/test_explorer.py
        └── Construct test cases covering deduplication, sort correctness, strategy differentiation, and filter persistence.
```

---

## 6. Testing Requirements

### 6.1 Unit & Property-Based Tests (`tests/test_explorer.py`)

1. **Batch Deduplication Unit Test**:
   - Verify `rank_and_select` returns a list with zero alpha-equivalent duplicate formulas.
   - Verify that adding a formula to `FormulaFilter` causes `is_seen()` to return `True` for both the formula and its alpha-renamed variant.
2. **Sort Constraint Property-Based Test** (`hypothesis`):
   - For every formula generated by `generate_candidates()`, verify `validate_formula(f, signature)` returns `True`.
   - Ensure no ill-sorted terms or invalid function application arities are generated.
3. **Diversity Metric & Shannon Entropy Verification**:
   - Assert `calculate_symbol_entropy(P(x) ∧ P(x))` is strictly lower than `calculate_symbol_entropy(P(x) ∧ Q(y) => R(x, y))`.
   - Assert `is_redundant_structure(x = x)` and `is_redundant_structure(P(x) => P(x))` return `True`.
4. **Strategy Differentiation Test**:
   - Run `generate_candidates()` with `"axiom_rewrite"`, `"anti_unification"`, `"saturation"`, and `"lemma_combination"` on a fixture knowledge base.
   - Verify each strategy produces non-empty, qualitatively distinct sets of candidate formulas.
5. **State Persistence Test**:
   - Add formulas to `FormulaFilter`, save state to a temporary JSON file via `save_state()`.
   - Instantiate a new `FormulaFilter` and call `load_state()`. Assert all previously saved formula hashes are present.

---

## 7. Acceptance Criteria

1. **Candidate Quality & Sorting**: Generates well-sorted, non-trivial, deduplicated candidate formulas that pass AST validation against the logical signature.
2. **Multi-Strategy Variety**: All 5 generation strategies (`axiom_rewrite`, `proof_frontier`, `anti_unification`, `saturation`, `lemma_combination`) execute without errors and produce distinct formula sets.
3. **Multi-Metric Scoring**: `DiversityMetrics` and `composite_interestingness` effectively differentiate trivial tautologies from structurally complex conjectures.
4. **Filter Persistence**: `FormulaFilter` persists state to disk across runs, successfully preserving hash sets through save/load cycles.
5. **CLI Operation**: `python -m solver explore --strategy mixed --count 20 --top-k 5` runs cleanly and outputs formatted candidate scores.

---

## 8. Risks and Mitigations

| Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **Combintorial explosion** during saturation or anti-unification | High | Bound saturation steps (max 2 resolution depth) and cap pair combinations in anti-unification. |
| **Generating unprovable / ill-sorted formulas** | High | Filter all generated candidates through `validate_formula()` before returning. |
| **Low candidate diversity** (repetitive ASTs) | Medium | Enforce `repeated_subtree_penalty` and filter candidates matching `is_redundant_structure()`. |
| **Filter state file I/O corruption** | Low | Write JSON filter files atomically and wrap load calls in error handles catching `DatabaseError`. |
