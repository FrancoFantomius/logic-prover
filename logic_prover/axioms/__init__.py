"""Axioms package classifying mathematical theories and foundational axioms."""

from __future__ import annotations
from typing import List, Tuple, Dict, Optional

from logic_prover.core.ast import Formula
from logic_prover.core.signature import Signature
from logic_prover.axioms.base import (
    Theory,
    register_theory,
    get_theory,
    list_theories,
    get_all_theories,
)
from logic_prover.axioms.equality import get_equality_axioms, get_equality_signature, equality_theory
from logic_prover.axioms.logic import get_fol_axioms, get_fol_signature, fol_theory
from logic_prover.axioms.peano import get_peano_axioms, get_peano_signature, peano_theory
from logic_prover.axioms.group_theory import (
    get_group_axioms,
    get_group_signature,
    get_group_theory_signature,
    get_abelian_group_axioms,
    group_theory,
    abelian_group_theory,
    GroupElem,
)
from logic_prover.axioms.relations import (
    get_relation_axioms,
    get_relation_signature,
    get_equivalence_relation_axioms,
    relation_theory,
    equivalence_relation_theory,
    RelElem,
)
from logic_prover.axioms.order_theory import (
    get_partial_order_axioms,
    get_total_order_axioms,
    get_lattice_axioms,
    get_order_signature,
    partial_order_theory,
    total_order_theory,
    lattice_theory,
    OrderElem,
)
from logic_prover.axioms.zfc import (
    get_zfc_axioms,
    get_zfc_signature,
    get_set_theory_axioms,
    get_set_signature,
    zfc_theory,
    SetElem,
    ElemSort,
    SetType,
)
from logic_prover.axioms.functions import (
    get_function_axioms,
    get_function_signature,
    function_theory,
    Dom,
    Codom,
    FuncSort,
)
from logic_prover.axioms.analysis import (
    get_analysis_axioms,
    get_analysis_signature,
    analysis_theory,
    Real,
)
from logic_prover.axioms.linear_algebra import (
    get_linear_algebra_axioms,
    get_linear_algebra_signature,
    linear_algebra_theory,
    Vector,
    Scalar,
)
from logic_prover.axioms.ring_theory import (
    get_ring_axioms,
    get_field_axioms,
    get_ring_signature,
    ring_theory,
    field_theory,
    RingElem,
)
from logic_prover.axioms.boolean_algebra import (
    get_boolean_algebra_axioms,
    get_boolean_algebra_signature,
    boolean_algebra_theory,
    BoolElem,
)


def get_extended_axioms() -> List[Tuple[str, Formula, str]]:
    """Retrieves all extended mathematical domain axioms with category tags.

    Collects axioms across algebra (groups, rings, linear algebra), relations, orderings,
    ZFC set theory, real analysis, boolean algebra, and functions.

    Returns:
        List[Tuple[str, Formula, str]]: List of (name, formula, category) tuples.

    Example:
        >>> axioms = get_extended_axioms()
        >>> len(axioms) > 0
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

    for name, formula in get_analysis_axioms():
        extended_axioms.append((name, formula, "analysis"))

    for name, formula in get_linear_algebra_axioms():
        extended_axioms.append((name, formula, "linear_algebra"))

    for name, formula in get_field_axioms():
        extended_axioms.append((name, formula, "fields"))

    for name, formula in get_boolean_algebra_axioms():
        extended_axioms.append((name, formula, "boolean_algebra"))

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
    """Constructs and returns the union signature across all supported mathematical theories.

    Merges symbols for equality, first-order logic, Peano arithmetic, group theory,
    relations, partial/total orders, set theory, functions, real analysis, linear algebra,
    ring theory, and boolean algebra.

    Returns:
        Signature: A comprehensive Signature instance containing all registered symbols and constructors.

    Example:
        >>> sig = get_combined_signature()
        >>> sig.has_symbol("eq") or sig.has_symbol("add") or sig.has_symbol("vadd")
        True
    """
    sig = get_equality_signature()
    sig = sig.merge(get_fol_signature())
    sig = sig.merge(get_peano_signature())
    sig = sig.merge(get_group_signature())
    sig = sig.merge(get_relation_signature())
    sig = sig.merge(get_order_signature())
    sig = sig.merge(get_zfc_signature())
    sig = sig.merge(get_function_signature())
    sig = sig.merge(get_analysis_signature())
    sig = sig.merge(get_linear_algebra_signature())
    sig = sig.merge(get_ring_signature())
    sig = sig.merge(get_boolean_algebra_signature())
    return sig


__all__ = [
    "Theory",
    "register_theory",
    "get_theory",
    "list_theories",
    "get_all_theories",
    # Specific Theory objects
    "group_theory",
    "abelian_group_theory",
    "peano_theory",
    "zfc_theory",
    "analysis_theory",
    "linear_algebra_theory",
    "ring_theory",
    "field_theory",
    "partial_order_theory",
    "total_order_theory",
    "lattice_theory",
    "boolean_algebra_theory",
    "relation_theory",
    "equivalence_relation_theory",
    "function_theory",
    "equality_theory",
    "fol_theory",
    # Axioms & Signatures
    "get_group_axioms",
    "get_group_signature",
    "get_group_theory_signature",
    "get_abelian_group_axioms",
    "get_peano_axioms",
    "get_peano_signature",
    "get_zfc_axioms",
    "get_zfc_signature",
    "get_set_theory_axioms",
    "get_set_signature",
    "get_analysis_axioms",
    "get_analysis_signature",
    "get_linear_algebra_axioms",
    "get_linear_algebra_signature",
    "get_ring_axioms",
    "get_field_axioms",
    "get_ring_signature",
    "get_partial_order_axioms",
    "get_total_order_axioms",
    "get_lattice_axioms",
    "get_order_signature",
    "get_boolean_algebra_axioms",
    "get_boolean_algebra_signature",
    "get_relation_axioms",
    "get_equivalence_relation_axioms",
    "get_relation_signature",
    "get_function_axioms",
    "get_function_signature",
    "get_equality_axioms",
    "get_equality_signature",
    "get_fol_axioms",
    "get_fol_signature",
    # Aggregate utilities
    "get_extended_axioms",
    "get_all_axioms",
    "get_combined_signature",
    # Sorts
    "GroupElem",
    "RelElem",
    "OrderElem",
    "SetElem",
    "ElemSort",
    "SetType",
    "Dom",
    "Codom",
    "FuncSort",
    "Real",
    "Vector",
    "Scalar",
    "RingElem",
    "BoolElem",
]
