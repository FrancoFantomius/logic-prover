"""Zermelo-Fraenkel Set Theory with Choice (ZFC) axioms, signature, and Theory definition."""

from __future__ import annotations
from typing import List, Tuple

from logic_prover.core.ast import (
    Formula, Variable, Constant, FunctionApp, PredicateApp, Equality,
    Forall, Exists, Implies, And, Or, Not, Iff
)
from logic_prover.core.sorts import PrimitiveSort, ParameterizedSort, SetSort, Ind
from logic_prover.core.signature import Signature
from logic_prover.axioms.base import Theory, register_theory

ElemSort: PrimitiveSort = PrimitiveSort("Elem")
SetElem: PrimitiveSort = ElemSort
SetType: ParameterizedSort = SetSort(ElemSort)


def get_zfc_signature() -> Signature:
    """Constructs the signature declaring ZFC axiomatic set theory symbols.

    Registers sort constructor 'Set', binary relations 'in_set', 'subset',
    constant 'empty_set', and operations 'union', 'inter', 'diff', 'singleton',
    'pair', 'powerset', and 'choice'.

    Returns:
        Signature: The initialized ZFC Set Theory Signature instance.

    Example:
        >>> sig = get_zfc_signature()
        >>> sig.has_symbol("union") and sig.has_symbol("in_set") and sig.has_symbol("choice")
        True
    """
    sig = Signature()
    sig.register_sort_constructor("Set", 1)
    sig.register_predicate("in_set", 2, (Ind, Ind))
    sig.register_predicate("subset", 2, (SetType, SetType))
    sig.register_constant("empty_set", SetType)
    sig.register_function("union", 2, (SetType, SetType), SetType)
    sig.register_function("inter", 2, (SetType, SetType), SetType)
    sig.register_function("diff", 2, (SetType, SetType), SetType)
    sig.register_function("singleton", 1, (ElemSort,), SetType)
    sig.register_function("pair", 2, (ElemSort, ElemSort), SetType)
    sig.register_function("powerset", 1, (SetType,), SetSort(SetType))
    sig.register_function("choice", 1, (SetType,), ElemSort)
    return sig


def get_set_signature() -> Signature:
    """Constructs signature for set theory.

    Returns:
        Signature: The initialized set theory Signature instance.

    Example:
        >>> sig = get_set_signature()
        >>> sig.has_symbol("in_set")
        True
    """
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


