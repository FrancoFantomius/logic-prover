"""Knowledge base module providing foundational logic, arithmetic, group, relation, order, set, and function axioms."""

from __future__ import annotations
from typing import List, Tuple

from logic_prover.core.ast import Formula
from logic_prover.core.signature import Signature
from logic_prover.kb.equality import get_equality_axioms, get_equality_signature
from logic_prover.kb.logic import get_fol_axioms, get_fol_signature
from logic_prover.kb.numbers import get_peano_axioms, get_peano_signature
from logic_prover.kb.groups import get_group_axioms, get_group_signature
from logic_prover.kb.relations import get_relation_axioms, get_relation_signature
from logic_prover.kb.orders import get_partial_order_axioms, get_total_order_axioms, get_order_signature
from logic_prover.kb.sets import get_set_theory_axioms, get_set_signature
from logic_prover.kb.functions import get_function_axioms, get_function_signature


def get_extended_axioms() -> List[Tuple[str, Formula, str]]:
    """Retrieves all extended mathematical domain axioms with category tags.

    Collects axioms across algebra (groups), binary relations, orderings,
    axiomatic set theory, and function theory.

    Returns:
        List[Tuple[str, Formula, str]]: List of (name, formula, category) tuples.

    Example:
        >>> axioms = get_extended_axioms()
        >>> len(axioms) > 0
        True
        >>> axioms[0][2] in ("groups", "relations", "orders", "sets", "functions")
        True
    """
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
    """Retrieves the complete standard axiom library combining foundational and extended domains.

    Merges equality schemata, first-order logic axioms, Peano arithmetic axioms,
    and all extended mathematical theory axioms.

    Returns:
        List[Tuple[str, Formula, str]]: List of (name, formula, category) tuples representing all axioms.

    Example:
        >>> all_ax = get_all_axioms()
        >>> any(name == "eq_reflexive" for name, _, _ in all_ax)
        True
    """
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
    """Constructs and returns the union signature across all supported axiom domains.

    Merges symbols for equality, first-order logic, Peano arithmetic, group theory,
    relations, partial/total orders, set theory, and functions.

    Returns:
        Signature: A comprehensive Signature instance containing all registered symbols and constructors.

    Example:
        >>> sig = get_combined_signature()
        >>> sig.has_symbol("eq") or sig.has_symbol("add") or sig.has_symbol("succ")
        True
    """
    sig = get_equality_signature()
    sig = sig.merge(get_fol_signature())
    sig = sig.merge(get_peano_signature())
    sig = sig.merge(get_group_signature())
    sig = sig.merge(get_relation_signature())
    sig = sig.merge(get_order_signature())
    sig = sig.merge(get_set_signature())
    sig = sig.merge(get_function_signature())
    return sig
