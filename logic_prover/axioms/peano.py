"""Peano arithmetic axioms, signature, and formal Theory definitions."""

from __future__ import annotations
from typing import List, Tuple

from logic_prover.core.ast import (
    Formula, Variable, Constant, FunctionApp, PredicateApp, Equality,
    Not, Implies, Iff, Forall, Exists
)
from logic_prover.core.sorts import Nat, Ind
from logic_prover.core.signature import Signature
from logic_prover.axioms.base import Theory, register_theory


def get_peano_signature() -> Signature:
    """Constructs the logical signature declaring Peano arithmetic constants, functions, and relations.

    Registers constant 'zero', unary function 'succ', binary functions 'add' and 'mul',
    and binary relations 'le' and 'eq'.

    Returns:
        Signature: The initialized Peano arithmetic Signature instance.

    Example:
        >>> sig = get_peano_signature()
        >>> sig.has_symbol("zero") and sig.has_symbol("add") and sig.has_symbol("succ")
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


def get_peano_axioms() -> List[Tuple[str, Formula]]:
    """Generates the First-Order Peano arithmetic axioms for natural numbers.

    Axioms:
    - peano_zero_not_succ: ∀n:Nat. ¬(S(n) = 0)
    - peano_succ_injective: ∀m, n:Nat. (S(m) = S(n) ⇒ m = n)
    - peano_add_zero: ∀n:Nat. n + 0 = n
    - peano_add_succ: ∀m, n:Nat. m + S(n) = S(m + n)
    - peano_mul_zero: ∀n:Nat. n * 0 = 0
    - peano_mul_succ: ∀m, n:Nat. m * S(n) = (m * n) + m
    - peano_le_def: ∀m, n:Nat. (m ≤ n ⇔ ∃k. m + k = n)

    Returns:
        List[Tuple[str, Formula]]: List of (axiom_name, formula) pairs for Peano arithmetic.

    Example:
        >>> axioms = get_peano_axioms()
        >>> len(axioms) == 7
        True
        >>> axioms[0][0]
        'peano_zero_not_succ'
    """
    zero = Constant("zero", sort=Nat)

    m = Variable(0, sort=Nat)
    n = Variable(1, sort=Nat)
    k = Variable(2, sort=Nat)

    succ_m = FunctionApp("succ", 1, (m,), return_sort=Nat)
    succ_n = FunctionApp("succ", 1, (n,), return_sort=Nat)

    # 1. peano_zero_not_succ: forall n:Nat, ~(S(n) = 0)
    peano_zero_not_succ = Forall(n, Not(Equality(succ_n, zero)))

    # 2. peano_succ_injective: forall m:Nat forall n:Nat, (S(m) = S(n) => m = n)
    peano_succ_injective = Forall(m, Forall(n, Implies(Equality(succ_m, succ_n), Equality(m, n))))

    # 3. peano_add_zero: forall n:Nat, n + 0 = n
    add_n_zero = FunctionApp("add", 2, (n, zero), return_sort=Nat)
    peano_add_zero = Forall(n, Equality(add_n_zero, n))

    # 4. peano_add_succ: forall m:Nat forall n:Nat, m + S(n) = S(m + n)
    add_m_succ_n = FunctionApp("add", 2, (m, succ_n), return_sort=Nat)
    add_m_n = FunctionApp("add", 2, (m, n), return_sort=Nat)
    succ_add_m_n = FunctionApp("succ", 1, (add_m_n,), return_sort=Nat)
    peano_add_succ = Forall(m, Forall(n, Equality(add_m_succ_n, succ_add_m_n)))

    # 5. peano_mul_zero: forall n:Nat, n * 0 = 0
    mul_n_zero = FunctionApp("mul", 2, (n, zero), return_sort=Nat)
    peano_mul_zero = Forall(n, Equality(mul_n_zero, zero))

    # 6. peano_mul_succ: forall m:Nat forall n:Nat, m * S(n) = (m * n) + m
    mul_m_succ_n = FunctionApp("mul", 2, (m, succ_n), return_sort=Nat)
    mul_m_n = FunctionApp("mul", 2, (m, n), return_sort=Nat)
    add_mul_m_n_m = FunctionApp("add", 2, (mul_m_n, m), return_sort=Nat)
    peano_mul_succ = Forall(m, Forall(n, Equality(mul_m_succ_n, add_mul_m_n_m)))

    # 7. peano_le_def: forall m:Nat forall n:Nat, (m <= n <=> exists k:Nat, m + k = n)
    le_m_n = PredicateApp("le", 2, (m, n))
    add_m_k = FunctionApp("add", 2, (m, k), return_sort=Nat)
    peano_le_def = Forall(m, Forall(n, Iff(le_m_n, Exists(k, Equality(add_m_k, n)))))

    return [
        ("peano_zero_not_succ", peano_zero_not_succ),
        ("peano_succ_injective", peano_succ_injective),
        ("peano_add_zero", peano_add_zero),
        ("peano_add_succ", peano_add_succ),
        ("peano_mul_zero", peano_mul_zero),
        ("peano_mul_succ", peano_mul_succ),
        ("peano_le_def", peano_le_def),
    ]


# Instantiated Theory object
peano_theory: Theory = Theory(
    name="peano",
    description="First-order Peano arithmetic for natural numbers (successor, addition, multiplication, ordering).",
    sorts={"Nat": Nat},
    signature=get_peano_signature(),
    axioms=dict(get_peano_axioms()),
)
register_theory(peano_theory)