def get_zfc_axioms() -> List[Tuple[str, Formula]]:
    """Generates the foundational First-Order Axioms of ZFC Set Theory.

    Axioms:
    - zfc_extensionality: ∀A, B. (A = B ⇔ ∀x. (x ∈ A ⇔ x ∈ B))
    - zfc_subset_def: ∀A, B. (A ⊆ B ⇔ ∀x. (x ∈ A ⇒ x ∈ B))
    - zfc_empty_set: ∀x. ¬(x ∈ ∅)
    - zfc_pairing: ∀x, y, z. (z ∈ pair(x, y) ⇔ (z = x ∨ z = y))
    - zfc_singleton: ∀x, y. (y ∈ singleton(x) ⇔ y = x)
    - zfc_union_def: ∀A, B, x. (x ∈ (A ∪ B) ⇔ (x ∈ A ∨ x ∈ B))
    - zfc_inter_def: ∀A, B, x. (x ∈ (A ∩ B) ⇔ (x ∈ A ∧ x ∈ B))
    - zfc_diff_def: ∀A, B, x. (x ∈ (A \\ B) ⇔ (x ∈ A ∧ ¬(x ∈ B)))
    - zfc_powerset_def: ∀A, B. (B ∈ 𝒫(A) ⇔ B ⊆ A)
    - zfc_choice_axiom: ∀A. (¬(A = ∅) ⇒ choice(A) ∈ A)

    Returns:
        List[Tuple[str, Formula]]: List of (axiom_name, formula) pairs for ZFC set theory.

    Example:
        >>> axioms = get_zfc_axioms()
        >>> len(axioms) == 10
        True
        >>> axioms[0][0]
        'zfc_extensionality'
    """
    A = Variable(0, sort=SetType)
    B = Variable(1, sort=SetType)
    x = Variable(2, sort=ElemSort)
    y = Variable(3, sort=ElemSort)
    z = Variable(4, sort=ElemSort)

    empty_set = Constant("empty_set", sort=SetType)

    in_xA = PredicateApp("in_set", 2, (x, A))
    in_xB = PredicateApp("in_set", 2, (x, B))

    # 1. zfc_extensionality: forall A forall B, (A = B <=> forall x, (x in A <=> x in B))
    zfc_extensionality = Forall(
        A,
        Forall(
            B,
            Iff(
                Equality(A, B),
                Forall(x, Iff(in_xA, in_xB)),
            ),
        ),
    )

    # 2. zfc_subset_def: forall A forall B, (A <= B <=> forall x, (x in A => x in B))
    sub_AB = PredicateApp("subset", 2, (A, B))
    zfc_subset_def = Forall(
        A,
        Forall(
            B,
            Iff(sub_AB, Forall(x, Implies(in_xA, in_xB))),
        ),
    )

    # 3. zfc_empty_set: forall x, ~(x in empty_set)
    in_x_empty = PredicateApp("in_set", 2, (x, empty_set))
    zfc_empty_set = Forall(x, Not(in_x_empty))

    # 4. zfc_pairing: forall x forall y forall z, (z in pair(x, y) <=> (z = x | z = y))
    pair_xy = FunctionApp("pair", 2, (x, y), return_sort=SetType)
    in_z_pair = PredicateApp("in_set", 2, (z, pair_xy))
    zfc_pairing = Forall(
        x,
        Forall(
            y,
            Forall(z, Iff(in_z_pair, Or(Equality(z, x), Equality(z, y)))),
        ),
    )

    # 5. zfc_singleton: forall x forall y, (y in singleton(x) <=> y = x)
    sing_x = FunctionApp("singleton", 1, (x,), return_sort=SetType)
    in_y_sing = PredicateApp("in_set", 2, (y, sing_x))
    zfc_singleton = Forall(
        x,
        Forall(y, Iff(in_y_sing, Equality(y, x))),
    )

    # 6. zfc_union_def: forall A forall B forall x, (x in union(A, B) <=> (x in A | x in B))
    union_AB = FunctionApp("union", 2, (A, B), return_sort=SetType)
    in_x_union = PredicateApp("in_set", 2, (x, union_AB))
    zfc_union_def = Forall(
        A,
        Forall(
            B,
            Forall(x, Iff(in_x_union, Or(in_xA, in_xB))),
        ),
    )

    # 7. zfc_inter_def: forall A forall B forall x, (x in inter(A, B) <=> (x in A & x in B))
    inter_AB = FunctionApp("inter", 2, (A, B), return_sort=SetType)
    in_x_inter = PredicateApp("in_set", 2, (x, inter_AB))
    zfc_inter_def = Forall(
        A,
        Forall(
            B,
            Forall(x, Iff(in_x_inter, And(in_xA, in_xB))),
        ),
    )

    # 8. zfc_diff_def: forall A forall B forall x, (x in diff(A, B) <=> (x in A & ~(x in B)))
    diff_AB = FunctionApp("diff", 2, (A, B), return_sort=SetType)
    in_x_diff = PredicateApp("in_set", 2, (x, diff_AB))
    zfc_diff_def = Forall(
        A,
        Forall(
            B,
            Forall(x, Iff(in_x_diff, And(in_xA, Not(in_xB)))),
        ),
    )

    # 9. zfc_powerset_def: forall A forall B, (B in powerset(A) <=> B <= A)
    pset_A = FunctionApp("powerset", 1, (A,), return_sort=SetSort(SetType))
    in_B_pset = PredicateApp("in_set", 2, (B, pset_A))
    sub_BA = PredicateApp("subset", 2, (B, A))
    zfc_powerset_def = Forall(
        A,
        Forall(B, Iff(in_B_pset, sub_BA)),
    )

    # 10. zfc_choice_axiom: forall A, (~(A = empty_set) => choice(A) in A)
    choice_A = FunctionApp("choice", 1, (A,), return_sort=ElemSort)
    in_choice_A = PredicateApp("in_set", 2, (choice_A, A))
    zfc_choice_axiom = Forall(
        A,
        Implies(Not(Equality(A, empty_set)), in_choice_A),
    )

    return [
        ("zfc_extensionality", zfc_extensionality),
        ("zfc_subset_def", zfc_subset_def),
        ("zfc_empty_set", zfc_empty_set),
        ("zfc_pairing", zfc_pairing),
        ("zfc_singleton", zfc_singleton),
        ("zfc_union_def", zfc_union_def),
        ("zfc_inter_def", zfc_inter_def),
        ("zfc_diff_def", zfc_diff_def),
        ("zfc_powerset_def", zfc_powerset_def),
        ("zfc_choice_axiom", zfc_choice_axiom),
    ]


def get_set_theory_axioms() -> List[Tuple[str, Formula]]:
    """Generates foundational Set Theory axioms.

    Returns:
        List[Tuple[str, Formula]]: List of (axiom_name, formula) pairs for set theory.

    Example:
        >>> axioms = get_set_theory_axioms()
        >>> len(axioms) == 8
        True
        >>> axioms[0][0]
        'set_extensionality'
    """
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


# Instantiated Theory object
zfc_theory: Theory = Theory(
    name="zfc",
    description="Zermelo-Fraenkel Set Theory with Axiom of Choice (extensionality, empty set, union, powerset, choice).",
    sorts={"Elem": ElemSort, "Set": SetType},
    signature=get_zfc_signature(),
    axioms=dict(get_zfc_axioms()),
)
register_theory(zfc_theory)
