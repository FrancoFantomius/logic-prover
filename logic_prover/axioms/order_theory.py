"""Order theory and lattice axioms, signatures, and Theory definitions."""

from __future__ import annotations
from typing import List, Tuple

from logic_prover.core.ast import (
    Formula, Variable, PredicateApp, FunctionApp, Equality, Forall, Implies, And, Or, Not, Iff
)
from logic_prover.core.sorts import PrimitiveSort, Ind
from logic_prover.core.signature import Signature
from logic_prover.axioms.base import Theory, register_theory

OrderElem: PrimitiveSort = PrimitiveSort("OrderElem")


def get_order_signature() -> Signature:
    """Constructs the signature declaring order relation predicates and lattice operations.

    Registers predicates 'le', 'lt', 'ge' and binary lattice operations 'meet', 'join'.

    Returns:
        Signature: The initialized order theory Signature instance.

    Example:
        >>> sig = get_order_signature()
        >>> sig.has_symbol("le") and sig.has_symbol("lt") and sig.has_symbol("meet")
        True
    """
    sig = Signature()
    sig.register_predicate("le", 2, (Ind, Ind))
    sig.register_predicate("lt", 2, (Ind, Ind))
    sig.register_predicate("ge", 2, (Ind, Ind))
    sig.register_function("meet", 2, (OrderElem, OrderElem), OrderElem)
    sig.register_function("join", 2, (OrderElem, OrderElem), OrderElem)
    return sig


def get_partial_order_axioms() -> List[Tuple[str, Formula]]:
    """Generates the fundamental Partial Order theory axioms.

    Includes:
    - po_reflexive: ∀x. x ≤ x
    - po_antisymmetric: ∀x, y. ((x ≤ y ∧ y ≤ x) ⇒ x = y)
    - po_transitive: ∀x, y, z. ((x ≤ y ∧ y ≤ z) ⇒ x ≤ z)
    - po_lt_def: ∀x, y. (x < y ⇔ (x ≤ y ∧ ¬(x = y)))

    Returns:
        List[Tuple[str, Formula]]: List of (axiom_name, formula) pairs for partial orders.

    Example:
        >>> axioms = get_partial_order_axioms()
        >>> len(axioms) == 4
        True
        >>> axioms[0][0]
        'po_reflexive'
    """
    x = Variable(0, sort=OrderElem)
    y = Variable(1, sort=OrderElem)
    z = Variable(2, sort=OrderElem)

    le_xx = PredicateApp("le", 2, (x, x))
    le_xy = PredicateApp("le", 2, (x, y))
    le_yx = PredicateApp("le", 2, (y, x))
    le_yz = PredicateApp("le", 2, (y, z))
    le_xz = PredicateApp("le", 2, (x, z))
    lt_xy = PredicateApp("lt", 2, (x, y))

    # 1. po_reflexive: forall x, le(x, x)
    po_reflexive = Forall(x, le_xx)

    # 2. po_antisymmetric: forall x y, ((le(x, y) & le(y, x)) => x = y)
    po_antisymmetric = Forall(
        x,
        Forall(y, Implies(And(le_xy, le_yx), Equality(x, y))),
    )

    # 3. po_transitive: forall x y z, ((le(x, y) & le(y, z)) => le(x, z))
    po_transitive = Forall(
        x,
        Forall(
            y,
            Forall(z, Implies(And(le_xy, le_yz), le_xz)),
        ),
    )

    # 4. po_lt_def: forall x y, (lt(x, y) <=> (le(x, y) & ~(x = y)))
    po_lt_def = Forall(
        x,
        Forall(y, Iff(lt_xy, And(le_xy, Not(Equality(x, y))))),
    )

    return [
        ("po_reflexive", po_reflexive),
        ("po_antisymmetric", po_antisymmetric),
        ("po_transitive", po_transitive),
        ("po_lt_def", po_lt_def),
    ]


def get_total_order_axioms() -> List[Tuple[str, Formula]]:
    """Generates Total Order axioms combining partial order axioms with totality and trichotomy.

    Returns:
        List[Tuple[str, Formula]]: List of (axiom_name, formula) pairs for total orders.

    Example:
        >>> axioms = get_total_order_axioms()
        >>> len(axioms) == 6
        True
    """
    axioms = get_partial_order_axioms()

    x = Variable(0, sort=OrderElem)
    y = Variable(1, sort=OrderElem)

    le_xy = PredicateApp("le", 2, (x, y))
    le_yx = PredicateApp("le", 2, (y, x))
    lt_xy = PredicateApp("lt", 2, (x, y))
    lt_yx = PredicateApp("lt", 2, (y, x))

    # 5. to_totality: forall x y, (le(x, y) | le(y, x))
    to_totality = Forall(x, Forall(y, Or(le_xy, le_yx)))

    # 6. to_trichotomy: forall x y, (lt(x, y) | x = y | lt(y, x))
    to_trichotomy = Forall(
        x,
        Forall(
            y,
            Or(Or(lt_xy, Equality(x, y)), lt_yx),
        ),
    )

    axioms.extend([
        ("to_totality", to_totality),
        ("to_trichotomy", to_trichotomy),
    ])
    return axioms


