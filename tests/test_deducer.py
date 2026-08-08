import unittest
import tempfile
import json
from pathlib import Path

from logic.core.ast import (
    Variable, Constant, PredicateApp, Not, Or, Implies, And, Forall
)
from logic.core.sorts import Ind
from logic.core.signature import Signature
from logic.prover.engine import TheoremProver
from logic.prover.proof import ProofDAG, ProofStep
from logic.deducer.graph import DependencyGraph
from logic.deducer.analyzer import (
    analyze_dependencies,
    find_minimal_hypotheses,
    detect_redundant_hypotheses,
    compute_equivalence_classes,
)
from logic.core.database import KnowledgeDatabase
from logic.__main__ import main


class TestDeducer(unittest.TestCase):

    def setUp(self):
        self.sig = Signature()
        self.sig.register_predicate("P", 1, (Ind,))
        self.sig.register_predicate("Q", 1, (Ind,))
        self.sig.register_predicate("R", 1, (Ind,))
        self.sig.register_constant("a", Ind)
        self.prover = TheoremProver(signature=self.sig)

        self.p_a = PredicateApp("P", 1, (Constant("a"),))
        self.q_a = PredicateApp("Q", 1, (Constant("a"),))
        self.r_a = PredicateApp("R", 1, (Constant("a"),))


    def test_dependency_graph_basic_operations(self):
        graph = DependencyGraph()
        graph.add_node("A", self.p_a)
        graph.add_node("B", self.q_a)

        # Idempotent addition
        graph.add_node("A", self.p_a)
        self.assertIn("A", graph.nodes)

        # Conflicting formula raises ValueError
        with self.assertRaises(ValueError):
            graph.add_node("A", self.q_a)

        # Add valid edge
        graph.add_edge("A", "B", "implies")
        self.assertIn(("A", "B", "implies"), graph.edges)

        # Invalid relationship raises ValueError
        with self.assertRaises(ValueError):
            graph.add_edge("A", "B", "invalid_relation")

        # Missing node raises KeyError
        with self.assertRaises(KeyError):
            graph.add_edge("A", "NON_EXISTENT", "implies")
        with self.assertRaises(KeyError):
            graph.add_edge("NON_EXISTENT", "B", "implies")

    def test_dependency_graph_traversals(self):
        graph = DependencyGraph()
        graph.add_node("A", self.p_a)
        graph.add_node("B", self.q_a)
        graph.add_node("C", self.r_a)
        c_a2 = PredicateApp("R", 1, (Constant("a"),))
        graph.add_node("D", c_a2)

        graph.add_edge("A", "B", "implies")
        graph.add_edge("B", "C", "implies")
        graph.add_edge("A", "D", "implies")

        self.assertEqual(graph.predecessors("C"), ["B"])
        self.assertEqual(graph.successors("A"), ["B", "D"])
        self.assertEqual(graph.transitive_closure("A"), {"B", "C", "D"})
        self.assertEqual(graph.transitive_closure("C"), set())

        # Missing node raises KeyError
        with self.assertRaises(KeyError):
            graph.predecessors("MISSING")
        with self.assertRaises(KeyError):
            graph.successors("MISSING")
        with self.assertRaises(KeyError):
            graph.transitive_closure("MISSING")

    def test_register_proof_incremental(self):
        graph = DependencyGraph()
        step0 = ProofStep(id="prem_0", rule="Axiom", premise_ids=[], conclusion=self.p_a)
        step1 = ProofStep(id="prem_1", rule="Axiom", premise_ids=[], conclusion=self.q_a)
        step_root = ProofStep(id="root", rule="AndIntroduction", premise_ids=["prem_0", "prem_1"], conclusion=self.r_a)

        proof = ProofDAG(
            steps={"prem_0": step0, "prem_1": step1, "root": step_root},
            root_id="root",
            axiom_ids={"prem_0", "prem_1"}
        )

        graph.register_proof(proof, "Theorem_C")

        self.assertIn("Theorem_C", graph.nodes)
        self.assertEqual(graph.nodes["Theorem_C"], self.r_a)
        self.assertIn("premise_0", graph.nodes)
        self.assertIn("premise_1", graph.nodes)
        self.assertIn("Theorem_C", graph.successors("premise_0"))
        self.assertIn("Theorem_C", graph.successors("premise_1"))

    def test_graph_serialization(self):
        graph = DependencyGraph()
        graph.add_node("A", self.p_a)
        graph.add_node("B", self.q_a)
        graph.add_edge("A", "B", "implies")

        data = graph.to_dict()
        self.assertIn("nodes", data)
        self.assertIn("edges", data)
        self.assertEqual(len(data["nodes"]), 2)
        self.assertEqual(len(data["edges"]), 1)
        self.assertEqual(data["edges"][0], {"source": "A", "target": "B", "relationship": "implies"})

    def test_is_acyclic_modulo_equivalence(self):
        graph = DependencyGraph()
        graph.add_node("A", self.p_a)
        graph.add_node("B", self.q_a)
        graph.add_node("C", self.r_a)

        graph.add_edge("A", "B", "implies")
        graph.add_edge("B", "C", "implies")
        self.assertTrue(graph.is_acyclic_modulo_equivalence())

        # Directed cycle in implication edge -> False
        graph.add_edge("C", "A", "implies")
        self.assertFalse(graph.is_acyclic_modulo_equivalence())

        # Graph with equivalent relationship loop only -> True
        graph_eq = DependencyGraph()
        graph_eq.add_node("X", self.p_a)
        graph_eq.add_node("Y", self.q_a)
        graph_eq.add_edge("X", "Y", "equivalent")
        graph_eq.add_edge("Y", "X", "equivalent")
        self.assertTrue(graph_eq.is_acyclic_modulo_equivalence())

    def test_find_minimal_hypotheses(self):
        # H1: P(a)
        # H2: Q(a) (redundant)
        # H3: P(a) => R(a)
        # Target: R(a)
        h1 = self.p_a
        h2 = self.q_a
        h3 = Implies(left=self.p_a, right=self.r_a)
        target = self.r_a

        minimal = find_minimal_hypotheses(
            target=target,
            available_hypotheses=[h1, h2, h3],
            prover=self.prover
        )

        self.assertEqual(len(minimal), 2)
        self.assertIn(h1, minimal)
        self.assertIn(h3, minimal)
        self.assertNotIn(h2, minimal)

        # Unprovable target raises ValueError
        with self.assertRaises(ValueError):
            find_minimal_hypotheses(target=self.q_a, available_hypotheses=[h1], prover=self.prover)

    def test_detect_redundant_hypotheses(self):
        h1 = self.p_a
        h2 = self.q_a
        h3 = Implies(left=self.p_a, right=self.r_a)
        target = self.r_a

        redundant = detect_redundant_hypotheses(
            hypotheses=[h1, h2, h3],
            target=target,
            prover=self.prover
        )

        self.assertEqual(redundant, [h2])

        # Unprovable target raises ValueError
        with self.assertRaises(ValueError):
            detect_redundant_hypotheses(hypotheses=[h1], target=self.q_a, prover=self.prover)

    def test_compute_equivalence_classes_syntactic_and_semantic(self):
        # F1: P(a) => Q(a)
        # F2: ~P(a) | Q(a)
        # F3: R(a)
        f1 = Implies(left=self.p_a, right=self.q_a)
        f2 = Or(left=Not(operand=self.p_a), right=self.q_a)
        f3 = self.r_a

        classes = compute_equivalence_classes(
            formulas=[("F1", f1), ("F2", f2), ("F3", f3)],
            prover=self.prover
        )

        class_sets = [set(c) for c in classes]
        self.assertIn({"F1", "F2"}, class_sets)
        self.assertIn({"F3"}, class_sets)

        # Fast-path syntactic alpha-equivalence test
        vx = Variable(id=0, sort=Ind)
        vy = Variable(id=1, sort=Ind)
        fa_x = Forall(variable=vx, body=PredicateApp("P", 1, (vx,)))
        fa_y = Forall(variable=vy, body=PredicateApp("P", 1, (vy,)))

        classes_alpha = compute_equivalence_classes(
            formulas=[("Alpha1", fa_x), ("Alpha2", fa_y)],
            prover=self.prover
        )
        self.assertEqual(len(classes_alpha), 1)
        self.assertEqual(classes_alpha[0], {"Alpha1", "Alpha2"})

    def test_analyze_dependencies_pairwise(self):
        # F1: P(a) & Q(a)
        # F2: P(a)
        f1 = And(left=self.p_a, right=self.q_a)
        f2 = self.p_a

        graph = analyze_dependencies(
            formulas=[("F1", f1), ("F2", f2)],
            prover=self.prover,
            pairwise=True
        )

        self.assertIn(("F1", "F2", "implies"), graph.edges)
        self.assertNotIn(("F2", "F1", "implies"), graph.edges)

    def test_cli_analyze_command(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test_deducer.db")
            out_json = str(Path(tmpdir) / "graph.json")

            db = KnowledgeDatabase(db_path)
            db.add_axiom("Axiom_P", self.p_a, category="test")
            db.add_axiom("Axiom_Q", self.q_a, category="test")
            db.close()

            # Execute CLI analyze command
            main(["analyze", "--db-path", db_path, "--output", out_json])

            self.assertTrue(Path(out_json).exists())
            with open(out_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertIn("nodes", data)
            self.assertIn("edges", data)


if __name__ == "__main__":
    unittest.main()
