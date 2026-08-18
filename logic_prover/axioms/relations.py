"""Binary relation theory axioms, signatures, and Theory definitions."""

from __future__ import annotations
from typing import List, Tuple

from logic_prover.core.ast import Formula, Variable, PredicateApp, Equality, Forall, Implies, And, Not, Iff
from logic_prover.core.sorts import PrimitiveSort
from logic_prover.core.signature import Signature
from logic_prover.axioms.base import Theory, register_theory

RelElem: PrimitiveSort = PrimitiveSort("RelElem")


def get_relation_signature() -> Signature:
    """Constructs the signature declaring binary relation predicates 'R' and 'EqRel' over RelElem.

    Returns:
        Signature: The initialized binary relation Signature instance.

    Example:
        >>> sig = get_relation_signature()
        >>> sig.has_symbol("R") and sig.has_symbol("EqRel")
        True
    """
    sig = Signature()
    sig.register_predicate("R", 2, (RelElem, RelElem))
    sig.register_predicate("EqRel", 2, (RelElem, RelElem))
    return sig


def get_relation_axioms() -> List[Tuple[str, Formula]]:
    """Generates the fundamental binary relation property axioms.

    Includes:
    - rel_reflexive: ∀x. R(x, x)
    - rel_symmetric: ∀x, y. (R(x, y) ⇒ R(y, x))
    - rel_transitive: ∀x, y, z. ((R(x, y) ∧ R(y, z)) ⇒ R(x, z))
    - rel_antisymmetric: ∀x, y. ((R(x, y) ∧ R(y, x)) ⇒ x = y)
    - rel_irreflexive: ∀x. ¬R(x, x)
    - rel_asymmetric: ∀x, y. (R(x, y) ⇒ ¬R(y, x))

    Returns:
        List[Tuple[str, Formula]]: List of (axiom_name, formula) pairs for relation properties.

    Example:
        >>> axioms = get_relation_axioms()
        >>> len(axioms) == 6
        True
        >>> axioms[0][0]
        'rel_reflexive'
    """
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


def get_equivalence_relation_axioms() -> List[Tuple[str, Formula]]:
    """Generates the Equivalence Relation axioms (reflexivity, symmetry, transitivity).

    Returns:
        List[Tuple[str, Formula]]: List of (axiom_name, formula) pairs for equivalence relations.

    Example:
        >>> axioms = get_equivalence_relation_axioms()
        >>> len(axioms) == 3
        True
    """
    rel_map = dict(get_relation_axioms())
    return [
        ("eq_rel_reflexive", rel_map["rel_reflexive"]),
        ("eq_rel_symmetric", rel_map["rel_symmetric"]),
        ("eq_rel_transitive", rel_map["rel_transitive"]),
    ]


# Instantiated Theory objects
relation_theory: Theory = Theory(
    name="relations",
    description="First-order theory of binary relations (reflexivity, symmetry, transitivity, antisymmetry, etc.).",
    sorts={"RelElem": RelElem},
    signature=get_relation_signature(),
    axioms=dict(get_relation_axioms()),
)
register_theory(relation_theory)

equivalence_relation_theory: Theory = Theory(
    name="equivalence_relations",
    description="First-order theory of equivalence relations (reflexive, symmetric, transitive binary relations).",
    sorts={"RelElem": RelElem},
    signature=get_relation_signature(),
    axioms=dict(get_equivalence_relation_axioms()),
)
register_theory(equivalence_relation_theory)
