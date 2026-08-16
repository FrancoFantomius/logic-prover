"""Example 06: Export theorems to Lean 4 and interactive HTML graphs.

Two exporters turn in-memory results into artifacts you can use elsewhere:

- ``LeanExporter`` emits Lean 4 theorem declarations (with ``sorry`` stubs
  when proofs are not available) from a list of (name, formula, proof)
  tuples, ready to paste into a Mathlib project.
- ``GraphExporter`` renders a ``ProofDAG`` or a ``DependencyGraph`` into a
  self-contained interactive HTML file using the vis-network library.

Run it with:

    python examples/06_exporters.py

Requires the ``logic_prover`` package to be installed. From the repository
root run ``pip install -e .`` (or otherwise make the package importable)
before executing this example.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Lean 4 output uses Unicode symbols; force UTF-8 stdout so the print below
# works even on consoles whose default codepage is not UTF-8.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from logic_prover.core.ast import (
    Variable, Constant, PredicateApp, Implies,
)
from logic_prover.core.sorts import Ind, Nat
from logic_prover.core.database import KnowledgeDatabase
from logic_prover.prover.engine import TheoremProver
from logic_prover.prover.proof import ProofStep, ProofDAG
from logic_prover.deducer.graph import DependencyGraph
from logic_prover.exporters.lean_exporter import LeanExporter
from logic_prover.exporters.graph_exporter import GraphExporter


def main() -> None:
    # ------------------------------------------------------------------
    # 1. Build a proof DAG the way the prover would
    # ------------------------------------------------------------------
    v0 = Variable(id=0, sort=Ind)
    p_v0 = PredicateApp(pred="P", arity=1, args=(v0,))
    q_v0 = PredicateApp(pred="Q", arity=1, args=(v0,))

    step_h1 = ProofStep(id="h1", rule="Hypothesis", premise_ids=[], conclusion=p_v0)
    step_h2 = ProofStep(id="h2", rule="Hypothesis", premise_ids=[], conclusion=Implies(left=p_v0, right=q_v0))
    step_mp = ProofStep(id="step_mp", rule="ModusPonens", premise_ids=["h2", "h1"], conclusion=q_v0)

    proof = ProofDAG(
        steps={"h1": step_h1, "h2": step_h2, "step_mp": step_mp},
        root_id="step_mp",
    )

    # ------------------------------------------------------------------
    # 2. Export a theorem to Lean 4
    # ------------------------------------------------------------------
    lean_exporter = LeanExporter(lean_project_name="LogicExamples", universe_name="u")
    lean_code = lean_exporter.export_proof(proof=proof, theorem_name="modus_ponens_demo")
    print("=== Lean 4 export ===")
    print(lean_code)
    print()

    # ------------------------------------------------------------------
    # 3. Write the proof graph and a dependency graph to HTML
    # ------------------------------------------------------------------
    with tempfile.TemporaryDirectory() as tmp_dir:
        proof_html = str(Path(tmp_dir) / "proof.html")
        dep_html = str(Path(tmp_dir) / "dependency.html")

        graph_exporter = GraphExporter(theme="light")
        graph_exporter.export_proof_to_html(proof, proof_html, title="Modus Ponens Proof")

        # A small dependency graph with an 'implies' edge.
        dep_graph = DependencyGraph()
        dep_graph.add_node("Axiom1", p_v0)
        dep_graph.add_node("Thm1", q_v0)
        dep_graph.add_edge("Axiom1", "Thm1", "implies")
        graph_exporter.export_dependency_network_to_html(dep_graph, dep_html, title="Dependency Network")

        print("=== HTML exports ===")
        print(f"Proof graph     : {proof_html} ({Path(proof_html).stat().st_size} bytes)")
        print(f"Dependency graph: {dep_html} ({Path(dep_html).stat().st_size} bytes)")

    # ------------------------------------------------------------------
    # 4. Export from the database using the library-level API
    # ------------------------------------------------------------------
    db_path = ":memory:"
    db = KnowledgeDatabase(db_path)
    db.add_theorem("modus_ponens_demo", q_v0, proof=proof)

    theorems = [(name, formula, db.get_proof(name)) for name, formula in db.get_theorems()]
    with tempfile.TemporaryDirectory() as tmp_dir:
        lean_file = str(Path(tmp_dir) / "theorems.lean")
        lean_exporter.export_file(lean_file, theorems, stubs_only=False)
        print(f"Exported {len(theorems)} theorem(s) to {lean_file}")
    db.close()


if __name__ == "__main__":
    main()
