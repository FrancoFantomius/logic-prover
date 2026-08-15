"""Deducer subsystem for network dependency graph construction and minimal hypothesis analysis."""

from logic_prover.deducer.graph import DependencyGraph
from logic_prover.deducer.analyzer import (
    analyze_dependencies,
    find_minimal_hypotheses,
    detect_redundant_hypotheses,
    compute_equivalence_classes,
)

__all__ = [
    "DependencyGraph",
    "analyze_dependencies",
    "find_minimal_hypotheses",
    "detect_redundant_hypotheses",
    "compute_equivalence_classes",
]
