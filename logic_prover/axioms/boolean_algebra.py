"""Boolean algebra axioms, signature, and Theory definitions."""

from __future__ import annotations
from typing import List, Tuple

from logic_prover.core.ast import Formula, Variable, Constant, FunctionApp, Equality, Forall
from logic_prover.core.sorts import PrimitiveSort
from logic_prover.core.signature import Signature
from logic_prover.axioms.base import Theory, register_theory

BoolElem: PrimitiveSort = PrimitiveSort("BoolElem")


def get_boolean_algebra_signature() -> Signature:
    """Constructs the signature declaring Boolean Algebra operations and bounds.

    Registers constants 'bot', 'top', binary operations 'bmeet', 'bjoin', and unary complement 'bneg'.

    Returns:
        Signature: The initialized Boolean Algebra Signature instance.

    Example:
        >>> sig = get_boolean_algebra_signature()
        >>> sig.has_symbol("bmeet") and sig.has_symbol("bjoin") and sig.has_symbol("bneg")
        True
    """
    sig = Signature()
    sig.register_constant("bot", BoolElem)
    sig.register_constant("top", BoolElem)
    sig.register_function("bmeet", 2, (BoolElem, BoolElem), BoolElem)
    sig.register_function("bjoin", 2, (BoolElem, BoolElem), BoolElem)
    sig.register_function("bneg", 1, (BoolElem,), BoolElem)
    return sig


