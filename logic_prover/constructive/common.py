"""Shared constants, predicates, and normalization utilities for constructive logic."""

from __future__ import annotations
import itertools
from typing import List, Sequence, Tuple, Set, Optional, Iterable

from logic_prover.core.ast import (
    Formula, Term, Variable, Constant, FunctionApp,
    PredicateApp, Not, And, Or, Implies, Iff, Forall, Exists
)
from logic_prover.core.sorts import Ind


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
    term equalities, or any AST node that is not a propositional connective or quantifier.

    Args:
        formula (Formula): The formula AST node to check.

    Returns:
        bool: True if atomic, False if compound connective or quantifier.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, And
        >>> from logic_prover.constructive.common import _is_atomic
        >>> p = PredicateApp(pred="P", arity=0, args=())
        >>> _is_atomic(p)
        True
        >>> _is_atomic(And(left=p, right=p))
        False
    """
    if isinstance(formula, (Not, And, Or, Implies, Iff, Forall, Exists)):
        return False
    return True


def normalize_formula(formula: Formula) -> Formula:
    """Recursively normalizes connectives for constructive logic calculus.

    Expands logical equivalence A <=> B into (A => B) & (B => A) and
    negation ~A into A => _bot (falsum), and recurses into quantifier bodies.

    Args:
        formula (Formula): The raw formula to normalize.

    Returns:
        Formula: The normalized formula using only atomic nodes, And, Or, Implies, Forall, and Exists.

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
    elif isinstance(formula, Forall):
        return Forall(variable=formula.variable, body=normalize_formula(formula.body))
    elif isinstance(formula, Exists):
        return Exists(variable=formula.variable, body=normalize_formula(formula.body))
    else:
        return formula


def _formula_weight(formula: Formula) -> int:
    """Computes the Dyckhoff weight of a normalized formula.

    The Dyckhoff measure strictly decreases across propositional deduction steps:
    - w(Atom) = 1
    - w(A & B) = 1 + w(A) + w(B)
    - w(A | B) = 1 + w(A) + w(B)
    - w(A => B) = 1 + w(A) * (w(B) + 1)
    - w(forall x. A) = 1 + w(A)
    - w(exists x. A) = 1 + w(A)

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
    elif isinstance(formula, (Forall, Exists)):
        return 1 + _formula_weight(formula.body)
    else:
        return 1


def fresh_variable(existing_vars: Iterable[Variable] = ()) -> Variable:
    """Generates a fresh individual Variable distinct from existing variables.

    Args:
        existing_vars (Iterable[Variable], default=()): Collection of allocated variables.

    Returns:
        Variable: A fresh Variable instance.

    Example:
        >>> from logic_prover.constructive.common import fresh_variable
        >>> from logic_prover.core.ast import Variable
        >>> v = fresh_variable([Variable(1), Variable(2)])
        >>> v.id
        3
    """
    ids = {v.id for v in existing_vars}
    next_id = max(ids, default=0) + 1
    return Variable(id=next_id, sort=Ind)


def fresh_constant(
    prefix: str = "c",
    counter: Optional[List[int]] = None,
    existing_constants: Iterable[Constant] = ()
) -> Constant:
    """Generates a fresh Constant symbol distinct from existing constants.

    Args:
        prefix (str, default='c'): Name prefix for the generated constant.
        counter (Optional[List[int]], default=None): Mutable single-element integer counter.
        existing_constants (Iterable[Constant], default=()): Collection of allocated constants.

    Returns:
        Constant: A fresh Constant instance.

    Example:
        >>> from logic_prover.constructive.common import fresh_constant
        >>> c = fresh_constant(prefix="c")
        >>> isinstance(c.name, str)
        True
    """
    existing_names = {c.name for c in existing_constants}
    if counter is not None:
        while True:
            c_name = f"{prefix}{counter[0]}"
            counter[0] += 1
            if c_name not in existing_names:
                return Constant(name=c_name, sort=Ind)
    idx = 0
    while True:
        c_name = f"{prefix}_{idx}" if prefix.endswith(tuple("0123456789")) else f"{prefix}{idx}"
        if c_name not in existing_names:
            return Constant(name=c_name, sort=Ind)
        idx += 1


def ground_terms(
    constants: Sequence[Term],
    functions: Sequence[Tuple[str, int]] = (),
    max_depth: int = 1
) -> List[Term]:
    """Enumerates ground terms from a set of base constant terms and function declarations.

    Args:
        constants (Sequence[Term]): Available base constant terms.
        functions (Sequence[Tuple[str, int]], default=()): Function symbol name and arity tuples.
        max_depth (int, default=1): Maximum nesting depth of function applications.

    Returns:
        List[Term]: Ordered list of generated ground terms.

    Example:
        >>> from logic_prover.constructive.common import ground_terms
        >>> from logic_prover.core.ast import Constant
        >>> c = Constant("c0")
        >>> terms = ground_terms([c], functions=[("f", 1)], max_depth=1)
        >>> len(terms) >= 1
        True
    """
    base_terms = list(constants) if constants else [Constant(name="c0", sort=Ind)]
    all_terms: List[Term] = list(base_terms)
    seen: Set[Term] = set(base_terms)

    current_layer = list(base_terms)
    for _ in range(max_depth):
        next_layer: List[Term] = []
        for func_name, arity in functions:
            if arity <= 0:
                continue
            for args in itertools.product(all_terms, repeat=arity):
                fn_term = FunctionApp(func=func_name, arity=arity, args=args, return_sort=Ind)
                if fn_term not in seen:
                    seen.add(fn_term)
                    next_layer.append(fn_term)
        if not next_layer:
            break
        all_terms.extend(next_layer)
        current_layer = next_layer

    return all_terms


__all__ = [
    "FALSUM",
    "VERUM",
    "_is_falsum",
    "_is_verum",
    "_is_atomic",
    "normalize_formula",
    "_formula_weight",
    "fresh_variable",
    "fresh_constant",
    "ground_terms",
]
