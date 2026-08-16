"""Network dependency analyzer and minimal hypothesis deduction algorithms."""

from __future__ import annotations
from typing import List, Tuple, Set, Optional, Dict
import logging

from logic_prover.core.ast import Formula, canonicalize_bound_variables
from logic_prover.prover.engine import TheoremProver
from logic_prover.prover.proof import ProofDAG
from logic_prover.core.exceptions import ProofTimeoutError, ProofSearchExhaustedError
from logic_prover.deducer.graph import DependencyGraph

logger = logging.getLogger(__name__)


def _try_prove(prover: TheoremProver, target: Formula, premises: List[Formula]) -> bool:
    """Attempts to prove target from premises using TheoremProver. Handles both prove and prove_theorem methods."""
    try:
        if hasattr(prover, "prove_theorem"):
            try:
                proof = prover.prove_theorem(hypotheses=premises, target=target)
            except TypeError:
                proof = prover.prove_theorem(target=target, premises=premises)
        else:
            proof = prover.prove(target=target, premises=premises)
        return proof is not None
    except (ProofTimeoutError, ProofSearchExhaustedError, Exception) as e:
        logger.debug("Proof attempt failed: %s", e)
        return False


def analyze_dependencies(
    formulas: List[Tuple[str, Formula]],
    prover: TheoremProver,
    pairwise: bool = False
) -> DependencyGraph:
    """Builds a DependencyGraph across a collection of named formulas.

    Args:
        formulas: List of (name, formula) tuples.
        prover: TheoremProver instance configured with timeout and search settings.
        pairwise: If True, attempts all O(n^2) pairwise implication proofs.
                  If False (default), builds graph incrementally from existing node formulas.

    Returns:
        DependencyGraph populated with nodes and proved implication/equivalence edges.
    """
    graph = DependencyGraph()

    for name, formula in formulas:
        graph.add_node(name, formula)

    if not pairwise:
        logger.info("Building DependencyGraph incrementally (pairwise=False).")
        return graph

    logger.info(f"Running pairwise dependency analysis over {len(formulas)} formulas (O(n^2)).")
    n = len(formulas)
    proved_pairs: Set[Tuple[str, str]] = set()

    for i in range(n):
        name_i, f_i = formulas[i]
        for j in range(n):
            if i == j:
                continue
            name_j, f_j = formulas[j]

            # Attempt proof f_i |- f_j
            if _try_prove(prover, target=f_j, premises=[f_i]):
                proved_pairs.add((name_i, name_j))

    # Process relationships
    for src, tgt in proved_pairs:
        if (tgt, src) in proved_pairs:
            graph.add_edge(src, tgt, "equivalent")
        else:
            graph.add_edge(src, tgt, "implies")

    return graph


def find_minimal_hypotheses(
    target: Formula,
    available_hypotheses: List[Formula],
    prover: TheoremProver
) -> List[Formula]:
    """Extracts a minimal sufficient subset of hypotheses for proving the target formula.

    Uses a greedy elimination algorithm: tests whether target remains provable when removing
    each hypothesis one by one. If provable without h, h is discarded.

    Args:
        target: Target conclusion formula.
        available_hypotheses: Initial candidate list of hypothesis formulas.
        prover: TheoremProver instance.

    Returns:
        A minimal subset of hypotheses sufficient to prove target.

    Raises:
        ValueError: If target is not provable from available_hypotheses.
    """
    if not _try_prove(prover, target, available_hypotheses):
        raise ValueError("Target formula is not provable from the provided hypotheses.")

    minimal_set = list(available_hypotheses)

    for hyp in list(available_hypotheses):
        candidate_set = [h for h in minimal_set if h != hyp]
        if _try_prove(prover, target, candidate_set):
            minimal_set = candidate_set

    return minimal_set


def detect_redundant_hypotheses(
    hypotheses: List[Formula],
    target: Formula,
    prover: TheoremProver
) -> List[Formula]:
    """Identifies all redundant hypotheses in a premise set for a target formula.

    A hypothesis h is redundant if (hypotheses \\ {h}) is sufficient to prove target.
    Unlike find_minimal_hypotheses (which returns a single minimal subset), this function
    tests each hypothesis independently against the full remaining set.

    Args:
        hypotheses: Candidate list of hypothesis formulas.
        target: Target conclusion formula.
        prover: TheoremProver instance.

    Returns:
        List of hypotheses that can be individually removed without losing provability.

    Raises:
        ValueError: If target is not provable from hypotheses.
    """
    if not _try_prove(prover, target, hypotheses):
        raise ValueError("Target formula is not provable from the provided hypotheses.")

    redundant: List[Formula] = []

    for hyp in hypotheses:
        candidate_set = [h for h in hypotheses if h != hyp]
        if _try_prove(prover, target, candidate_set):
            redundant.append(hyp)

    return redundant


def compute_equivalence_classes(
    formulas: List[Tuple[str, Formula]],
    prover: TheoremProver
) -> List[Set[str]]:
    """Groups formula names into logical equivalence classes where formulas mutually imply each other (A <=> B).

    Fast-paths syntactic alpha-equivalence via canonicalize_bound_variables, then invokes
    bidirectional prover calls for remaining pairs.

    Args:
        formulas: List of (name, formula) tuples.
        prover: TheoremProver instance.

    Returns:
        List of sets of formula names, where each set contains mutually equivalent formulas.
    """
    if not formulas:
        return []

    parent: Dict[str, str] = {name: name for name, _ in formulas}

    def find(i: str) -> str:
        """Finds the union-find representative for a name with path compression.

        Args:
            i: The name to look up.

        Returns:
            The representative root name.
        """
        if parent[i] == i:
            return i
        parent[i] = find(parent[i])
        return parent[i]

    def union(i: str, j: str) -> None:
        """Merges the union-find sets containing i and j.

        Args:
            i: First name to merge.
            j: Second name to merge.
        """
        root_i = find(i)
        root_j = find(j)
        if root_i != root_j:
            parent[root_i] = root_j

    # 1. Fast-path: Group by canonical alpha-equivalence
    canonical_map: Dict[str, str] = {}
    for name, formula in formulas:
        canon_key = str(canonicalize_bound_variables(formula))
        if canon_key in canonical_map:
            union(name, canonical_map[canon_key])
        else:
            canonical_map[canon_key] = name

    # 2. Semantic proving pass across representative formulas
    representatives = list(canonical_map.items())
    formula_lookup = dict(formulas)
    n = len(representatives)

    for i in range(n):
        canon_i, name_i = representatives[i]
        formula_i = formula_lookup[name_i]
        for j in range(i + 1, n):
            canon_j, name_j = representatives[j]
            formula_j = formula_lookup[name_j]

            if find(name_i) == find(name_j):
                continue

            # Check bidirectional proof: f_i |- f_j and f_j |- f_i
            if _try_prove(prover, target=formula_j, premises=[formula_i]):
                if _try_prove(prover, target=formula_i, premises=[formula_j]):
                    union(name_i, name_j)

    # Collect equivalence classes
    classes_dict: Dict[str, Set[str]] = {}
    for name, _ in formulas:
        root = find(name)
        if root not in classes_dict:
            classes_dict[root] = set()
        classes_dict[root].add(name)

    return list(classes_dict.values())
