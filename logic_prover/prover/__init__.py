"""
Prover module for resolution refutation search, clausification, proof DAG validation,
and natural deduction proof reconstruction.
"""

from logic.prover.clausifier import Literal, Clause, to_cnf, negate_and_clausify
from logic.prover.rules import InferenceRule, resolve_clauses, factor_clause, paramodulate
from logic.prover.proof import ProofStep, ProofDAG
from logic.prover.engine import ResolutionStep, TheoremProver
from logic.prover.reconstruction import reconstruct_proof, simplify_proof

__all__ = [
    "Literal",
    "Clause",
    "to_cnf",
    "negate_and_clausify",
    "InferenceRule",
    "resolve_clauses",
    "factor_clause",
    "paramodulate",
    "ProofStep",
    "ProofDAG",
    "ResolutionStep",
    "TheoremProver",
    "reconstruct_proof",
    "simplify_proof",
]
