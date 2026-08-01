"""Binary relation theory axioms (reflexivity, symmetry, transitivity, irreflexivity)."""

from __future__ import annotations
from typing import List, Tuple

from solver.core.ast import (
    Formula, Variable, PredicateApp, Equality, Forall, Implies, And, Not
)
from solver.core.sorts import PrimitiveSort
from solver.core.signature import Signature

RelElem: PrimitiveSort = PrimitiveSort("RelElem")


def get_relation_signature() -> Signature:
    """Returns the signature declaring binary relation predicate R and EqRel."""
    sig = Signature()
    sig.register_predicate("R", 2, (RelElem, RelElem))
    sig.register_predicate("EqRel", 2, (RelElem, RelElem))
    return sig


def get_relation_axioms() -> List[Tuple[str, Formula]]:
    """Returns relation property axioms: reflexivity, symmetry, transitivity, anti-symmetry, irreflexivity, asymmetry."""
    x = Variable(0, sort=RelElem)
    y = Variable(1, sort=RelElem)
    z = Variable(2, sort=RelElem)

    r_xx = PredicateApp("R", 2, (x, x))
    r_xy = PredicateApp("R", 2, (x, y))
    r_yx = PredicateApp("R", 2, (y, x))
    r_yz = PredicateApp("R", 2, (y, z))
    r_xz = PredicateApp("R", 2, (x, z))

    # 1. rel_reflexive: forall x, R(x, x)
    rel_reflexive = Forall(x, r_xx)

    # 2. rel_symmetric: forall x y, (R(x, y) => R(y, x))
    rel_symmetric = Forall(x, Forall(y, Implies(r_xy, r_yx)))

    # 3. rel_transitive: forall x y z, ((R(x, y) & R(y, z)) => R(x, z))
    rel_transitive = Forall(
        x,
        Forall(
            y,
            Forall(z, Implies(And(r_xy, r_yz), r_xz)),
        ),
    )

    # 4. rel_antisymmetric: forall x y, ((R(x, y) & R(y, x)) => x = y)
    rel_antisymmetric = Forall(
        x,
        Forall(y, Implies(And(r_xy, r_yx), Equality(x, y))),
    )

    # 5. rel_irreflexive: forall x, ~R(x, x)
    rel_irreflexive = Forall(x, Not(r_xx))

    # 6. rel_asymmetric: forall x y, (R(x, y) => ~R(y, x))
    rel_asymmetric = Forall(x, Forall(y, Implies(r_xy, Not(r_yx))))

    return [
        ("rel_reflexive", rel_reflexive),
        ("rel_symmetric", rel_symmetric),
        ("rel_transitive", rel_transitive),
        ("rel_antisymmetric", rel_antisymmetric),
        ("rel_irreflexive", rel_irreflexive),
        ("rel_asymmetric", rel_asymmetric),
    ]
