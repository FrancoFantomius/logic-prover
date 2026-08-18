"""Shared constants, predicates, and normalization utilities for constructive logic."""

from __future__ import annotations

from logic_prover.core.ast import (
    Formula, PredicateApp, Not, And, Or, Implies, Iff
)


# Internal representation for Falsum (Bottom / \bot)
FALSUM = PredicateApp(pred="_bot", arity=0, args=())
# Internal representation for Verum (Top / \top)
VERUM = PredicateApp(pred="_top", arity=0, args=())


def _is_falsum(formula: Formula) -> bool:
    """Checks if a formula AST represents the bottom / falsum logical constant.

    Args:
        formula (Formula): The formula AST node to test.

    Returns:
        bool: True if the formula is falsum (_bot), False otherwise.

    Example:
        >>> from logic_prover.constructive.common import _is_falsum, FALSUM
        >>> _is_falsum(FALSUM)
        True
    """
    return isinstance(formula, PredicateApp) and formula.pred == "_bot" and formula.arity == 0


def _is_verum(formula: Formula) -> bool:
    """Checks if a formula AST represents the top / verum logical constant.

    Args:
        formula (Formula): The formula AST node to test.

    Returns:
        bool: True if the formula is verum (_top), False otherwise.

    Example:
        >>> from logic_prover.constructive.common import _is_verum, VERUM
        >>> _is_verum(VERUM)
        True
    """
    return isinstance(formula, PredicateApp) and formula.pred == "_top" and formula.arity == 0


def _is_atomic(formula: Formula) -> bool:
    """Determines whether a formula is treated as an atomic proposition in constructive logic.

    Atomic propositions include predicate applications (including falsum and verum),
    term equalities, or any AST node that is not a propositional connective.

    Args:
        formula (Formula): The formula AST node to check.

    Returns:
        bool: True if atomic, False if compound connective.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, And
        >>> from logic_prover.constructive.common import _is_atomic
        >>> p = PredicateApp(pred="P", arity=0, args=())
        >>> _is_atomic(p)
        True
        >>> _is_atomic(And(left=p, right=p))
        False
    """
    if isinstance(formula, (Not, And, Or, Implies, Iff)):
        return False
    return True


def normalize_formula(formula: Formula) -> Formula:
    """Recursively normalizes connectives for constructive logic calculus.

    Expands logical equivalence A <=> B into (A => B) & (B => A) and
    negation ~A into A => _bot (falsum).

    Args:
        formula (Formula): The raw formula to normalize.

    Returns:
        Formula: The normalized formula using only atomic nodes, And, Or, and Implies.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, Not
        >>> from logic_prover.constructive.common import normalize_formula
        >>> p = PredicateApp(pred="P", arity=0, args=())
        >>> norm = normalize_formula(Not(operand=p))
        >>> type(norm).__name__
        'Implies'
    """
    if isinstance(formula, Not):
        norm_op = normalize_formula(formula.operand)
        return Implies(left=norm_op, right=FALSUM)
    elif isinstance(formula, Iff):
        left_norm = normalize_formula(formula.left)
        right_norm = normalize_formula(formula.right)
        imp1 = Implies(left=left_norm, right=right_norm)
        imp2 = Implies(left=right_norm, right=left_norm)
        return And(left=imp1, right=imp2)
    elif isinstance(formula, And):
        return And(left=normalize_formula(formula.left), right=normalize_formula(formula.right))
    elif isinstance(formula, Or):
        return Or(left=normalize_formula(formula.left), right=normalize_formula(formula.right))
    elif isinstance(formula, Implies):
        return Implies(left=normalize_formula(formula.left), right=normalize_formula(formula.right))
    else:
        return formula


def _formula_weight(formula: Formula) -> int:
    """Computes the Dyckhoff weight of a normalized formula.

    The Dyckhoff measure strictly decreases across every deduction step in LJT:
    - w(Atom) = 1
    - w(A & B) = 1 + w(A) + w(B)
    - w(A | B) = 1 + w(A) + w(B)
    - w(A => B) = 1 + w(A) * (w(B) + 1)

    Args:
        formula (Formula): The formula AST whose weight is to be computed.

    Returns:
        int: The positive integer weight of the formula.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, And
        >>> from logic_prover.constructive.common import _formula_weight
        >>> p = PredicateApp(pred="P", arity=0, args=())
        >>> _formula_weight(p)
        1
        >>> _formula_weight(And(left=p, right=p))
        3
    """
    if _is_atomic(formula):
        return 1
    elif isinstance(formula, And):
        return 1 + _formula_weight(formula.left) + _formula_weight(formula.right)
    elif isinstance(formula, Or):
        return 1 + _formula_weight(formula.left) + _formula_weight(formula.right)
    elif isinstance(formula, Implies):
        return 1 + _formula_weight(formula.left) * (_formula_weight(formula.right) + 1)
    else:
        return 1


__all__ = [
    "FALSUM",
    "VERUM",
    "_is_falsum",
    "_is_verum",
    "_is_atomic",
    "normalize_formula",
    "_formula_weight",
]
