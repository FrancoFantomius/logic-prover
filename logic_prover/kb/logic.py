"""First-Order Logic foundational axioms and tautologies."""

from __future__ import annotations
from typing import List, Tuple

from logic.core.ast import (
    Formula, Variable, PredicateApp, Not, And, Or, Implies, Iff, Forall, Exists
)
from logic.core.sorts import Ind
from logic.core.signature import Signature


def get_fol_signature() -> Signature:
    """Returns signature declaring sample predicate symbols for FOL schemata."""
    sig = Signature()
    sig.register_predicate("P", 1, (Ind,))
    sig.register_predicate("Q", 1, (Ind,))
    return sig


def get_fol_axioms() -> List[Tuple[str, Formula]]:
    """Returns First-Order Logic axioms: propositional schemata and quantifier laws."""
    x = Variable(0, sort=Ind)
    y = Variable(1, sort=Ind)

    px = PredicateApp("P", 1, (x,))
    qx = PredicateApp("Q", 1, (x,))
    py = PredicateApp("P", 1, (y,))

    # 1. prop_impl_self: forall x, P(x) => P(x)
    prop_impl_self = Forall(x, Implies(px, px))

    # 2. prop_and_elim_left: forall x, (P(x) & Q(x)) => P(x)
    prop_and_elim_left = Forall(x, Implies(And(px, qx), px))

    # 3. prop_and_elim_right: forall x, (P(x) & Q(x)) => Q(x)
    prop_and_elim_right = Forall(x, Implies(And(px, qx), qx))

    # 4. prop_or_intro_left: forall x, P(x) => (P(x) | Q(x))
    prop_or_intro_left = Forall(x, Implies(px, Or(px, qx)))

    # 5. prop_double_negation: forall x, ~~P(x) => P(x)
    prop_double_negation = Forall(x, Implies(Not(Not(px)), px))

    # 6. quant_forall_elim: forall x, P(x) => P(x)
    quant_forall_elim = Forall(x, Implies(px, px))

    # 7. quant_exists_intro: forall x, (P(x) => exists y, P(y))
    quant_exists_intro = Forall(x, Implies(px, Exists(y, py)))

    # 8. quant_de_morgan_1: forall x, (~ exists y, P(y) <=> forall y, ~P(y))
    not_exists_py = Not(Exists(y, py))
    forall_not_py = Forall(y, Not(py))
    quant_de_morgan_1 = Forall(x, Iff(not_exists_py, forall_not_py))

    return [
        ("prop_impl_self", prop_impl_self),
        ("prop_and_elim_left", prop_and_elim_left),
        ("prop_and_elim_right", prop_and_elim_right),
        ("prop_or_intro_left", prop_or_intro_left),
        ("prop_double_negation", prop_double_negation),
        ("quant_forall_elim", quant_forall_elim),
        ("quant_exists_intro", quant_exists_intro),
        ("quant_de_morgan_1", quant_de_morgan_1),
    ]
