"""Example 05: Analyze dependencies and deduce minimal hypotheses.

The deducer subsystem studies how formulas relate to one another:

- ``DependencyGraph`` stores named formulas and directed ``implies`` /
  ``equivalent`` edges and supports traversals and cycle detection.
- ``analyze_dependencies`` builds such a graph across a collection of
  formulas, optionally running expensive pairwise implication proofs.
- ``find_minimal_hypotheses`` removes hypotheses one at a time to find a
  minimal sufficient subset for a given target.
- ``detect_redundant_hypotheses`` reports every hypothesis that can be
  dropped individually.
- ``compute_equivalence_classes`` groups formulas that mutually imply each
  other, fast-pathing on syntactic alpha-equivalence.

Run it with:

    python examples/05_dependency_deducer.py

Requires the ``logic_prover`` package to be installed. From the repository
root run ``pip install -e .`` (or otherwise make the package importable)
before executing this example.
"""

from __future__ import annotations

from logic_prover.core.ast import (
    Variable, Constant, PredicateApp, Not, Or, And, Implies,
)
from logic_prover.core.sorts import Ind
from logic_prover.core.signature import Signature
from logic_prover.prover.engine import TheoremProver
from logic_prover.deducer.graph import DependencyGraph
from logic_prover.deducer.analyzer import (
    analyze_dependencies,
    find_minimal_hypotheses,
    detect_redundant_hypotheses,
    compute_equivalence_classes,
)


def main() -> None:
    sig = Signature()
    sig.register_predicate("P", 1, (Ind,))
    sig.register_predicate("Q", 1, (Ind,))
    sig.register_predicate("R", 1, (Ind,))
    sig.register_constant("a", Ind)
    prover = TheoremProver(signature=sig)

    p_a = PredicateApp("P", 1, (Constant("a"),))
    q_a = PredicateApp("Q", 1, (Constant("a"),))
    r_a = PredicateApp("R", 1, (Constant("a"),))

    # ------------------------------------------------------------------
    # 1. Build a dependency graph manually
    # ------------------------------------------------------------------
    graph = DependencyGraph()
    graph.add_node("A", p_a)
    graph.add_node("B", q_a)
    graph.add_node("C", r_a)
    graph.add_edge("A", "B", "implies")
    graph.add_edge("B", "C", "implies")

    print("Nodes:", list(graph.nodes))
    print("Successors of A:", graph.successors("A"))
    print("Predecessors of C:", graph.predecessors("C"))
    print("Transitive closure of A:", sorted(graph.transitive_closure("A")))
    print("Acyclic (modulo equivalence)?:", graph.is_acyclic_modulo_equivalence())
    print()

    # ------------------------------------------------------------------
    # 2. Find a minimal subset of hypotheses for a target
    # ------------------------------------------------------------------
    # H1: P(a), H2: Q(a) (redundant), H3: P(a) => R(a). Target: R(a).
    h1, h2, h3 = p_a, q_a, Implies(left=p_a, right=r_a)
    minimal = find_minimal_hypotheses(target=r_a, available_hypotheses=[h1, h2, h3], prover=prover)
    print(f"Minimal hypothesis subset for R(a): {len(minimal)} formula(s)")
    for f in minimal:
        print("  -", f)

    redundant = detect_redundant_hypotheses(hypotheses=[h1, h2, h3], target=r_a, prover=prover)
    print(f"Individually redundant hypotheses: {len(redundant)}")
    print()

    # ------------------------------------------------------------------
    # 3. Equivalent formulas and full dependency analysis
    # ------------------------------------------------------------------
    # P(a) => Q(a) and ~P(a) | Q(a) are logically equivalent.
    f1 = Implies(left=p_a, right=q_a)
    f2 = Or(left=Not(operand=p_a), right=q_a)
    classes = compute_equivalence_classes([("F1", f1), ("F2", f2), ("F3", r_a)], prover=prover)
    print("Equivalence classes:", [sorted(c) for c in classes])

    dep_graph = analyze_dependencies(
        [("F1", f1), ("F2", f2), ("F3", r_a)],
        prover=prover,
        pairwise=True,
    )
    print("Dependency edges:", dep_graph.edges)


if __name__ == "__main__":
    main()
