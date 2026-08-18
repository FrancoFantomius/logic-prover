"""
logic-prover: A formal logic theorem prover, explorer, deducer, and Lean 4 exporter.
"""

from __future__ import annotations

__version__ = "0.2.0"
__author__ = "Franco Fantomius"

from logic_prover.config import SolverConfig
from logic_prover.core.parser import parse_formula, to_string
from logic_prover.axioms import get_combined_signature, Theory, get_theory
from logic_prover import axioms
from logic_prover.logging import get_logger, setup_logging
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
    "Theory",
    "get_theory",
    "axioms",
    "setup_logging",
    "get_logger",
]
