"""
Solver Library
==============
Automated logical solver, proof generator, consequence explorer, and Lean 4 verifier.
"""

from .formula import Formula, Var, Not, Implies, And, Or, Iff, Forall, Exists, Equals, Pred, parse_formula
from .database import TheoryDatabase
from .prover import prove, reconstruct_proof, get_subformulas
from .verifier import verify_proof_local, verify_proof_with_lean, verify_and_save
from .explorer import explore_consequences
from .deducer import Deducer, deduce_consequences, Consequence
from .lean_exporter import formula_to_lean, export_proof
from .graph_exporter import build_theory_graph, export_graph_dot, export_graph_json, export_graph_html
from . import dependencies

__all__ = [
    "Formula",
    "Var",
    "Not",
    "Implies",
    "And",
    "Or",
    "Iff",
    "Forall",
    "Exists",
    "Equals",
    "Pred",
    "parse_formula",
    "TheoryDatabase",
    "prove",
    "reconstruct_proof",
    "get_subformulas",
    "verify_proof_local",
    "verify_proof_with_lean",
    "verify_and_save",
    "explore_consequences",
    "Deducer",
    "deduce_consequences",
    "Consequence",
    "formula_to_lean",
    "export_proof",
    "build_theory_graph",
    "export_graph_dot",
    "export_graph_json",
    "export_graph_html",
    "dependencies",
]

