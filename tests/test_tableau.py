"""Unit and regression tests for Semantic Tableaux with Kripke Semantics (IPC)."""

from __future__ import annotations
import unittest

from logic_prover.core.ast import (
    PredicateApp, Equality, Not, And, Or, Implies, Iff, Constant
)
from logic_prover.core.sorts import Ind
from logic_prover.constructive.tableau import (
    Sign,
    World,
    SignedFormula,
    KripkeModel,
    TableauNode,
    TableauProofTree,
    TableauProofResult,
    TableauProver,
    prove_tableau,
    FALSUM,
    VERUM,
)


class TestTableauProver(unittest.TestCase):
    """Test suite for the Intuitionistic Semantic Tableau prover and Kripke countermodel builder."""

    def setUp(self) -> None:
        """Sets up proposition variables for testing."""
        self.p = PredicateApp(pred="P", arity=0, args=())
        self.q = PredicateApp(pred="Q", arity=0, args=())
        self.r = PredicateApp(pred="R", arity=0, args=())
        self.prover = TableauProver()

    def test_sign_and_world_dataclasses(self) -> None:
        """Tests Sign and World basic behaviors."""
        self.assertEqual(str(Sign.TRUE), "T")
        self.assertEqual(str(Sign.FALSE), "F")

        w0 = World(id=0, name="w0")
        self.assertEqual(w0.id, 0)
        self.assertEqual(w0.name, "w0")
        self.assertEqual(str(w0), "w0")
        self.assertIn("World(id=0, name=w0)", repr(w0))

    def test_signed_formula(self) -> None:
        """Tests SignedFormula formatting."""
        w0 = World(id=0, name="w0")
        sf_t = SignedFormula(sign=Sign.TRUE, formula=self.p, world=w0)
        self.assertEqual(sf_t.to_string(), "T(P, w0)")
        self.assertEqual(str(sf_t), "T(P, w0)")

        sf_f = SignedFormula(sign=Sign.FALSE, formula=FALSUM, world=w0)
        self.assertEqual(sf_f.to_string(), "F(_bot, w0)")
        self.assertEqual(sf_f.to_string(notation="latex"), "F(\\bot, w0)")

        sf_top = SignedFormula(sign=Sign.TRUE, formula=VERUM, world=w0)
        self.assertEqual(sf_top.to_string(), "T(_top, w0)")
        self.assertEqual(sf_top.to_string(notation="latex"), "T(\\top, w0)")

    def test_kripke_model_operations_and_evaluation(self) -> None:
        """Tests KripkeModel construction, accessibility, and semantic evaluation."""
        model = KripkeModel()
        w0 = World(0, "w0")
        w1 = World(1, "w1")
        w2 = World(2, "w2")

        model.add_world(w0)
        model.add_relation(w0, w1)
        model.add_relation(w1, w2)

        # Transitivity check
        self.assertTrue(model.is_accessible(w0, w0))
        self.assertTrue(model.is_accessible(w0, w1))
        self.assertTrue(model.is_accessible(w0, w2))
        self.assertFalse(model.is_accessible(w1, w0))

        # Valuation & Monotonicity
        model.add_valuation(w1, self.p)
        self.assertFalse(model.evaluate(self.p, w0))
        self.assertTrue(model.evaluate(self.p, w1))
        self.assertTrue(model.evaluate(self.p, w2))

        # Evaluation of connectives
        # w0 |/= P, w0 |/= ~P because w1 >= w0 and w1 |= P
        self.assertFalse(model.evaluate(Or(self.p, Not(self.p)), w0))
        self.assertTrue(model.evaluate(FALSUM, w0) is False)
        self.assertTrue(model.evaluate(VERUM, w0) is True)

        # Serialization
        m_dict = model.to_dict()
        self.assertEqual(len(m_dict["worlds"]), 3)
        self.assertIn("Kripke Model", model.to_string())
        self.assertIn("Kripke Model", str(model))

    def test_identity_axiom(self) -> None:
        """Tests basic identity P => P."""
        target = Implies(left=self.p, right=self.p)
        res = self.prover.prove(target=target)
        self.assertTrue(res.is_valid)
        self.assertTrue(res.tree.is_closed())
        self.assertIsNone(res.countermodel)

    def test_k_combinator(self) -> None:
        """Tests K combinator: P => (Q => P)."""
        target = Implies(left=self.p, right=Implies(left=self.q, right=self.p))
        res = self.prover.prove(target=target)
        self.assertTrue(res.is_valid)

    def test_s_combinator(self) -> None:
        """Tests S combinator: (P => (Q => R)) => ((P => Q) => (P => R))."""
        p_imp_q_imp_r = Implies(left=self.p, right=Implies(left=self.q, right=self.r))
        p_imp_q = Implies(left=self.p, right=self.q)
        p_imp_r = Implies(left=self.p, right=self.r)
        target = Implies(
            left=p_imp_q_imp_r,
            right=Implies(left=p_imp_q, right=p_imp_r)
        )
        res = self.prover.prove(target=target)
        self.assertTrue(res.is_valid)

    def test_conjunction_and_disjunction_laws(self) -> None:
        """Tests commutativity, associativity, and distributivity of And / Or."""
        # Commutativity of And
        target_and_comm = Implies(
            left=And(left=self.p, right=self.q),
            right=And(left=self.q, right=self.p)
        )
        self.assertTrue(self.prover.is_valid(target_and_comm))

        # Commutativity of Or
        target_or_comm = Implies(
            left=Or(left=self.p, right=self.q),
            right=Or(left=self.q, right=self.p)
        )
        self.assertTrue(self.prover.is_valid(target_or_comm))

        # Distributivity of And over Or: (P & (Q | R)) => ((P & Q) | (P & R))
        distrib = Implies(
            left=And(left=self.p, right=Or(left=self.q, right=self.r)),
            right=Or(left=And(left=self.p, right=self.q), right=And(left=self.p, right=self.r))
        )
        self.assertTrue(self.prover.is_valid(distrib))

    def test_double_negation_introduction(self) -> None:
        """Tests intuitionistic double negation introduction: P => ~~P."""
        target = Implies(left=self.p, right=Not(operand=Not(operand=self.p)))
        self.assertTrue(self.prover.is_valid(target))

    def test_triple_negation_reduction(self) -> None:
        """Tests intuitionistic triple negation reduction: ~~~P <=> ~P."""
        not_p = Not(operand=self.p)
        not_not_not_p = Not(operand=Not(operand=Not(operand=self.p)))
        target = Iff(left=not_not_not_p, right=not_p)
        self.assertTrue(self.prover.is_valid(target))

    def test_intuitionistic_de_morgan(self) -> None:
        """Tests intuitionistically valid De Morgan laws."""
        # ~(P | Q) <=> (~P & ~Q)
        target1 = Iff(
            left=Not(operand=Or(left=self.p, right=self.q)),
            right=And(left=Not(operand=self.p), right=Not(operand=self.q))
        )
        self.assertTrue(self.prover.is_valid(target1))

        # (~P | ~Q) => ~(P & Q)
        target2 = Implies(
            left=Or(left=Not(operand=self.p), right=Not(operand=self.q)),
            right=Not(operand=And(left=self.p, right=self.q))
        )
        self.assertTrue(self.prover.is_valid(target2))

    def test_ex_falso_quodlibet(self) -> None:
        """Tests ex falso: ~P => (P => Q) and deriving goal from falsum premise."""
        target = Implies(
            left=Not(operand=self.p),
            right=Implies(left=self.p, right=self.q)
        )
        self.assertTrue(self.prover.is_valid(target))
        self.assertTrue(self.prover.is_valid(target=self.p, premises=[FALSUM]))

    def test_hypothesis_premises_modus_ponens(self) -> None:
        """Tests proving target from premises using Modus Ponens."""
        p_imp_q = Implies(left=self.p, right=self.q)
        res = self.prover.prove(target=self.q, premises=[self.p, p_imp_q])
        self.assertTrue(res.is_valid)

    def test_classical_non_theorems_and_countermodels(self) -> None:
        """Tests invalid constructive formulas and verifies extracted Kripke countermodels."""
        # 1. Law of Excluded Middle: P | ~P
        lem = Or(left=self.p, right=Not(operand=self.p))
        res_lem = self.prover.prove(lem)
        self.assertFalse(res_lem.is_valid)
        self.assertIsNotNone(res_lem.countermodel)
        assert res_lem.countermodel is not None
        w0 = res_lem.countermodel.worlds[0]
        self.assertFalse(res_lem.countermodel.evaluate(lem, w0))

        # 2. Peirce's Law: ((P => Q) => P) => P
        peirce = Implies(
            left=Implies(left=Implies(left=self.p, right=self.q), right=self.p),
            right=self.p
        )
        res_peirce = self.prover.prove(peirce)
        self.assertFalse(res_peirce.is_valid)
        self.assertIsNotNone(res_peirce.countermodel)
        assert res_peirce.countermodel is not None
        w0 = res_peirce.countermodel.worlds[0]
        self.assertFalse(res_peirce.countermodel.evaluate(peirce, w0))

        # 3. Double Negation Elimination: ~~P => P
        dne = Implies(left=Not(operand=Not(operand=self.p)), right=self.p)
        res_dne = self.prover.prove(dne)
        self.assertFalse(res_dne.is_valid)
        self.assertIsNotNone(res_dne.countermodel)
        assert res_dne.countermodel is not None
        w0 = res_dne.countermodel.worlds[0]
        self.assertFalse(res_dne.countermodel.evaluate(dne, w0))

        # 4. Classical De Morgan: ~(P & Q) => (~P | ~Q)
        demorgan_classical = Implies(
            left=Not(operand=And(left=self.p, right=self.q)),
            right=Or(left=Not(operand=self.p), right=Not(operand=self.q))
        )
        res_dm = self.prover.prove(demorgan_classical)
        self.assertFalse(res_dm.is_valid)
        self.assertIsNotNone(res_dm.countermodel)
        assert res_dm.countermodel is not None
        w0 = res_dm.countermodel.worlds[0]
        self.assertFalse(res_dm.countermodel.evaluate(demorgan_classical, w0))

        # 5. Implication to Disjunction: (P => Q) => (~P | Q)
        imp_to_disj = Implies(
            left=Implies(left=self.p, right=self.q),
            right=Or(left=Not(operand=self.p), right=self.q)
        )
        self.assertFalse(self.prover.is_valid(imp_to_disj))
        cm_imp = self.prover.countermodel(imp_to_disj)
        self.assertIsNotNone(cm_imp)
        assert cm_imp is not None
        self.assertFalse(cm_imp.evaluate(imp_to_disj, cm_imp.worlds[0]))

    def test_equality_atom_support(self) -> None:
        """Tests first-order equality atoms in intuitionistic semantic tableaux."""
        c_a = Constant("a", sort=Ind)
        c_b = Constant("b", sort=Ind)
        eq_ab = Equality(left=c_a, right=c_b)
        target = Implies(left=eq_ab, right=eq_ab)
        res = self.prover.prove(target=target)
        self.assertTrue(res.is_valid)

    def test_convenience_function_prove_tableau(self) -> None:
        """Tests the top-level prove_tableau convenience function."""
        target = Implies(left=self.p, right=self.p)
        res = prove_tableau(target)
        self.assertTrue(res.is_valid)
        self.assertGreater(res.tree.get_size(), 0)
        self.assertGreater(res.tree.get_depth(), 0)
        self.assertIn("Derivation Tree", res.to_string())
        self.assertIn("Derivation Tree", str(res))

        # Serialization
        res_dict = res.to_dict()
        self.assertTrue(res_dict["is_valid"])
        self.assertEqual(res_dict["target"], "(P => P)")

        # Tree LaTeX export
        latex = res.tree.to_latex()
        self.assertIn("\\begin{forest}", latex)
        self.assertIn("\\end{forest}", latex)

    def test_contradictions_rejected(self) -> None:
        """Verifies that TableauProver does not accept contradictions.

        Tests that attempting to prove P & ~P, FALSUM (_bot), or P <=> ~P
        fails and produces results where is_valid is False and a countermodel is available.

        Args:
            None

        Returns:
            None: Asserts that contradictions are unprovable in the tableau prover.

        Example:
            >>> self.test_contradictions_rejected()
        """
        contradiction = And(left=self.p, right=Not(operand=self.p))
        res_and = self.prover.prove(contradiction)
        self.assertFalse(res_and.is_valid)
        self.assertFalse(self.prover.is_valid(contradiction))
        self.assertIsNotNone(res_and.countermodel)

        res_bot = self.prover.prove(FALSUM)
        self.assertFalse(res_bot.is_valid)
        self.assertFalse(self.prover.is_valid(FALSUM))

        iff_contra = Iff(left=self.p, right=Not(operand=self.p))
        res_iff = self.prover.prove(iff_contra)
        self.assertFalse(res_iff.is_valid)
        self.assertFalse(self.prover.is_valid(iff_contra))


if __name__ == "__main__":
    unittest.main()
