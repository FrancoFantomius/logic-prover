from __future__ import annotations
import os
import sys
import tempfile
import unittest
from pathlib import Path

from logic.core.ast import (
    Variable, Constant, FunctionApp, PredicateApp, Equality,
    Not, And, Or, Implies, Iff, Forall, Exists, VariableKind
)
from logic.core.sorts import (
    PrimitiveSort, ParameterizedSort, FunctionSort, Ind, Nat, Bool, SetSort
)
from logic.core.database import KnowledgeDatabase
from logic.prover.proof import ProofStep, ProofDAG
from logic.prover.rules import InferenceRule
from logic.deducer.graph import DependencyGraph
from logic.exporters.lean_exporter import LeanExporter
from logic.exporters.graph_exporter import GraphExporter
from logic.__main__ import main, build_cli_parser


class TestLeanExporter(unittest.TestCase):
    """Unit tests for LEAN 4 Exporter (Tier 1, Tier 2, Tier 3)."""

    def setUp(self) -> None:
        self.exporter = LeanExporter(lean_project_name="TestProject", universe_name="u", default_sort_var="α")

    def test_export_sort(self) -> None:
        self.assertEqual(self.exporter.export_sort(Nat), "ℕ")
        self.assertEqual(self.exporter.export_sort(Ind), "α")
        self.assertEqual(self.exporter.export_sort(Bool), "Bool")

        set_nat = SetSort(Nat)
        self.assertEqual(self.exporter.export_sort(set_nat), "Set ℕ")

        func_sort = FunctionSort((Nat, Bool), Ind)
        self.assertEqual(self.exporter.export_sort(func_sort), "ℕ → Bool → α")

    def test_export_term(self) -> None:
        v0 = Variable(id=0)
        c_a = Constant(name="a")
        f_app = FunctionApp(func="f", arity=2, args=(v0, c_a))
        plus_app = FunctionApp(func="+", arity=2, args=(v0, c_a))

        self.assertEqual(self.exporter.export_term(v0), "v0")
        self.assertEqual(self.exporter.export_term(c_a), "a")
        self.assertEqual(self.exporter.export_term(f_app), "(f v0 a)")
        self.assertEqual(self.exporter.export_term(plus_app), "(v0 + a)")

    def test_export_formula_connectives(self) -> None:
        v0 = Variable(id=0)
        c_a = Constant(name="a")
        p_v0 = PredicateApp(pred="P", arity=1, args=(v0,))
        q_a = PredicateApp(pred="Q", arity=1, args=(c_a,))
        eq_node = Equality(left=v0, right=c_a)

        self.assertEqual(self.exporter.export_formula(p_v0), "(P v0)")
        self.assertEqual(self.exporter.export_formula(eq_node), "(v0 = a)")
        self.assertEqual(self.exporter.export_formula(Not(operand=p_v0)), "¬ ((P v0))")
        self.assertEqual(self.exporter.export_formula(And(left=p_v0, right=q_a)), "((P v0) ∧ (Q a))")
        self.assertEqual(self.exporter.export_formula(Or(left=p_v0, right=q_a)), "((P v0) ∨ (Q a))")
        self.assertEqual(self.exporter.export_formula(Implies(left=p_v0, right=q_a)), "((P v0) → (Q a))")
        self.assertEqual(self.exporter.export_formula(Iff(left=p_v0, right=q_a)), "((P v0) ↔ (Q a))")

    def test_export_formula_quantifiers(self) -> None:
        v0 = Variable(id=0, sort=Nat)
        p_v0 = PredicateApp(pred="P", arity=1, args=(v0,))
        forall_node = Forall(variable=v0, body=p_v0)
        exists_node = Exists(variable=v0, body=p_v0)

        self.assertEqual(self.exporter.export_formula(forall_node), "∀ (v0 : ℕ), (P v0)")
        self.assertEqual(self.exporter.export_formula(exists_node), "∃ (v0 : ℕ), (P v0)")

    def test_export_theorem_statement(self) -> None:
        v0 = Variable(id=0)
        p_v0 = PredicateApp(pred="P", arity=1, args=(v0,))
        q_v0 = PredicateApp(pred="Q", arity=1, args=(v0,))

        stmt = self.exporter.export_theorem_statement(
            name="modus_ponens_lemma",
            formula=q_v0,
            hypotheses=[("h1", p_v0), ("h2", Implies(left=p_v0, right=q_v0))]
        )
        self.assertIn("theorem modus_ponens_lemma (h1 : (P v0)) (h2 : ((P v0) → (Q v0))) : (Q v0) := by", stmt)
        self.assertIn("sorry", stmt)

    def test_export_proof_dag(self) -> None:
        v0 = Variable(id=0)
        p_v0 = PredicateApp(pred="P", arity=1, args=(v0,))
        q_v0 = PredicateApp(pred="Q", arity=1, args=(v0,))

        step_h1 = ProofStep(id="h1", rule="Hypothesis", premise_ids=[], conclusion=p_v0)
        step_h2 = ProofStep(id="h2", rule="Hypothesis", premise_ids=[], conclusion=Implies(left=p_v0, right=q_v0))
        step_mp = ProofStep(id="step_mp", rule="ModusPonens", premise_ids=["h2", "h1"], conclusion=q_v0)

        proof = ProofDAG(
            steps={"h1": step_h1, "h2": step_h2, "step_mp": step_mp},
            root_id="step_mp"
        )

        lean_code = self.exporter.export_proof(proof=proof, theorem_name="test_mp_thm")
        self.assertIn("theorem test_mp_thm (h1 : (P v0)) (h2 : ((P v0) → (Q v0))) : (Q v0) := by", lean_code)
        self.assertIn("have step_mp : (Q v0) := h2 h1", lean_code)
        self.assertIn("exact step_mp", lean_code)

    def test_export_file(self) -> None:
        v0 = Variable(id=0)
        p_v0 = PredicateApp(pred="P", arity=1, args=(v0,))

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = os.path.join(tmp_dir, "export.lean")
            theorems = [("thm1", p_v0, None)]
            self.exporter.export_file(out_file, theorems=theorems, stubs_only=True)

            self.assertTrue(os.path.exists(out_file))
            with open(out_file, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("import Mathlib.Tactic", content)
            self.assertIn("namespace TestProject", content)
            self.assertIn("theorem thm1 : (P v0) := by", content)
            self.assertIn("end TestProject", content)


class TestGraphExporter(unittest.TestCase):
    """Unit tests for GraphExporter (ProofDAG and DependencyGraph HTML export)."""

    def setUp(self) -> None:
        self.exporter = GraphExporter(theme="light")

    def test_export_proof_to_html(self) -> None:
        v0 = Variable(id=0)
        p_v0 = PredicateApp(pred="P", arity=1, args=(v0,))
        q_v0 = PredicateApp(pred="Q", arity=1, args=(v0,))

        step_h1 = ProofStep(id="h1", rule="Hypothesis", premise_ids=[], conclusion=p_v0)
        step_h2 = ProofStep(id="h2", rule="Hypothesis", premise_ids=[], conclusion=Implies(left=p_v0, right=q_v0))
        step_mp = ProofStep(id="step_mp", rule="ModusPonens", premise_ids=["h2", "h1"], conclusion=q_v0)

        proof = ProofDAG(
            steps={"h1": step_h1, "h2": step_h2, "step_mp": step_mp},
            root_id="step_mp"
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            html_file = os.path.join(tmp_dir, "proof.html")
            self.exporter.export_proof_to_html(proof, html_file, title="Test Proof HTML")

            self.assertTrue(os.path.exists(html_file))
            with open(html_file, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("<!DOCTYPE html>", content)
            self.assertIn("vis-network", content)
            self.assertIn("mynetwork", content)
            self.assertIn("step_mp", content)
            self.assertIn("ModusPonens", content)
            self.assertIn("Test Proof HTML", content)

    def test_export_dependency_network_to_html(self) -> None:
        v0 = Variable(id=0)
        p_v0 = PredicateApp(pred="P", arity=1, args=(v0,))
        q_v0 = PredicateApp(pred="Q", arity=1, args=(v0,))

        dep_graph = DependencyGraph()
        dep_graph.add_node("Axiom1", p_v0)
        dep_graph.add_node("Thm1", q_v0)
        dep_graph.add_edge("Axiom1", "Thm1", "implies")

        with tempfile.TemporaryDirectory() as tmp_dir:
            html_file = os.path.join(tmp_dir, "dep_graph.html")
            self.exporter.export_dependency_network_to_html(dep_graph, html_file, title="Test Dep Graph")

            self.assertTrue(os.path.exists(html_file))
            with open(html_file, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("<!DOCTYPE html>", content)
            self.assertIn("vis-network", content)
            self.assertIn("Axiom1", content)
            self.assertIn("Thm1", content)
            self.assertIn("implies", content)


class TestCLIExportCommands(unittest.TestCase):
    """Integration tests for `export lean` and `export graph` CLI subcommands."""

    def test_cli_export_lean(self) -> None:
        v0 = Variable(id=0)
        p_v0 = PredicateApp(pred="P", arity=1, args=(v0,))

        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            lean_out = os.path.join(tmp_dir, "output.lean")

            db = KnowledgeDatabase(db_path)
            db.add_axiom("ax_p", p_v0, category="test")
            db.close()

            main(["export", "lean", "--output", lean_out, "--db-path", db_path, "--stubs-only"])

            self.assertTrue(os.path.exists(lean_out))
            with open(lean_out, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("import Mathlib.Tactic", content)
            self.assertIn("theorem ax_p", content)

    def test_cli_export_graph_proof(self) -> None:
        v0 = Variable(id=0)
        p_v0 = PredicateApp(pred="P", arity=1, args=(v0,))

        step_h1 = ProofStep(id="h1", rule="Hypothesis", premise_ids=[], conclusion=p_v0)
        proof = ProofDAG(steps={"h1": step_h1}, root_id="h1")

        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            html_out = os.path.join(tmp_dir, "proof_graph.html")

            db = KnowledgeDatabase(db_path)
            db.add_theorem("thm_p", p_v0, proof=proof)
            db.close()

            main(["export", "graph", "--output", html_out, "--type", "proof", "--theorem", "thm_p", "--db-path", db_path])

            self.assertTrue(os.path.exists(html_out))
            with open(html_out, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("<!DOCTYPE html>", content)
            self.assertIn("h1", content)

    def test_cli_export_graph_dependency(self) -> None:
        v0 = Variable(id=0)
        p_v0 = PredicateApp(pred="P", arity=1, args=(v0,))

        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            html_out = os.path.join(tmp_dir, "dep_graph.html")

            db = KnowledgeDatabase(db_path)
            db.add_axiom("ax_p", p_v0, category="test")
            db.close()

            main(["export", "graph", "--output", html_out, "--type", "dependency", "--db-path", db_path])

            self.assertTrue(os.path.exists(html_out))
            with open(html_out, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("<!DOCTYPE html>", content)
            self.assertIn("ax_p", content)


if __name__ == "__main__":
    unittest.main()
