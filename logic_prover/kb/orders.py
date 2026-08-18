"""Order theory axioms (partial orders, total orders, strict orders)."""

from __future__ import annotations
from typing import List, Tuple

from logic_prover.core.ast import (
    Formula, Variable, PredicateApp, Equality, Forall, Implies, And, Or, Not, Iff
)
from logic_prover.core.sorts import PrimitiveSort, Ind
from logic_prover.core.signature import Signature

OrderElem: PrimitiveSort = PrimitiveSort("OrderElem")


def get_order_signature() -> Signature:
    """Constructs the signature declaring order relation predicates 'le', 'lt', and 'ge'.

    Returns:
        Signature: The initialized order theory Signature instance.

    Example:
        >>> sig = get_order_signature()
        >>> sig.has_symbol("le") and sig.has_symbol("lt") and sig.has_symbol("ge")
        True
    """
    sig = Signature()
    sig.register_predicate("le", 2, (Ind, Ind))
    sig.register_predicate("lt", 2, (Ind, Ind))
    sig.register_predicate("ge", 2, (Ind, Ind))
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

    Includes:
    - All partial order axioms (po_reflexive, po_antisymmetric, po_transitive, po_lt_def)
    - to_totality: ∀x, y. (x ≤ y ∨ y ≤ x)
    - to_trichotomy: ∀x, y. (x < y ∨ x = y ∨ y < x)

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
