"""Equality axioms and congruence signature definitions."""

from __future__ import annotations
from typing import List, Tuple

from solver.core.ast import (
    Formula, Variable, Equality, Not, And, Or, Implies, Iff, Forall, Exists, FunctionApp, PredicateApp
)
from solver.core.sorts import Ind
from solver.core.signature import Signature


def get_equality_signature() -> Signature:
    """Returns signature declaring generic equality operations and sample symbols for schemata."""
    sig = Signature()
    sig.register_function("f", 1, (Ind,), Ind)
    sig.register_function("f_bin", 2, (Ind, Ind), Ind)
    sig.register_predicate("P", 1, (Ind,))
    return sig


def get_equality_axioms() -> List[Tuple[str, Formula]]:
    """Returns fundamental equality axioms: reflexivity, symmetry, transitivity, and congruence schemata."""
    x = Variable(0, sort=Ind)
    y = Variable(1, sort=Ind)
    z = Variable(2, sort=Ind)
    x1 = Variable(0, sort=Ind)
    x2 = Variable(1, sort=Ind)
    y1 = Variable(2, sort=Ind)
    y2 = Variable(3, sort=Ind)

    # 1. eq_reflexive: forall x, x = x
    eq_reflexive = Forall(x, Equality(x, x))

    # 2. eq_symmetric: forall x y, (x = y => y = x)
    eq_symmetric = Forall(x, Forall(y, Implies(Equality(x, y), Equality(y, x))))

    # 3. eq_transitive: forall x y z, ((x = y & y = z) => x = z)
    eq_transitive = Forall(
        x,
        Forall(
            y,
            Forall(
                z,
                Implies(And(Equality(x, y), Equality(y, z)), Equality(x, z))
            )
        )
    )

    # 4. eq_congruence_unary_func: forall x y, (x = y => f(x) = f(y))
    fx = FunctionApp("f", 1, (x,), return_sort=Ind)
    fy = FunctionApp("f", 1, (y,), return_sort=Ind)
    eq_congruence_unary_func = Forall(x, Forall(y, Implies(Equality(x, y), Equality(fx, fy))))

    # 5. eq_congruence_binary_func: forall x1 x2 y1 y2, ((x1 = y1 & x2 = y2) => f_bin(x1, x2) = f_bin(y1, y2))
    f_x1_x2 = FunctionApp("f_bin", 2, (x1, x2), return_sort=Ind)
    f_y1_y2 = FunctionApp("f_bin", 2, (y1, y2), return_sort=Ind)
    eq_congruence_binary_func = Forall(
        x1,
        Forall(
            x2,
            Forall(
                y1,
                Forall(
                    y2,
                    Implies(And(Equality(x1, y1), Equality(x2, y2)), Equality(f_x1_x2, f_y1_y2))
                )
            )
        )
    )

    # 6. eq_congruence_unary_pred: forall x y, ((x = y & P(x)) => P(y))
    px = PredicateApp("P", 1, (x,))
    py = PredicateApp("P", 1, (y,))
    eq_congruence_unary_pred = Forall(
        x,
        Forall(
            y,
            Implies(And(Equality(x, y), px), py)
        )
    )

    return [
        ("eq_reflexive", eq_reflexive),
        ("eq_symmetric", eq_symmetric),
        ("eq_transitive", eq_transitive),
        ("eq_congruence_unary_func", eq_congruence_unary_func),
        ("eq_congruence_binary_func", eq_congruence_binary_func),
        ("eq_congruence_unary_pred", eq_congruence_unary_pred),
    ]
