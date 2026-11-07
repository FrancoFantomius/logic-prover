"""Tests for Constructive Modal Logic IK (AST, Parser, Semantics, Tableaux, Sequent, Translation)."""

import unittest

from logic_prover.core.ast import (
    PredicateApp, Constant, Variable, Not, And, Or, Implies, Iff,
    Forall, Exists, Box, Diamond,
    formula_depth, formula_size, free_variables, bound_variables
)
from logic_prover.core.parser import parse_formula, to_string
from logic_prover.core.signature import Signature
from logic_prover.core.visitors import (
    DepthVisitor, SizeVisitor, FreeVariableCollector, ExportVisitor
)
from logic_prover.core.validator import validate_formula
from logic_prover.core.rewriter import RewriteRule, rewrite_all
from logic_prover.constructive.kripke import World, KripkeModel
from logic_prover.constructive.tableau.prover import TableauProver
from logic_prover.constructive.ik import IKProver, prove_ik, IKSequent
from logic_prover.constructive.resolution.translation import (
    translate_ik_to_fol, get_ik_frame_axioms, IKTranslationResolutionProver, prove_ik_translation_resolution
)
from logic_prover.config import SolverConfig


class TestIK(unittest.TestCase):

    # ---------------------------------------------------------------------------
    # 1. AST & Visitor Tests
    # ---------------------------------------------------------------------------

    def test_box_diamond_ast(self):
        p = PredicateApp("P", 0, ())
        bp = Box(p)
        dp = Diamond(p)

        self.assertIsInstance(bp, Box)
        self.assertIsInstance(dp, Diamond)
        self.assertEqual(bp.operand, p)
        self.assertEqual(dp.operand, p)
        self.assertEqual(hash(bp), hash(Box(p)))
        self.assertEqual(hash(dp), hash(Diamond(p)))
        self.assertNotEqual(bp, dp)

        # Depth and size
        self.assertEqual(formula_depth(bp), 2)
        self.assertEqual(formula_depth(dp), 2)
        self.assertEqual(formula_size(bp), 2)
        self.assertEqual(formula_size(dp), 2)

        # Visitors
        self.assertEqual(DepthVisitor().visit(bp), 2)
        self.assertEqual(SizeVisitor().visit(dp), 2)
        self.assertEqual(ExportVisitor(notation="prefix").visit(bp), "(box P)")
        self.assertEqual(ExportVisitor(notation="prefix").visit(dp), "(diamond P)")
        self.assertEqual(ExportVisitor(notation="infix").visit(bp), "[]P")
        self.assertEqual(ExportVisitor(notation="infix").visit(dp), "<>P")
        self.assertEqual(ExportVisitor(notation="latex").visit(bp), "\\Box P")
        self.assertEqual(ExportVisitor(notation="latex").visit(dp), "\\Diamond P")

    def test_box_diamond_with_variables(self):
        x = Variable(0)
        px = PredicateApp("P", 1, (x,))
        f = Forall(x, Box(px))

        self.assertEqual(free_variables(f), set())
        self.assertEqual(bound_variables(f), {x})
        self.assertEqual(formula_depth(f), 3)

    def test_validator_and_rewriter_box_diamond(self):
        p = PredicateApp("P", 0, ())
        q = PredicateApp("Q", 0, ())
        rule = RewriteRule(lhs=p, rhs=q)

        f1 = Box(p)
        res1 = rewrite_all(f1, [rule])
        self.assertEqual(res1, Box(q))

        f2 = Diamond(p)
        res2 = rewrite_all(f2, [rule])
        self.assertEqual(res2, Diamond(q))

    # ---------------------------------------------------------------------------
    # 2. Parser & Lexer Tests
    # ---------------------------------------------------------------------------

    def test_parse_box_diamond(self):
        sig = Signature()
        sig.register_predicate("P", 0, ())
        f1 = parse_formula("[]P", sig)
        self.assertIsInstance(f1, Box)
        self.assertEqual(f1.operand, PredicateApp("P", 0, ()))

        f2 = parse_formula("<>P", sig)
        self.assertIsInstance(f2, Diamond)
        self.assertEqual(f2.operand, PredicateApp("P", 0, ()))

        f3 = parse_formula("box P", sig)
        self.assertEqual(f3, f1)

        f4 = parse_formula("diamond P", sig)
        self.assertEqual(f4, f2)

        f5 = parse_formula("□P", sig)
        self.assertEqual(f5, f1)

        f6 = parse_formula("◇P", sig)
        self.assertEqual(f6, f2)

    def test_parse_box_diamond_prefix_and_precedence(self):
        sig = Signature()
        sig.register_predicate("P", 0, ())
        sig.register_predicate("Q", 0, ())

        f1 = parse_formula("(box (P & Q))", sig)
        self.assertIsInstance(f1, Box)
        self.assertIsInstance(f1.operand, And)

        f2 = parse_formula("(diamond (P | Q))", sig)
        self.assertIsInstance(f2, Diamond)
        self.assertIsInstance(f2.operand, Or)

        f3 = parse_formula("[]P => <>Q", sig)
        self.assertIsInstance(f3, Implies)
        self.assertIsInstance(f3.left, Box)
        self.assertIsInstance(f3.right, Diamond)

    # ---------------------------------------------------------------------------
    # 3. Kripke Semantics Tests
    # ---------------------------------------------------------------------------

    def test_kripke_modal_evaluation(self):
        m = KripkeModel()
        w0 = World(0, "w0")
        w1 = World(1, "w1")
        m.add_world(w0)
        m.add_world(w1)
        m.add_modal_relation(w0, w1)

        p = PredicateApp("P", 0, ())
        m.add_valuation(w1, p)

        self.assertTrue(m.evaluate(Box(p), w0))
        self.assertTrue(m.evaluate(Diamond(p), w0))

        # Check to_dict and to_string include modal relations
        m_dict = m.to_dict()
        self.assertIn("modal_relations", m_dict)
        self.assertIn("w1", m_dict["modal_relations"]["w0"])
        self.assertIn("Modal Accessibility Relation (R):", m.to_string())

    def test_kripke_commutation(self):
        m = KripkeModel()
        w0 = World(0, "w0")
        w1 = World(1, "w1")
        v0 = World(2, "v0")
        m.add_world(w0)
        m.add_world(w1)
        m.add_world(v0)

        m.add_relation(w0, w1)
        m.add_modal_relation(w0, v0)

        # Commutation ensures w1 R v0 (or some v1 with v0 <= v1)
        self.assertIn(v0, m.modal_relations.get(w1, set()))

    # ---------------------------------------------------------------------------
    # 4. Semantic Tableau Prover Tests
    # ---------------------------------------------------------------------------

    def test_tableau_prover_valid_theorems(self):
        p = PredicateApp("P", 0, ())
        q = PredicateApp("Q", 0, ())

        prover = TableauProver()

        # K axiom: [](P => Q) => ([]P => []Q)
        k_axiom = Implies(Box(Implies(p, q)), Implies(Box(p), Box(q)))
        res1 = prover.prove(k_axiom)
        self.assertTrue(res1.is_valid)

        # Diamond disjunction: <>(P | Q) <=> (<>P | <>Q)
        dia_disj = Iff(Diamond(Or(p, q)), Or(Diamond(p), Diamond(q)))
        res2 = prover.prove(dia_disj)
        self.assertTrue(res2.is_valid)

        # Diamond falsum negation: ~<>_bot
        falsum = PredicateApp("_bot", 0, ())
        res3 = prover.prove(Not(Diamond(falsum)))
        self.assertTrue(res3.is_valid)

        # (<>P => []Q) => [](P => Q)
        res4 = prover.prove(Implies(Implies(Diamond(p), Box(q)), Box(Implies(p, q))))
        self.assertTrue(res4.is_valid)

    def test_tableau_prover_invalid_formulas(self):
        p = PredicateApp("P", 0, ())
        q = PredicateApp("Q", 0, ())
        prover = TableauProver()

        # P => []P is invalid in IK
        res1 = prover.prove(Implies(p, Box(p)))
        self.assertFalse(res1.is_valid)
        self.assertIsNotNone(res1.countermodel)

        # []P => P is invalid in IK
        res2 = prover.prove(Implies(Box(p), p))
        self.assertFalse(res2.is_valid)
        self.assertIsNotNone(res2.countermodel)

        # [](P | Q) => ([]P | []Q) is invalid in IK
        res3 = prover.prove(Implies(Box(Or(p, q)), Or(Box(p), Box(q))))
        self.assertFalse(res3.is_valid)
        self.assertIsNotNone(res3.countermodel)

    # ---------------------------------------------------------------------------
    # 5. Sequent Calculus Prover Tests (IKProver)
    # ---------------------------------------------------------------------------

    def test_ik_sequent_prover(self):
        p = PredicateApp("P", 0, ())
        q = PredicateApp("Q", 0, ())

        prover = IKProver()

        # []P => []P
        res1 = prover.prove(Implies(Box(p), Box(p)))
        self.assertTrue(res1.is_valid)
        self.assertIsNotNone(res1.proof_tree)
        self.assertTrue("K_Box" in res1.proof_tree.to_string() or "Imp_R" in res1.proof_tree.to_string())

        # K axiom: [](P => Q) => ([]P => []Q)
        k_axiom = Implies(Box(Implies(p, q)), Implies(Box(p), Box(q)))
        res2 = prover.prove(k_axiom)
        self.assertTrue(res2.is_valid)

        # Diamond monotonic: [](P => Q) => (<>P => <>Q)
        dia_mono = Implies(Box(Implies(p, q)), Implies(Diamond(p), Diamond(q)))
        res3 = prover.prove(dia_mono)
        self.assertTrue(res3.is_valid)

        # prove_ik top-level function
        res4 = prove_ik(Implies(Box(p), Box(p)))
        self.assertTrue(res4.is_valid)
        self.assertIn("begin{prooftree}", res4.proof_tree.export_latex())

    # ---------------------------------------------------------------------------
    # 6. Relational Translation Prover Tests
    # ---------------------------------------------------------------------------

    def test_translate_ik_to_fol(self):
        p = PredicateApp("P", 0, ())
        fol_box = translate_ik_to_fol(Box(p))
        self.assertIsInstance(fol_box, Forall)

        fol_dia = translate_ik_to_fol(Diamond(p))
        self.assertIsInstance(fol_dia, Exists)

        axioms = get_ik_frame_axioms([("P", 0)])
        self.assertEqual(len(axioms), 4)

    def test_ik_translation_resolution_prover(self):
        p = PredicateApp("P", 0, ())
        prover = IKTranslationResolutionProver(max_steps=500, timeout_sec=5.0)

        # []P => []P
        res = prover.prove(Implies(Box(p), Box(p)))
        self.assertIsNotNone(res)
        self.assertTrue(res.is_valid)

        # Helper function
        res2 = prove_ik_translation_resolution(Implies(Box(p), Box(p)))
        self.assertIsNotNone(res2)
        self.assertTrue(res2.is_valid)

    # ---------------------------------------------------------------------------
    # 7. Config Tests
    # ---------------------------------------------------------------------------

    def test_solver_config_ik(self):
        cfg = SolverConfig()
        self.assertTrue(hasattr(cfg, "ik_max_modal_depth"))
        self.assertEqual(cfg.ik_max_modal_depth, 3)


if __name__ == "__main__":
    unittest.main()
