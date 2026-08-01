"""Formula explorer subsystem for candidate generation, diversity filtering, and heuristic ranking."""

from __future__ import annotations

from solver.explorer.heuristics import (
    DiversityMetrics,
    calculate_symbol_entropy,
    calculate_diversity_scores,
    composite_interestingness,
    is_redundant_structure
)
from solver.explorer.filter import FormulaFilter
from solver.explorer.generator import (
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
