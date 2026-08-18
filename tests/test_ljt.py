"""Unit and regression tests for Roy Dyckhoff's Contraction-Free Sequent Calculus (LJT / G4ip)."""

from __future__ import annotations
import unittest

from logic_prover.core.ast import (
    PredicateApp, Equality, Not, And, Or, Implies, Iff, Constant
)
from logic_prover.core.sorts import Ind
from logic_prover.constructive.ljt import (
    Sequent,
    LJTProofNode,
    LJTProofTree,
    LJTProver,
    prove_ljt,
    normalize_formula,
    _formula_weight,
    FALSUM,
    VERUM,
)


class TestLJTProver(unittest.TestCase):
    """Test suite for the LJT / G4ip intuitionistic sequent calculus implementation."""

    def setUp(self) -> None:
        """Sets up proposition variables for testing."""
        self.p = PredicateApp(pred="P", arity=0, args=())
        self.q = PredicateApp(pred="Q", arity=0, args=())
        self.r = PredicateApp(pred="R", arity=0, args=())
        self.prover = LJTProver()

    def test_identity_axiom(self) -> None:
        """Tests basic identity sequent P ==> P."""
        proof = self.prover.prove(target=self.p, premises=[self.p])
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid())
        self.assertEqual(proof.root.rule, "Ax")

    def test_implication_introduction(self) -> None:
        """Tests self-implication P => P."""
        target = Implies(left=self.p, right=self.p)
        proof = self.prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid())
        self.assertEqual(proof.root.rule, "R_Imp")

    def test_k_combinator(self) -> None:
        """Tests K combinator: P => (Q => P)."""
        target = Implies(left=self.p, right=Implies(left=self.q, right=self.p))
        proof = self.prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid())

    def test_s_combinator(self) -> None:
        """Tests S combinator: (P => (Q => R)) => ((P => Q) => (P => R))."""
        p_imp_q_imp_r = Implies(left=self.p, right=Implies(left=self.q, right=self.r))
        p_imp_q = Implies(left=self.p, right=self.q)
        p_imp_r = Implies(left=self.p, right=self.r)
        target = Implies(
            left=p_imp_q_imp_r,
            right=Implies(left=p_imp_q, right=p_imp_r)
        )
        proof = self.prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid())

    def test_conjunction_commutativity(self) -> None:
        """Tests (P & Q) => (Q & P)."""
        target = Implies(
            left=And(left=self.p, right=self.q),
            right=And(left=self.q, right=self.p)
        )
        proof = self.prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid())

    def test_disjunction_commutativity(self) -> None:
        """Tests (P | Q) => (Q | P)."""
        target = Implies(
            left=Or(left=self.p, right=self.q),
            right=Or(left=self.q, right=self.p)
        )
        proof = self.prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid())

    def test_double_negation_introduction(self) -> None:
        """Tests intuitionistic double negation introduction: P => ~~P."""
        target = Implies(left=self.p, right=Not(operand=Not(operand=self.p)))
        proof = self.prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid())

    def test_triple_negation_reduction(self) -> None:
        """Tests intuitionistic triple negation reduction: ~~~P <=> ~P."""
        not_p = Not(operand=self.p)
        not_not_not_p = Not(operand=Not(operand=Not(operand=self.p)))
        target = Iff(left=not_not_not_p, right=not_p)
        proof = self.prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid())

    def test_de_morgan_intuitionistic_valid_1(self) -> None:
        """Tests ~(P | Q) <=> (~P & ~Q)."""
        target = Iff(
            left=Not(operand=Or(left=self.p, right=self.q)),
            right=And(left=Not(operand=self.p), right=Not(operand=self.q))
        )
        proof = self.prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid())

    def test_de_morgan_intuitionistic_valid_2(self) -> None:
        """Tests (~P | ~Q) => ~(P & Q)."""
        target = Implies(
            left=Or(left=Not(operand=self.p), right=Not(operand=self.q)),
            right=Not(operand=And(left=self.p, right=self.q))
        )
        proof = self.prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid())

    def test_ex_falso_quodlibet(self) -> None:
        """Tests ex falso: ~P => (P => Q)."""
        target = Implies(
            left=Not(operand=self.p),
            right=Implies(left=self.p, right=self.q)
        )
        proof = self.prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid())

    def test_dyckhoff_nested_implication(self) -> None:
        """Tests nested implication ((P => Q) => R) => (Q => R)."""
        target = Implies(
            left=Implies(left=Implies(left=self.p, right=self.q), right=self.r),
            right=Implies(left=self.q, right=self.r)
        )
        proof = self.prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid())

    def test_classical_non_theorems(self) -> None:
        """Tests formulas that are classically valid but intuitionistically invalid."""
        # 1. Law of Excluded Middle: P | ~P
        lem = Or(left=self.p, right=Not(operand=self.p))
        self.assertFalse(self.prover.is_provable(lem))

        # 2. Peirce's Law: ((P => Q) => P) => P
        peirce = Implies(
            left=Implies(left=Implies(left=self.p, right=self.q), right=self.p),
            right=self.p
        )
        self.assertFalse(self.prover.is_provable(peirce))

        # 3. Double Negation Elimination: ~~P => P
        dne = Implies(left=Not(operand=Not(operand=self.p)), right=self.p)
        self.assertFalse(self.prover.is_provable(dne))

        # 4. Classical De Morgan: ~(P & Q) => (~P | ~Q)
        demorgan_classical = Implies(
            left=Not(operand=And(left=self.p, right=self.q)),
            right=Or(left=Not(operand=self.p), right=Not(operand=self.q))
        )
        self.assertFalse(self.prover.is_provable(demorgan_classical))

    def test_equality_atom_support(self) -> None:
        """Tests first-order equality atoms in intuitionistic sequent calculus."""
        c_a = Constant("a", sort=Ind)
        c_b = Constant("b", sort=Ind)
        eq_ab = Equality(left=c_a, right=c_b)
        target = Implies(left=eq_ab, right=eq_ab)
        proof = self.prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid())

    def test_proof_tree_properties_and_exports(self) -> None:
        """Tests tree properties, ASCII rendering, LaTeX generation, and serialization."""
        target = Implies(left=self.p, right=self.p)
        proof = prove_ljt(target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertGreater(proof.depth, 0)
        self.assertGreater(proof.size, 0)
        self.assertTrue(proof.is_valid())

        # ASCII representation
        ascii_tree = proof.to_ascii()
        self.assertIn("R_Imp", ascii_tree)
        self.assertIn("Ax", ascii_tree)

        # String representation
        self.assertEqual(str(proof), ascii_tree)

        # LaTeX export
        latex = proof.to_latex()
        self.assertIn("\\begin{prooftree}", latex)
        self.assertIn("\\RightLabel{R_Imp}", latex)
        self.assertIn("\\end{prooftree}", latex)

        # Dict export
        tree_dict = proof.to_dict()
        self.assertEqual(tree_dict["root"]["rule"], "R_Imp")
        self.assertTrue(tree_dict["is_valid"])

    def test_verum_and_falsum_constants(self) -> None:
        """Tests verum and falsum handling in sequents."""
        self.assertTrue(self.prover.is_provable(VERUM))
        self.assertTrue(self.prover.is_provable(target=self.p, premises=[FALSUM]))

    def test_formula_weight(self) -> None:
        """Tests formula weight computation for Dyckhoff ordering."""
        self.assertEqual(_formula_weight(self.p), 1)
        and_pq = And(left=self.p, right=self.q)
        self.assertEqual(_formula_weight(and_pq), 3)
        imp_pq = Implies(left=self.p, right=self.q)
        self.assertEqual(_formula_weight(imp_pq), 3)

    def test_contradictions_rejected(self) -> None:
        """Verifies that LJTProver does not accept contradictions.

        Tests that attempting to prove P & ~P, FALSUM (_bot), or P <=> ~P
        from empty premises fails and returns None.

        Args:
            None

        Returns:
            None: Asserts that contradictions cannot be proved in LJT sequent calculus.

        Example:
            >>> self.test_contradictions_rejected()
        """
        contradiction = And(left=self.p, right=Not(operand=self.p))
        self.assertIsNone(self.prover.prove(target=contradiction))
        self.assertFalse(self.prover.is_provable(target=contradiction))

        self.assertIsNone(self.prover.prove(target=FALSUM))
        self.assertFalse(self.prover.is_provable(target=FALSUM))

        iff_contra = Iff(left=self.p, right=Not(operand=self.p))
        self.assertIsNone(self.prover.prove(target=iff_contra))
        self.assertFalse(self.prover.is_provable(target=iff_contra))


if __name__ == "__main__":
    unittest.main()
