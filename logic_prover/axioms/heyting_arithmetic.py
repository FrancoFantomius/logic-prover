"""Heyting Arithmetic (HA) axioms, logical signature, and formal Theory definitions."""

from __future__ import annotations
from typing import List, Tuple, Optional

from logic_prover.core.ast import (
    Formula, Term, Variable, Constant, FunctionApp, PredicateApp, Equality,
    Not, And, Implies, Iff, Forall, Exists
)
from logic_prover.core.sorts import Nat, Ind
from logic_prover.core.signature import Signature
from logic_prover.core.substitutions import substitute_formula
from logic_prover.axioms.base import Theory, register_theory


def get_ha_signature() -> Signature:
    """Constructs the logical signature for Heyting Arithmetic (HA).

    Registers constant 'zero', unary function 'succ', binary functions 'add' and 'mul',
    and binary relations 'le', 'lt', and 'eq'.

    Returns:
        Signature: The initialized Heyting Arithmetic Signature instance.

    Example:
        >>> sig = get_ha_signature()
        >>> sig.has_symbol("zero") and sig.has_symbol("succ") and sig.has_symbol("add")
        True
    """
    sig = Signature()
    sig.register_constant("zero", Nat)
    sig.register_function("succ", 1, (Nat,), Nat)
    sig.register_function("add", 2, (Nat, Nat), Nat)
    sig.register_function("mul", 2, (Nat, Nat), Nat)
    sig.register_predicate("le", 2, (Ind, Ind))
    sig.register_predicate("lt", 2, (Ind, Ind))
    sig.register_predicate("eq", 2, (Nat, Nat))
    return sig


def instantiate_ha_induction(
    property_formula: Formula,
    bound_var: Variable,
    zero_term: Optional[Term] = None,
    succ_func_name: str = "succ"
) -> Formula:
    """Instantiates the First-Order Induction Schema for a specific property formula A(n).

    Generates the sentence:
    (A(0) & forall n. (A(n) => A(S(n)))) => forall n. A(n)

    Args:
        property_formula (Formula): The property formula A(n) to induct over.
        bound_var (Variable): The variable n used in the induction step and conclusion.
        zero_term (Optional[Term], default=None): The base term to substitute; defaults to Constant('zero').
        succ_func_name (str, default='succ'): The name of the successor function symbol.

    Returns:
        Formula: The instantiated induction schema formula.

    Example:
        >>> from logic_prover.core.ast import Variable, Equality
        >>> from logic_prover.core.sorts import Nat
        >>> n = Variable(0, sort=Nat)
        >>> form = Equality(n, n)
        >>> ind_ax = instantiate_ha_induction(form, n)
        >>> type(ind_ax).__name__
        'Implies'
    """
    if zero_term is None:
        zero_term = Constant("zero", sort=bound_var.sort)

    succ_term = FunctionApp(func=succ_func_name, arity=1, args=(bound_var,), return_sort=bound_var.sort)

    base_case = substitute_formula(property_formula, {bound_var: zero_term})
    step_body = substitute_formula(property_formula, {bound_var: succ_term})
    step_case = Forall(variable=bound_var, body=Implies(left=property_formula, right=step_body))

    hypothesis = And(left=base_case, right=step_case)
    conclusion = Forall(variable=bound_var, body=property_formula)

    return Implies(left=hypothesis, right=conclusion)


