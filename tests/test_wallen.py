"""Unit and regression tests for Lincoln Wallen's Matrix / Connection Method for IPC."""

from __future__ import annotations
import unittest

from logic_prover.core.ast import (
    PredicateApp, Equality, Not, And, Or, Implies, Iff
)
from logic_prover.constructive.common import FALSUM
from logic_prover.constructive.wallen import (
    PrefixSymbol,
    PrefixConstant,
    PrefixVariable,
    Prefix,
    PrefixSubstitution,
    PositionType,
    Position,
    FormulaTree,
    Connection,
    WallenProofResult,
    WallenProver,
    prove_wallen,
    unify_prefixes,
    is_admissible,
)


class TestWallenProver(unittest.TestCase):
    """Test suite for Lincoln Wallen's matrix/connection method for intuitionistic logic."""

    def setUp(self) -> None:
        """Sets up propositional symbols for testing."""
        self.p = PredicateApp(pred="P", arity=0, args=())
        self.q = PredicateApp(pred="Q", arity=0, args=())
        self.r = PredicateApp(pred="R", arity=0, args=())
        self.prover = WallenProver(max_multiplicity=3)

    # --- PREFIX DATA STRUCTURES & UNIFICATION TESTS ---

    def test_prefix_operations(self) -> None:
        """Tests Prefix manipulation methods, slicing, appending, and str representation."""
        c0 = PrefixConstant("c0")
        c1 = PrefixConstant("c1")
        v1 = PrefixVariable("V1")
        pre = Prefix((c0, c1))
        self.assertEqual(len(pre), 2)
        self.assertEqual(pre[0], c0)
        self.assertEqual(pre.to_string(), "c0.c1")

        extended = pre.append(v1)
        self.assertEqual(len(extended), 3)
        self.assertIn(v1, extended.variables())
        self.assertIn(c0, extended.constants())
        self.assertEqual(str(extended), "c0.c1.V1")

        empty_pre = Prefix()
        self.assertEqual(str(empty_pre), "eps")

    def test_prefix_substitution_apply(self) -> None:
        """Tests application of prefix substitution."""
        c0 = PrefixConstant("c0")
        c1 = PrefixConstant("c1")
        v1 = PrefixVariable("V1")
        subst = PrefixSubstitution().bind(v1, (c1,))
        res = subst.apply(Prefix((c0, v1)))
        self.assertEqual(res.symbols, (c0, c1))
        self.assertEqual(subst.to_dict(), {"V1": "c1"})

    def test_t_string_unification(self) -> None:
        """Tests intuitionistic T-string prefix unification algorithm."""
        c0 = PrefixConstant("c0")
        c1 = PrefixConstant("c1")
        c2 = PrefixConstant("c2")
        v1 = PrefixVariable("V1")

        # Unify c0.V1 with c0.c1
        unifs = unify_prefixes(Prefix((c0, v1)), Prefix((c0, c1)))
        self.assertEqual(len(unifs), 1)
        self.assertEqual(unifs[0].get(v1), (c1,))

        # Unify c0.c1 with c0.c2 (different constants -> failure)
        unifs_fail = unify_prefixes(Prefix((c0, c1)), Prefix((c0, c2)))
        self.assertEqual(len(unifs_fail), 0)

    # --- VALID INTUITIONISTIC THEOREMS ---

    def test_identity_axiom(self) -> None:
        """Tests basic identity sequent P ==> P."""
        proof = self.prover.prove(target=self.p, premises=[self.p])
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid)

    def test_implication_introduction(self) -> None:
        """Tests self-implication P => P."""
        target = Implies(left=self.p, right=self.p)
        proof = self.prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid)

    def test_k_combinator(self) -> None:
        """Tests K combinator: P => (Q => P)."""
        target = Implies(left=self.p, right=Implies(left=self.q, right=self.p))
        proof = self.prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid)

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
        self.assertTrue(proof.is_valid)

    def test_conjunction_commutativity(self) -> None:
        """Tests (P & Q) => (Q & P)."""
        target = Implies(
            left=And(left=self.p, right=self.q),
            right=And(left=self.q, right=self.p)
        )
        proof = self.prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid)

    def test_disjunction_commutativity(self) -> None:
        """Tests (P | Q) => (Q | P)."""
        target = Implies(
            left=Or(left=self.p, right=self.q),
            right=Or(left=self.q, right=self.p)
        )
        proof = self.prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid)

    def test_double_negation_introduction(self) -> None:
        """Tests intuitionistic double negation introduction: P => ~~P."""
        target = Implies(left=self.p, right=Not(operand=Not(operand=self.p)))
        proof = self.prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid)

    def test_contraposition_intuitionistic(self) -> None:
        """Tests intuitionistic contraposition: (P => Q) => (~Q => ~P)."""
        target = Implies(
            left=Implies(left=self.p, right=self.q),
            right=Implies(left=Not(operand=self.q), right=Not(operand=self.p))
        )
        proof = self.prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid)

    def test_distributivity_and_or(self) -> None:
        """Tests (P & (Q | R)) => ((P & Q) | (P & R))."""
        target = Implies(
            left=And(left=self.p, right=Or(left=self.q, right=self.r)),
            right=Or(left=And(left=self.p, right=self.q), right=And(left=self.p, right=self.r))
        )
        proof = self.prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid)

    def test_currying(self) -> None:
        """Tests currying equivalence: ((P & Q) => R) <=> (P => (Q => R))."""
        lhs = Implies(left=And(left=self.p, right=self.q), right=self.r)
        rhs = Implies(left=self.p, right=Implies(left=self.q, right=self.r))
        target = Iff(left=lhs, right=rhs)
        proof = self.prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid)

    def test_prove_wallen_convenience(self) -> None:
        """Tests top-level prove_wallen helper function."""
        target = Implies(left=self.p, right=self.p)
        res = prove_wallen(target)
        self.assertIsNotNone(res)
        assert res is not None
        self.assertTrue(res.is_valid)
        self.assertIn("VALID", res.to_string())
        self.assertTrue(res.to_dict()["is_valid"])

    # --- CLASSICAL-ONLY FORMULAS (MUST FAIL IN IPC) ---

    def test_peirce_law_fails(self) -> None:
        """Tests Peirce's Law: ((P => Q) => P) => P is NOT intuitionistically valid."""
        p_imp_q = Implies(left=self.p, right=self.q)
        target = Implies(left=Implies(left=p_imp_q, right=self.p), right=self.p)
        proof = self.prover.prove(target=target)
        self.assertIsNone(proof)

    def test_law_of_excluded_middle_fails(self) -> None:
        """Tests Law of Excluded Middle: P | ~P is NOT intuitionistically valid."""
        target = Or(left=self.p, right=Not(operand=self.p))
        proof = self.prover.prove(target=target)
        self.assertIsNone(proof)

    def test_double_negation_elimination_fails(self) -> None:
        """Tests Double Negation Elimination: ~~P => P is NOT intuitionistically valid."""
        target = Implies(left=Not(operand=Not(operand=self.p)), right=self.p)
        proof = self.prover.prove(target=target)
        self.assertIsNone(proof)

    def test_weak_peirce_fails(self) -> None:
        """Tests Weak Peirce: (~P => P) => P is NOT intuitionistically valid."""
        target = Implies(left=Implies(left=Not(operand=self.p), right=self.p), right=self.p)
        proof = self.prover.prove(target=target)
        self.assertIsNone(proof)

    def test_contradictions_rejected(self) -> None:
        """Verifies that WallenProver does not accept contradictions.

        Tests that attempting to prove P & ~P, FALSUM (_bot), or P <=> ~P
        fails and returns None.

        Args:
            None

        Returns:
            None: Asserts that contradictions cannot be proved in Wallen matrix method.

        Example:
            >>> self.test_contradictions_rejected()
        """
        contradiction = And(left=self.p, right=Not(operand=self.p))
        self.assertIsNone(self.prover.prove(target=contradiction))

        self.assertIsNone(self.prover.prove(target=FALSUM))

        iff_contra = Iff(left=self.p, right=Not(operand=self.p))
        self.assertIsNone(self.prover.prove(target=iff_contra))


if __name__ == "__main__":
    unittest.main()
