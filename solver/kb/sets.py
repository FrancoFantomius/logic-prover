"""Naive set theory axioms (extensionality, subset, union, intersection, empty set)."""

from __future__ import annotations
from typing import List, Tuple

from solver.core.ast import (
    Formula, Variable, Constant, FunctionApp, PredicateApp, Equality, Forall, Implies, And, Or, Not, Iff
)
from solver.core.sorts import PrimitiveSort, ParameterizedSort, SetSort, Ind
from solver.core.signature import Signature

ElemSort: PrimitiveSort = PrimitiveSort("Elem")
SetType: ParameterizedSort = SetSort(ElemSort)


def get_set_signature() -> Signature:
    """Returns signature for minimal set theory symbols."""
    sig = Signature()
    sig.register_sort_constructor("Set", 1)
    sig.register_predicate("in_set", 2, (Ind, Ind))
    sig.register_predicate("subset", 2, (SetType, SetType))
    sig.register_constant("empty_set", SetType)
    sig.register_function("union", 2, (SetType, SetType), SetType)
    sig.register_function("inter", 2, (SetType, SetType), SetType)
    sig.register_function("diff", 2, (SetType, SetType), SetType)
    sig.register_function("singleton", 1, (ElemSort,), SetType)
    sig.register_function("powerset", 1, (SetType,), SetSort(SetType))
    return sig


def get_set_theory_axioms() -> List[Tuple[str, Formula]]:
    """Returns minimal set theory axioms: extensionality, subset, empty set, union, inter, diff, singleton, powerset."""
    A = Variable(0, sort=SetType)
    B = Variable(1, sort=SetType)
    x = Variable(3, sort=ElemSort)
    y = Variable(4, sort=ElemSort)

    empty_set = Constant("empty_set", sort=SetType)

    in_xA = PredicateApp("in_set", 2, (x, A))
    in_xB = PredicateApp("in_set", 2, (x, B))

    # 1. set_extensionality: forall A forall B, (A = B <=> forall x, (x in A <=> x in B))
    set_extensionality = Forall(
        A,
        Forall(
            B,
            Iff(
                Equality(A, B),
                Forall(x, Iff(in_xA, in_xB)),
            ),
        ),
    )

    # 2. set_subset_def: forall A forall B, (A <= B <=> forall x, (x in A => x in B))
    sub_AB = PredicateApp("subset", 2, (A, B))
    set_subset_def = Forall(
        A,
        Forall(
            B,
            Iff(sub_AB, Forall(x, Implies(in_xA, in_xB))),
        ),
    )

    # 3. set_empty_def: forall x, ~(x in empty_set)
    in_x_empty = PredicateApp("in_set", 2, (x, empty_set))
    set_empty_def = Forall(x, Not(in_x_empty))

    # 4. set_union_def: forall A forall B forall x, (x in union(A, B) <=> (x in A | x in B))
    union_AB = FunctionApp("union", 2, (A, B), return_sort=SetType)
    in_x_union = PredicateApp("in_set", 2, (x, union_AB))
    set_union_def = Forall(
        A,
        Forall(
            B,
            Forall(x, Iff(in_x_union, Or(in_xA, in_xB))),
        ),
    )

    # 5. set_inter_def: forall A forall B forall x, (x in inter(A, B) <=> (x in A & x in B))
    inter_AB = FunctionApp("inter", 2, (A, B), return_sort=SetType)
    in_x_inter = PredicateApp("in_set", 2, (x, inter_AB))
    set_inter_def = Forall(
        A,
        Forall(
            B,
            Forall(x, Iff(in_x_inter, And(in_xA, in_xB))),
        ),
    )

    # 6. set_diff_def: forall A forall B forall x, (x in diff(A, B) <=> (x in A & ~(x in B)))
    diff_AB = FunctionApp("diff", 2, (A, B), return_sort=SetType)
    in_x_diff = PredicateApp("in_set", 2, (x, diff_AB))
    set_diff_def = Forall(
        A,
        Forall(
            B,
            Forall(x, Iff(in_x_diff, And(in_xA, Not(in_xB)))),
        ),
    )

    # 7. set_singleton_def: forall x forall y, (y in singleton(x) <=> y = x)
    sing_x = FunctionApp("singleton", 1, (x,), return_sort=SetType)
    in_y_sing = PredicateApp("in_set", 2, (y, sing_x))
    set_singleton_def = Forall(
        x,
        Forall(y, Iff(in_y_sing, Equality(y, x))),
    )

    # 8. set_powerset_def: forall A forall B, (B in powerset(A) <=> B <= A)
    pset_A = FunctionApp("powerset", 1, (A,), return_sort=SetSort(SetType))
    in_B_pset = PredicateApp("in_set", 2, (B, pset_A))
    sub_BA = PredicateApp("subset", 2, (B, A))
    set_powerset_def = Forall(
        A,
        Forall(B, Iff(in_B_pset, sub_BA)),
    )

    return [
        ("set_extensionality", set_extensionality),
        ("set_subset_def", set_subset_def),
        ("set_empty_def", set_empty_def),
        ("set_union_def", set_union_def),
        ("set_inter_def", set_inter_def),
        ("set_diff_def", set_diff_def),
        ("set_singleton_def", set_singleton_def),
        ("set_powerset_def", set_powerset_def),
    ]
