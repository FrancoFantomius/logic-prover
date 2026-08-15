"""
logic-prover: A formal logic theorem prover, explorer, deducer, and Lean 4 exporter.
"""

from __future__ import annotations

__version__ = "0.1.4"
__author__ = "Franco Fantomius"

from logic_prover.config import SolverConfig
from logic_prover.core.parser import parse_formula, to_string
from logic_prover.kb import get_combined_signature
from logic_prover.prover.engine import TheoremProver
from logic_prover.prover.proof import ProofDAG

__all__ = [
    "__version__",
    "__author__",
    "SolverConfig",
    "TheoremProver",
    "ProofDAG",
    "parse_formula",
    "to_string",
    "get_combined_signature",
]
