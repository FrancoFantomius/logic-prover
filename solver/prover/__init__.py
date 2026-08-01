"""
Prover module for resolution refutation search, clausification, proof DAG validation,
and natural deduction proof reconstruction.
"""

from solver.prover.clausifier import Literal, Clause, to_cnf, negate_and_clausify
from solver.prover.rules import InferenceRule, resolve_clauses, factor_clause, paramodulate
from solver.prover.proof import ProofStep, ProofDAG
from solver.prover.engine import ResolutionStep, TheoremProver
from solver.prover.reconstruction import reconstruct_proof, simplify_proof

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
