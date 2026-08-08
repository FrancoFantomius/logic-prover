"""Knowledge base module providing foundational logic, arithmetic, group, relation, order, set, and function axioms."""

from __future__ import annotations
from typing import List, Tuple

from logic.core.ast import Formula
from logic.core.signature import Signature
from logic.kb.equality import get_equality_axioms, get_equality_signature
from logic.kb.logic import get_fol_axioms, get_fol_signature
from logic.kb.numbers import get_peano_axioms, get_peano_signature
from logic.kb.groups import get_group_axioms, get_group_signature
from logic.kb.relations import get_relation_axioms, get_relation_signature
from logic.kb.orders import get_partial_order_axioms, get_total_order_axioms, get_order_signature
from logic.kb.sets import get_set_theory_axioms, get_set_signature
from logic.kb.functions import get_function_axioms, get_function_signature


def get_extended_axioms() -> List[Tuple[str, Formula, str]]:
    """Returns all extended axioms with category tags ('groups', 'relations', 'orders', 'sets', 'functions')."""
    extended_axioms: List[Tuple[str, Formula, str]] = []

    for name, formula in get_group_axioms():
        extended_axioms.append((name, formula, "groups"))

    for name, formula in get_relation_axioms():
        extended_axioms.append((name, formula, "relations"))

    for name, formula in get_total_order_axioms():
        extended_axioms.append((name, formula, "orders"))

    for name, formula in get_set_theory_axioms():
        extended_axioms.append((name, formula, "sets"))

    for name, formula in get_function_axioms():
        extended_axioms.append((name, formula, "functions"))

    return extended_axioms


def get_all_axioms() -> List[Tuple[str, Formula, str]]:
    """Returns complete library axiom set combining foundational and extended domains."""
    all_axioms: List[Tuple[str, Formula, str]] = []

    for name, formula in get_equality_axioms():
        all_axioms.append((name, formula, "equality"))

    for name, formula in get_fol_axioms():
        all_axioms.append((name, formula, "logic"))

    for name, formula in get_peano_axioms():
        all_axioms.append((name, formula, "peano"))

    all_axioms.extend(get_extended_axioms())

    return all_axioms


def get_combined_signature() -> Signature:
    """Merges signatures across all foundational and extended axiom domains."""
    sig = get_equality_signature()
    sig = sig.merge(get_fol_signature())
    sig = sig.merge(get_peano_signature())
    sig = sig.merge(get_group_signature())
    sig = sig.merge(get_relation_signature())
    sig = sig.merge(get_order_signature())
    sig = sig.merge(get_set_signature())
    sig = sig.merge(get_function_signature())
    return sig
