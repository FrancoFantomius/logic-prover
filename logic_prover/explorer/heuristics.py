"""Diversity metrics and formula interestingness heuristic scoring."""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Dict, Set, Optional, Tuple, Any, List

from logic_prover.core.ast import (
    Formula, Term, Variable, Constant, FunctionApp,
    PredicateApp, Equality, Not, And, Or, Implies, Iff, Forall, Exists,
    free_variables, bound_variables, formula_size, formula_depth
)
from logic_prover.core.visitors import ASTVisitor


@dataclass(frozen=True, slots=True)
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
        """Initializes state for tracking symbol frequencies, predicate sets, and quantifier depth."""
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
    penalty = sum_{sub, count > 1} (count - 1) * 0.5 * log2(size)
    Uses a single pass to collect sizes and counts together.
    """
    subtree_counts: Dict[Formula, int] = {}
    size_cache: Dict[int, int] = {}  # id(node) -> size

    def collect_subtrees(node: Formula) -> int:
        """Returns the formula_size of node, caching and counting as we go."""
        node_id = id(node)
        if node_id in size_cache:
            return size_cache[node_id]

        if isinstance(node, (PredicateApp, Equality)):
            sz = formula_size(node)
        elif isinstance(node, Not):
            sz = 1 + collect_subtrees(node.operand)
        elif isinstance(node, (And, Or, Implies, Iff)):
            sz = 1 + collect_subtrees(node.left) + collect_subtrees(node.right)
        elif isinstance(node, (Forall, Exists)):
            sz = 1 + collect_subtrees(node.body)
        else:
            sz = formula_size(node)

        size_cache[node_id] = sz
        if sz >= 2:
            subtree_counts[node] = subtree_counts.get(node, 0) + 1
        return sz

    collect_subtrees(formula)

    penalty = 0.0
    for node, count in subtree_counts.items():
        if count > 1:
            sz = size_cache.get(id(node), formula_size(node))
            penalty += (count - 1) * 0.5 * math.log2(sz)

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
