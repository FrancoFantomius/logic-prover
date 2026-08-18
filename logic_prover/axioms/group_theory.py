"""Group theory axioms, signatures, and formal Theory definitions."""

from __future__ import annotations
from typing import List, Tuple

from logic_prover.core.ast import Formula, Variable, Constant, FunctionApp, Equality, Forall, Implies
from logic_prover.core.sorts import PrimitiveSort
from logic_prover.core.signature import Signature
from logic_prover.axioms.base import Theory, register_theory

GroupElem: PrimitiveSort = PrimitiveSort("GroupElem")


def get_group_signature() -> Signature:
    """Constructs the logical signature for First-Order Group Theory.

    Registers constant identity 'e', binary operation 'op', and unary inverse 'inv'
    over sort GroupElem.

    Returns:
        Signature: The initialized group theory Signature instance.

    Example:
        >>> sig = get_group_signature()
        >>> sig.has_symbol("e") and sig.has_symbol("op") and sig.has_symbol("inv")
        True
    """
    sig = Signature()
    sig.register_constant("e", GroupElem)
    sig.register_function("op", 2, (GroupElem, GroupElem), GroupElem)
    sig.register_function("inv", 1, (GroupElem,), GroupElem)
    return sig


def get_group_theory_signature() -> Signature:
    """Alias for get_group_signature constructing the group theory signature.

    Returns:
        Signature: The initialized group theory Signature instance.

    Example:
        >>> sig = get_group_theory_signature()
        >>> sig.has_symbol("op")
        True
    """
    return get_group_signature()


def get_group_axioms() -> List[Tuple[str, Formula]]:
    """Generates the fundamental First-Order Group Theory axioms.

    Axioms:
    - group_assoc: ∀x, y, z. op(op(x, y), z) = op(x, op(y, z))
    - group_identity_left: ∀x. op(e, x) = x
    - group_identity_right: ∀x. op(x, e) = x
    - group_inverse_left: ∀x. op(inv(x), x) = e
    - group_inverse_right: ∀x. op(x, inv(x)) = e

    Returns:
        List[Tuple[str, Formula]]: List of (axiom_name, formula) pairs for group theory.

    Example:
        >>> axioms = get_group_axioms()
        >>> len(axioms) == 5
        True
        >>> axioms[0][0]
        'group_assoc'
    """
    v0 = Variable(0, sort=GroupElem)
    v1 = Variable(1, sort=GroupElem)
    v2 = Variable(2, sort=GroupElem)
    e = Constant("e", sort=GroupElem)

    inv_v0 = FunctionApp("inv", 1, (v0,), return_sort=GroupElem)

    op_v0_v1 = FunctionApp("op", 2, (v0, v1), return_sort=GroupElem)
    op_v1_v2 = FunctionApp("op", 2, (v1, v2), return_sort=GroupElem)

    # 1. group_assoc: forall x y z, op(op(x, y), z) = op(x, op(y, z))
    group_assoc = Forall(
        v0,
        Forall(
            v1,
            Forall(
                v2,
                Equality(
                    FunctionApp("op", 2, (op_v0_v1, v2), return_sort=GroupElem),
                    FunctionApp("op", 2, (v0, op_v1_v2), return_sort=GroupElem),
                ),
            ),
        ),
    )

    # 2. group_identity_left: forall x, op(e, x) = x
    group_identity_left = Forall(
        v0,
        Equality(FunctionApp("op", 2, (e, v0), return_sort=GroupElem), v0),
    )

    # 3. group_identity_right: forall x, op(x, e) = x
    group_identity_right = Forall(
        v0,
        Equality(FunctionApp("op", 2, (v0, e), return_sort=GroupElem), v0),
    )

    # 4. group_inverse_left: forall x, op(inv(x), x) = e
    group_inverse_left = Forall(
        v0,
        Equality(FunctionApp("op", 2, (inv_v0, v0), return_sort=GroupElem), e),
    )

    # 5. group_inverse_right: forall x, op(x, inv(x)) = e
    group_inverse_right = Forall(
        v0,
        Equality(FunctionApp("op", 2, (v0, inv_v0), return_sort=GroupElem), e),
    )

    return [
        ("group_assoc", group_assoc),
        ("group_identity_left", group_identity_left),
        ("group_identity_right", group_identity_right),
        ("group_inverse_left", group_inverse_left),
        ("group_inverse_right", group_inverse_right),
    ]


def get_abelian_group_axioms() -> List[Tuple[str, Formula]]:
    """Generates the Abelian (Commutative) Group Theory axioms.

    Extends basic group axioms with commutativity:
    - group_commutative: ∀x, y. op(x, y) = op(y, x)

    Returns:
        List[Tuple[str, Formula]]: List of (axiom_name, formula) pairs for abelian groups.

    Example:
        >>> axioms = get_abelian_group_axioms()
        >>> len(axioms) == 6
        True
    """
    axioms = get_group_axioms()
    v0 = Variable(0, sort=GroupElem)
    v1 = Variable(1, sort=GroupElem)

    op_v0_v1 = FunctionApp("op", 2, (v0, v1), return_sort=GroupElem)
    op_v1_v0 = FunctionApp("op", 2, (v1, v0), return_sort=GroupElem)

    group_comm = Forall(v0, Forall(v1, Equality(op_v0_v1, op_v1_v0)))
    axioms.append(("group_commutative", group_comm))
    return axioms


# Instantiated Theory objects
group_theory: Theory = Theory(
    name="group_theory",
    description="First-order theory of groups with associativity, left/right identity, and left/right inverse.",
    sorts={"GroupElem": GroupElem},
    signature=get_group_signature(),
    axioms=dict(get_group_axioms()),
)
register_theory(group_theory)

abelian_group_theory: Theory = Theory(
    name="abelian_group_theory",
    description="First-order theory of abelian groups with commutativity.",
    sorts={"GroupElem": GroupElem},
    signature=get_group_signature(),
    axioms=dict(get_abelian_group_axioms()),
)
register_theory(abelian_group_theory)