def get_boolean_algebra_axioms() -> List[Tuple[str, Formula]]:
    """Generates the First-Order Boolean Algebra axioms.

    Includes:
    - Commutativity and associativity of meet and join
    - Distributivity of meet over join and join over meet
    - Identity laws for top and bot
    - Complementation laws
    - De Morgan's dual laws

    Returns:
        List[Tuple[str, Formula]]: List of (axiom_name, formula) pairs for boolean algebra.

    Example:
        >>> axioms = get_boolean_algebra_axioms()
        >>> len(axioms) == 12
        True
        >>> axioms[0][0]
        'bool_meet_comm'
    """
    bot = Constant("bot", sort=BoolElem)
    top = Constant("top", sort=BoolElem)

    x = Variable(0, sort=BoolElem)
    y = Variable(1, sort=BoolElem)
    z = Variable(2, sort=BoolElem)

    meet_xy = FunctionApp("bmeet", 2, (x, y), return_sort=BoolElem)
    meet_yx = FunctionApp("bmeet", 2, (y, x), return_sort=BoolElem)
    join_xy = FunctionApp("bjoin", 2, (x, y), return_sort=BoolElem)
    join_yx = FunctionApp("bjoin", 2, (y, x), return_sort=BoolElem)

    # 1. bool_meet_comm: bmeet(x, y) = bmeet(y, x)
    bool_meet_comm = Forall(x, Forall(y, Equality(meet_xy, meet_yx)))

    # 2. bool_join_comm: bjoin(x, y) = bjoin(y, x)
    bool_join_comm = Forall(x, Forall(y, Equality(join_xy, join_yx)))

    # 3. bool_meet_assoc: bmeet(bmeet(x, y), z) = bmeet(x, bmeet(y, z))
    meet_yz = FunctionApp("bmeet", 2, (y, z), return_sort=BoolElem)
    bool_meet_assoc = Forall(
        x,
        Forall(
            y,
            Forall(
                z,
                Equality(
                    FunctionApp("bmeet", 2, (meet_xy, z), return_sort=BoolElem),
                    FunctionApp("bmeet", 2, (x, meet_yz), return_sort=BoolElem),
                ),
            ),
        ),
    )

    # 4. bool_join_assoc: bjoin(bjoin(x, y), z) = bjoin(x, bjoin(y, z))
    join_yz = FunctionApp("bjoin", 2, (y, z), return_sort=BoolElem)
    bool_join_assoc = Forall(
        x,
        Forall(
            y,
            Forall(
                z,
                Equality(
                    FunctionApp("bjoin", 2, (join_xy, z), return_sort=BoolElem),
                    FunctionApp("bjoin", 2, (x, join_yz), return_sort=BoolElem),
                ),
            ),
        ),
    )

    # 5. bool_distrib_meet: bmeet(x, bjoin(y, z)) = bjoin(bmeet(x, y), bmeet(x, z))
    bjoin_yz = FunctionApp("bjoin", 2, (y, z), return_sort=BoolElem)
    bmeet_x_join_yz = FunctionApp("bmeet", 2, (x, bjoin_yz), return_sort=BoolElem)
    bmeet_xz = FunctionApp("bmeet", 2, (x, z), return_sort=BoolElem)
    bjoin_meet_xy_meet_xz = FunctionApp("bjoin", 2, (meet_xy, bmeet_xz), return_sort=BoolElem)
    bool_distrib_meet = Forall(x, Forall(y, Forall(z, Equality(bmeet_x_join_yz, bjoin_meet_xy_meet_xz))))

    # 6. bool_distrib_join: bjoin(x, bmeet(y, z)) = bmeet(bjoin(x, y), bjoin(x, z))
    bmeet_yz = FunctionApp("bmeet", 2, (y, z), return_sort=BoolElem)
    bjoin_x_meet_yz = FunctionApp("bjoin", 2, (x, bmeet_yz), return_sort=BoolElem)
    bjoin_xz = FunctionApp("bjoin", 2, (x, z), return_sort=BoolElem)
    bmeet_join_xy_join_xz = FunctionApp("bmeet", 2, (join_xy, bjoin_xz), return_sort=BoolElem)
    bool_distrib_join = Forall(x, Forall(y, Forall(z, Equality(bjoin_x_meet_yz, bmeet_join_xy_join_xz))))

    # 7. bool_meet_top: bmeet(x, top) = x
    meet_x_top = FunctionApp("bmeet", 2, (x, top), return_sort=BoolElem)
    bool_meet_top = Forall(x, Equality(meet_x_top, x))

    # 8. bool_join_bot: bjoin(x, bot) = x
    join_x_bot = FunctionApp("bjoin", 2, (x, bot), return_sort=BoolElem)
    bool_join_bot = Forall(x, Equality(join_x_bot, x))

    # 9. bool_complement_meet: bmeet(x, bneg(x)) = bot
    neg_x = FunctionApp("bneg", 1, (x,), return_sort=BoolElem)
    meet_x_negx = FunctionApp("bmeet", 2, (x, neg_x), return_sort=BoolElem)
    bool_complement_meet = Forall(x, Equality(meet_x_negx, bot))

    # 10. bool_complement_join: bjoin(x, bneg(x)) = top
    join_x_negx = FunctionApp("bjoin", 2, (x, neg_x), return_sort=BoolElem)
    bool_complement_join = Forall(x, Equality(join_x_negx, top))

    # 11. bool_de_morgan_meet: bneg(bmeet(x, y)) = bjoin(bneg(x), bneg(y))
    neg_meet_xy = FunctionApp("bneg", 1, (meet_xy,), return_sort=BoolElem)
    neg_y = FunctionApp("bneg", 1, (y,), return_sort=BoolElem)
    join_negx_negy = FunctionApp("bjoin", 2, (neg_x, neg_y), return_sort=BoolElem)
    bool_de_morgan_meet = Forall(x, Forall(y, Equality(neg_meet_xy, join_negx_negy)))

    # 12. bool_de_morgan_join: bneg(bjoin(x, y)) = bmeet(bneg(x), bneg(y))
    neg_join_xy = FunctionApp("bneg", 1, (join_xy,), return_sort=BoolElem)
    meet_negx_negy = FunctionApp("bmeet", 2, (neg_x, neg_y), return_sort=BoolElem)
    bool_de_morgan_join = Forall(x, Forall(y, Equality(neg_join_xy, meet_negx_negy)))

    return [
        ("bool_meet_comm", bool_meet_comm),
        ("bool_join_comm", bool_join_comm),
        ("bool_meet_assoc", bool_meet_assoc),
        ("bool_join_assoc", bool_join_assoc),
        ("bool_distrib_meet", bool_distrib_meet),
        ("bool_distrib_join", bool_distrib_join),
        ("bool_meet_top", bool_meet_top),
        ("bool_join_bot", bool_join_bot),
        ("bool_complement_meet", bool_complement_meet),
        ("bool_complement_join", bool_complement_join),
        ("bool_de_morgan_meet", bool_de_morgan_meet),
        ("bool_de_morgan_join", bool_de_morgan_join),
    ]


# Instantiated Theory object
boolean_algebra_theory: Theory = Theory(
    name="boolean_algebra",
    description="First-order theory of Boolean algebras (bounded distributive lattices with complements and De Morgan identities).",
    sorts={"BoolElem": BoolElem},
    signature=get_boolean_algebra_signature(),
    axioms=dict(get_boolean_algebra_axioms()),
)
register_theory(boolean_algebra_theory)
