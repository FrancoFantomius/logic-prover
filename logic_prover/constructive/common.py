"""Shared constants, predicates, and normalization utilities for constructive logic."""

from __future__ import annotations
import itertools
from typing import List, Sequence, Tuple, Set, Optional, Iterable

from logic_prover.core.ast import (
    Formula, Term, Variable, Constant, FunctionApp,
    PredicateApp, Equality, Not, And, Or, Implies, Iff, Forall, Exists
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
    term equalities (Equality is intentionally atomic in iFOL=; equality reasoning is
    handled by prover rules and congruence closure rather than compound connective decomposition),
    or any AST node that is not a propositional connective or quantifier.

    Args:
        formula (Formula): The formula AST node to check.

    Returns:
        bool: True if atomic, False if compound connective or quantifier.

    Example:
        >>> from logic_prover.core.ast import PredicateApp, And, Equality, Constant
        >>> from logic_prover.constructive.common import _is_atomic
        >>> p = PredicateApp(pred="P", arity=0, args=())
        >>> _is_atomic(p)
        True
        >>> _is_atomic(Equality(Constant("a"), Constant("b")))
        True
        >>> _is_atomic(And(left=p, right=p))
        False
    """
    if isinstance(formula, (Not, And, Or, Implies, Iff, Forall, Exists)):
        return False
    return True


def collect_equalities(formula: Formula, sign: Optional[str] = None) -> Set[Equality]:
    """Recursively collects equality subformulas occurring within a formula AST.

    Args:
        formula (Formula): The formula AST node to inspect.
        sign (Optional[str], default=None): Polarity filter ('T' for positive occurrences, 'F' for negative, or None for all occurrences).

    Returns:
        Set[Equality]: Set of collected Equality subformula nodes.

    Example:
        >>> from logic_prover.core.ast import Equality, Constant, And, Not
        >>> from logic_prover.constructive.common import collect_equalities
        >>> eq1 = Equality(Constant("a"), Constant("b"))
        >>> eq2 = Equality(Constant("c"), Constant("d"))
        >>> f = And(eq1, Not(eq2))
        >>> sorted(list(collect_equalities(f)), key=lambda e: str(e.left)) == [eq1, eq2]
        True
        >>> collect_equalities(f, sign="T") == {eq1}
        True
    """
    equalities: Set[Equality] = set()

    def _traverse(node: Formula, current_polarity: int) -> None:
        if isinstance(node, Equality):
            if sign is None:
                equalities.add(node)
            elif sign == "T" and current_polarity == 1:
                equalities.add(node)
            elif sign == "F" and current_polarity == -1:
                equalities.add(node)
        elif isinstance(node, Not):
            _traverse(node.operand, -current_polarity)
        elif isinstance(node, And):
            _traverse(node.left, current_polarity)
            _traverse(node.right, current_polarity)
        elif isinstance(node, Or):
            _traverse(node.left, current_polarity)
            _traverse(node.right, current_polarity)
        elif isinstance(node, Implies):
            _traverse(node.left, -current_polarity)
            _traverse(node.right, current_polarity)
        elif isinstance(node, Iff):
            # In an equivalence A <=> B, both sides occur in both polarities
            _traverse(node.left, 0)
            _traverse(node.right, 0)
        elif isinstance(node, (Forall, Exists)):
            _traverse(node.body, current_polarity)

    _traverse(formula, 1)
    return equalities


def kbo_weight(term: Term) -> int:
    """Computes the Knuth-Bendix Ordering (KBO) weight of a term.

    Variables and constants are assigned a base weight of 1.
    Function applications have weight 1 plus the sum of the weights of their subterm arguments.

    Args:
        term (Term): The term whose KBO weight is to be computed.

    Returns:
        int: The positive integer KBO weight of the term.

    Example:
        >>> from logic_prover.core.ast import Constant, Variable, FunctionApp
        >>> from logic_prover.constructive.common import kbo_weight
        >>> kbo_weight(Constant("a"))
        1
        >>> kbo_weight(FunctionApp("f", 1, (Constant("a"),)))
        2
    """
    if isinstance(term, (Variable, Constant)):
        return 1
    elif isinstance(term, FunctionApp):
        return 1 + sum(kbo_weight(arg) for arg in term.args)
    return 1


def _variable_counts(term: Term) -> Dict[Variable, int]:
    """Helper counting the occurrences of each variable within a term.

    Args:
        term (Term): The term AST to scan.

    Returns:
        Dict[Variable, int]: Mapping from variables to their occurrence count.
    """
    counts: Dict[Variable, int] = {}

    def _count(t: Term) -> None:
        if isinstance(t, Variable):
            counts[t] = counts.get(t, 0) + 1
        elif isinstance(t, FunctionApp):
            for arg in t.args:
                _count(arg)

    _count(term)
    return counts


def kbo_compare(t1: Term, t2: Term) -> str:
    """Compares two terms under Knuth-Bendix Ordering (KBO).

    Determines if t1 > t2 ('gt'), t1 < t2 ('lt'), t1 == t2 ('eq'),
    or if the terms are incomparable ('incomparable').

    Args:
        t1 (Term): Left term to compare.
        t2 (Term): Right term to compare.

    Returns:
        str: Comparison result ('gt', 'lt', 'eq', or 'incomparable').

    Example:
        >>> from logic_prover.core.ast import Constant, FunctionApp
        >>> from logic_prover.constructive.common import kbo_compare
        >>> a = Constant("a")
        >>> f_a = FunctionApp("f", 1, (a,))
        >>> kbo_compare(f_a, a)
        'gt'
        >>> kbo_compare(a, f_a)
        'lt'
        >>> kbo_compare(a, a)
        'eq'
    """
    if t1 == t2:
        return "eq"

    w1 = kbo_weight(t1)
    w2 = kbo_weight(t2)

    vars1 = _variable_counts(t1)
    vars2 = _variable_counts(t2)

    # Condition: for t1 > t2, every variable in t2 must appear in t1 with count(t1, x) >= count(t2, x)
    def _vars_ge(v_sup: Dict[Variable, int], v_sub: Dict[Variable, int]) -> bool:
        return all(v_sup.get(x, 0) >= count for x, count in v_sub.items())

    # Check t1 > t2
    def _strictly_greater(left: Term, right: Term, w_left: int, w_right: int, v_left: Dict[Variable, int], v_right: Dict[Variable, int]) -> bool:
        if not _vars_ge(v_left, v_right):
            return False
        if w_left > w_right:
            return True
        if w_left == w_right:
            if isinstance(left, Constant) and isinstance(right, Constant):
                return left.name > right.name
            if isinstance(left, FunctionApp) and isinstance(right, FunctionApp):
                if left.func != right.func:
                    return str(left.func) > str(right.func)
                if left.arity != right.arity:
                    return left.arity > right.arity
                # Lexicographic comparison of arguments
                for a1, a2 in zip(left.args, right.args):
                    cmp_res = kbo_compare(a1, a2)
                    if cmp_res == "gt":
                        return True
                    elif cmp_res == "lt":
                        return False
            if isinstance(left, FunctionApp) and isinstance(right, Constant):
                return True
        return False

    if _strictly_greater(t1, t2, w1, w2, vars1, vars2):
        return "gt"
    if _strictly_greater(t2, t1, w2, w1, vars2, vars1):
        return "lt"

    return "incomparable"


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
    "collect_equalities",
    "kbo_weight",
    "kbo_compare",
    "normalize_formula",
    "_formula_weight",
    "fresh_variable",
    "fresh_constant",
    "ground_terms",
]