def get_lattice_axioms() -> List[Tuple[str, Formula]]:
    """Generates the algebraic Lattice Theory axioms (meet, join, commutativity, associativity, absorption).

    Returns:
        List[Tuple[str, Formula]]: List of (axiom_name, formula) pairs for lattices.

    Example:
        >>> axioms = get_lattice_axioms()
        >>> len(axioms) == 6
        True
        >>> axioms[0][0]
        'lat_meet_comm'
    """
    x = Variable(0, sort=OrderElem)
    y = Variable(1, sort=OrderElem)
    z = Variable(2, sort=OrderElem)

    meet_xy = FunctionApp("meet", 2, (x, y), return_sort=OrderElem)
    meet_yx = FunctionApp("meet", 2, (y, x), return_sort=OrderElem)
    join_xy = FunctionApp("join", 2, (x, y), return_sort=OrderElem)
    join_yx = FunctionApp("join", 2, (y, x), return_sort=OrderElem)

    # 1. lat_meet_comm: meet(x, y) = meet(y, x)
    lat_meet_comm = Forall(x, Forall(y, Equality(meet_xy, meet_yx)))

    # 2. lat_join_comm: join(x, y) = join(y, x)
    lat_join_comm = Forall(x, Forall(y, Equality(join_xy, join_yx)))

    # 3. lat_meet_assoc: meet(meet(x, y), z) = meet(x, meet(y, z))
    meet_yz = FunctionApp("meet", 2, (y, z), return_sort=OrderElem)
    lat_meet_assoc = Forall(
        x,
        Forall(
            y,
            Forall(
                z,
                Equality(
                    FunctionApp("meet", 2, (meet_xy, z), return_sort=OrderElem),
                    FunctionApp("meet", 2, (x, meet_yz), return_sort=OrderElem),
                ),
            ),
        ),
    )

    # 4. lat_join_assoc: join(join(x, y), z) = join(x, join(y, z))
    join_yz = FunctionApp("join", 2, (y, z), return_sort=OrderElem)
    lat_join_assoc = Forall(
        x,
        Forall(
            y,
            Forall(
                z,
                Equality(
                    FunctionApp("join", 2, (join_xy, z), return_sort=OrderElem),
                    FunctionApp("join", 2, (x, join_yz), return_sort=OrderElem),
                ),
            ),
        ),
    )

    # 5. lat_absorb_meet_join: meet(x, join(x, y)) = x
    join_xy_val = FunctionApp("join", 2, (x, y), return_sort=OrderElem)
    lat_absorb_meet_join = Forall(
        x,
        Forall(y, Equality(FunctionApp("meet", 2, (x, join_xy_val), return_sort=OrderElem), x)),
    )

    # 6. lat_absorb_join_meet: join(x, meet(x, y)) = x
    meet_xy_val = FunctionApp("meet", 2, (x, y), return_sort=OrderElem)
    lat_absorb_join_meet = Forall(
        x,
        Forall(y, Equality(FunctionApp("join", 2, (x, meet_xy_val), return_sort=OrderElem), x)),
    )

    return [
        ("lat_meet_comm", lat_meet_comm),
        ("lat_join_comm", lat_join_comm),
        ("lat_meet_assoc", lat_meet_assoc),
        ("lat_join_assoc", lat_join_assoc),
        ("lat_absorb_meet_join", lat_absorb_meet_join),
        ("lat_absorb_join_meet", lat_absorb_join_meet),
    ]


# Instantiated Theory objects
partial_order_theory: Theory = Theory(
    name="partial_order",
    description="First-order theory of partial orderings (reflexivity, antisymmetry, transitivity, strict order).",
    sorts={"OrderElem": OrderElem},
    signature=get_order_signature(),
    axioms=dict(get_partial_order_axioms()),
)
register_theory(partial_order_theory)

total_order_theory: Theory = Theory(
    name="total_order",
    description="First-order theory of total orderings (partial order with totality and trichotomy).",
    sorts={"OrderElem": OrderElem},
    signature=get_order_signature(),
    axioms=dict(get_total_order_axioms()),
)
register_theory(total_order_theory)

lattice_theory: Theory = Theory(
    name="lattice_theory",
    description="First-order algebraic lattice theory with meet, join, and absorption laws.",
    sorts={"OrderElem": OrderElem},
    signature=get_order_signature(),
    axioms=dict(get_lattice_axioms()),
)
register_theory(lattice_theory)
