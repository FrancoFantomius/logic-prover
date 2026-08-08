"""Group theory axioms (associativity, identity, inverse, commutativity)."""

from __future__ import annotations
from typing import List, Tuple

from logic.core.ast import Formula, Variable, Constant, FunctionApp, Equality, Forall
from logic.core.sorts import PrimitiveSort
from logic.core.signature import Signature

GroupElem: PrimitiveSort = PrimitiveSort("GroupElem")


def get_group_signature() -> Signature:
    """Returns the signature for group theory symbols (op, inv, e)."""
    sig = Signature()
    sig.register_constant("e", GroupElem)
    sig.register_function("op", 2, (GroupElem, GroupElem), GroupElem)
    sig.register_function("inv", 1, (GroupElem,), GroupElem)
    return sig


def get_group_axioms() -> List[Tuple[str, Formula]]:
    """Returns group theory axioms: associativity, left/right identity, left/right inverse."""
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
