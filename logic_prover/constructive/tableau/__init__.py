"""Semantic Tableaux with Kripke Semantics for Intuitionistic First-Order Logic (IQC).

This package implements a labelled/prefixed semantic tableau calculus for intuitionistic
first-order logic (Fitting 1969, 1983; Goré 1999). Proof search decomposes signed
formulas across explicit Kripke worlds and domains. When a formula is intuitionistically valid,
all tableau branches close. When a formula is unprovable (e.g. classical tautologies
such as excluded middle or double negation elimination), an open saturated branch
is used to construct an explicit finite Kripke countermodel (W, <=, D, V) falsifying
the target.
"""

from __future__ import annotations

from logic_prover.constructive.common import FALSUM, VERUM
from logic_prover.constructive.kripke import World, KripkeModel
from logic_prover.constructive.tableau.ast import (
    Sign,
    SignedFormula,
    TableauNode,
    TableauProofTree,
    TableauProofResult,
)
from logic_prover.constructive.tableau.branch import _BranchState
from logic_prover.constructive.tableau.prover import (
    TableauProver,
    prove_tableau,
)

__all__ = [
    "FALSUM",
    "VERUM",
    "Sign",
    "World",
    "SignedFormula",
    "KripkeModel",
    "TableauNode",
    "TableauProofTree",
    "TableauProofResult",
    "_BranchState",
    "TableauProver",
    "prove_tableau",
]
