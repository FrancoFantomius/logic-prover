"""Formula explorer subsystem for candidate generation, diversity filtering, and heuristic ranking."""

from __future__ import annotations

from logic_prover.explorer.heuristics import (
    DiversityMetrics,
    calculate_symbol_entropy,
    calculate_diversity_scores,
    composite_interestingness,
    is_redundant_structure
)
from logic_prover.explorer.filter import FormulaFilter
from logic_prover.explorer.generator import (
    FormulaExplorer,
    anti_unify_terms,
    anti_unify_formulas
)

__all__ = [
    "DiversityMetrics",
    "calculate_symbol_entropy",
    "calculate_diversity_scores",
    "composite_interestingness",
    "is_redundant_structure",
    "FormulaFilter",
    "FormulaExplorer",
    "anti_unify_terms",
    "anti_unify_formulas",
]