def get_ha_axioms() -> List[Tuple[str, Formula]]:
    """Generates the core First-Order Heyting Arithmetic axioms for natural numbers.

    Axioms:
    - ha_zero_not_succ: ∀n:Nat. ¬(S(n) = 0)
    - ha_succ_injective: ∀m, n:Nat. (S(m) = S(n) ⇒ m = n)
    - ha_add_zero: ∀n:Nat. n + 0 = n
    - ha_add_succ: ∀m, n:Nat. m + S(n) = S(m + n)
    - ha_mul_zero: ∀n:Nat. n * 0 = 0
    - ha_mul_succ: ∀m, n:Nat. m * S(n) = (m * n) + m
    - ha_le_def: ∀m, n:Nat. (m ≤ n ⇔ ∃k. m + k = n)

    Returns:
        List[Tuple[str, Formula]]: List of (axiom_name, formula) pairs for Heyting Arithmetic.

    Example:
        >>> axioms = get_ha_axioms()
        >>> len(axioms) == 7
        True
        >>> axioms[0][0]
        'ha_zero_not_succ'
    """
    zero = Constant("zero", sort=Nat)

    m = Variable(0, sort=Nat)
    n = Variable(1, sort=Nat)
    k = Variable(2, sort=Nat)

    succ_m = FunctionApp("succ", 1, (m,), return_sort=Nat)
    succ_n = FunctionApp("succ", 1, (n,), return_sort=Nat)

    # 1. ha_zero_not_succ: forall n:Nat, ~(S(n) = 0)
    ha_zero_not_succ = Forall(n, Not(Equality(succ_n, zero)))

    # 2. ha_succ_injective: forall m:Nat forall n:Nat, (S(m) = S(n) => m = n)
    ha_succ_injective = Forall(m, Forall(n, Implies(Equality(succ_m, succ_n), Equality(m, n))))

    # 3. ha_add_zero: forall n:Nat, n + 0 = n
    add_n_zero = FunctionApp("add", 2, (n, zero), return_sort=Nat)
    ha_add_zero = Forall(n, Equality(add_n_zero, n))

    # 4. ha_add_succ: forall m:Nat forall n:Nat, m + S(n) = S(m + n)
    add_m_succ_n = FunctionApp("add", 2, (m, succ_n), return_sort=Nat)
    add_m_n = FunctionApp("add", 2, (m, n), return_sort=Nat)
    succ_add_m_n = FunctionApp("succ", 1, (add_m_n,), return_sort=Nat)
    ha_add_succ = Forall(m, Forall(n, Equality(add_m_succ_n, succ_add_m_n)))

    # 5. ha_mul_zero: forall n:Nat, n * 0 = 0
    mul_n_zero = FunctionApp("mul", 2, (n, zero), return_sort=Nat)
    ha_mul_zero = Forall(n, Equality(mul_n_zero, zero))

    # 6. ha_mul_succ: forall m:Nat forall n:Nat, m * S(n) = (m * n) + m
    mul_m_succ_n = FunctionApp("mul", 2, (m, succ_n), return_sort=Nat)
    mul_m_n = FunctionApp("mul", 2, (m, n), return_sort=Nat)
    add_mul_m_n_m = FunctionApp("add", 2, (mul_m_n, m), return_sort=Nat)
    ha_mul_succ = Forall(m, Forall(n, Equality(mul_m_succ_n, add_mul_m_n_m)))

    # 7. ha_le_def: forall m:Nat forall n:Nat, (m <= n <=> exists k:Nat, m + k = n)
    le_m_n = PredicateApp("le", 2, (m, n))
    add_m_k = FunctionApp("add", 2, (m, k), return_sort=Nat)
    ha_le_def = Forall(m, Forall(n, Iff(le_m_n, Exists(k, Equality(add_m_k, n)))))

    return [
        ("ha_zero_not_succ", ha_zero_not_succ),
        ("ha_succ_injective", ha_succ_injective),
        ("ha_add_zero", ha_add_zero),
        ("ha_add_succ", ha_add_succ),
        ("ha_mul_zero", ha_mul_zero),
        ("ha_mul_succ", ha_mul_succ),
        ("ha_le_def", ha_le_def),
    ]


# Instantiated HA Theory object
ha_theory: Theory = Theory(
    name="ha",
    description="Heyting Arithmetic: constructive first-order arithmetic with Peano axioms and induction schema.",
    sorts={"Nat": Nat},
    signature=get_ha_signature(),
    axioms=dict(get_ha_axioms()),
)
register_theory(ha_theory)

