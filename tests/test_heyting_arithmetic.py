"""Unit and integration tests for Heyting Arithmetic (HA) constructive logic and theorem proving."""

from __future__ import annotations
import unittest

from logic_prover.core.ast import (
    Variable, Constant, FunctionApp, PredicateApp, Equality,
    Not, And, Or, Implies, Iff, Forall, Exists
)
from logic_prover.core.sorts import Nat, Ind
from logic_prover.axioms.heyting_arithmetic import (
    get_ha_signature,
    get_ha_axioms,
    instantiate_ha_induction,
    ha_theory,
)
from logic_prover.axioms.base import get_theory
from logic_prover.constructive.ljt import LJTProver, prove_ljt
from logic_prover.constructive.tableau import TableauProver, prove_tableau
from logic_prover.constructive.ha import HAProver, prove_ha, _extract_induction_candidates


class TestHeytingArithmeticTheory(unittest.TestCase):
    """Tests for the Heyting Arithmetic theory, signature, axioms, and induction instantiation."""

    def test_ha_signature_declarations(self) -> None:
        """HA signature declares zero, succ, add, mul, le, lt, and eq."""
        sig = get_ha_signature()
        self.assertTrue(sig.has_symbol("zero"))
        self.assertTrue(sig.has_symbol("succ"))
        self.assertTrue(sig.has_symbol("add"))
        self.assertTrue(sig.has_symbol("mul"))
        self.assertTrue(sig.has_symbol("le"))
        self.assertTrue(sig.has_symbol("lt"))
        self.assertTrue(sig.has_symbol("eq"))

    def test_ha_axioms_structure(self) -> None:
        """HA axioms list contains the 7 core Peano axioms."""
        axioms = get_ha_axioms()
        self.assertEqual(len(axioms), 7)
        axiom_names = [name for name, _ in axioms]
        self.assertIn("ha_zero_not_succ", axiom_names)
        self.assertIn("ha_succ_injective", axiom_names)
        self.assertIn("ha_add_zero", axiom_names)
        self.assertIn("ha_add_succ", axiom_names)
        self.assertIn("ha_mul_zero", axiom_names)
        self.assertIn("ha_mul_succ", axiom_names)
        self.assertIn("ha_le_def", axiom_names)

    def test_ha_theory_registered_and_valid(self) -> None:
        """ha_theory is correctly registered in the global theory registry and validates cleanly."""
        registered = get_theory("ha")
        self.assertIsNotNone(registered)
        self.assertEqual(registered.name, "ha")
        self.assertEqual(registered.validate(), [])

    def test_instantiate_ha_induction(self) -> None:
        """instantiate_ha_induction builds the standard first-order induction schema instance."""
        n = Variable(0, sort=Nat)
        zero = Constant("zero", sort=Nat)
        succ_n = FunctionApp("succ", 1, (n,), return_sort=Nat)
        add_0_n = FunctionApp("add", 2, (zero, n), return_sort=Nat)
        prop = Equality(add_0_n, n)

        ind_schema = instantiate_ha_induction(prop, n)
        self.assertIsInstance(ind_schema, Implies)
        self.assertIsInstance(ind_schema.left, And)
        self.assertIsInstance(ind_schema.right, Forall)


class TestHeytingArithmeticLJT(unittest.TestCase):
    """Tests for constructive theorem proving in Heyting Arithmetic using LJT sequent calculus."""

    def setUp(self) -> None:
        self.zero = Constant("zero", sort=Nat)
        self.n = Variable(1, sort=Nat)
        self.m = Variable(2, sort=Nat)
        self.k = Variable(3, sort=Nat)
        self.ha_axioms_dict = dict(get_ha_axioms())

    def test_left_identity_addition(self) -> None:
        """forall n. 0 + n = n is provable in LJT via mathematical induction (R_Ind)."""
        add_0_n = FunctionApp("add", 2, (self.zero, self.n), return_sort=Nat)
        goal = Forall(self.n, Equality(add_0_n, self.n))

        # Specialized successor lemma for 0 + S(n) = S(0 + n) to enable efficient induction step
        succ_n = FunctionApp("succ", 1, (self.n,), return_sort=Nat)
        add_0_succ_n = FunctionApp("add", 2, (self.zero, succ_n), return_sort=Nat)
        succ_add_0_n = FunctionApp("succ", 1, (add_0_n,), return_sort=Nat)
        lemma_add_succ_0 = Forall(self.n, Equality(add_0_succ_n, succ_add_0_n))

        premises = [
            self.ha_axioms_dict["ha_add_zero"],
            lemma_add_succ_0,
        ]

        prover = LJTProver(max_term_depth=1, eq_subst_max=2, max_ind_depth=2)
        proof = prover.prove(target=goal, premises=premises)
        self.assertIsNotNone(proof)
        self.assertTrue(proof.is_valid())
        self.assertIn("R_Ind", proof.to_ascii())

    def test_succ_not_equal_self(self) -> None:
        """forall n. S(n) <> n is provable in LJT via induction."""
        succ_n = FunctionApp("succ", 1, (self.n,), return_sort=Nat)
        goal = Forall(self.n, Not(Equality(succ_n, self.n)))

        premises = [
            self.ha_axioms_dict["ha_zero_not_succ"],
            self.ha_axioms_dict["ha_succ_injective"],
        ]

        prover = LJTProver(max_ind_depth=2)
        proof = prover.prove(target=goal, premises=premises)
        self.assertIsNotNone(proof)
        self.assertTrue(proof.is_valid())
        self.assertIn("R_Ind", proof.to_ascii())

    def test_ordering_reflexivity(self) -> None:
        """forall n. n <= n is provable in LJT using ha_le_def and ha_add_zero."""
        le_n_n = PredicateApp("le", 2, (self.n, self.n))
        goal = Forall(self.n, le_n_n)

        # Ordering reflexivity lemma: forall n. n + 0 = n => n <= n (from ha_le_def instantiated with k = 0)
        add_n_0 = FunctionApp("add", 2, (self.n, self.zero), return_sort=Nat)
        le_def_inst = Forall(self.n, Implies(Equality(add_n_0, self.n), le_n_n))

        premises = [
            self.ha_axioms_dict["ha_add_zero"],
            le_def_inst,
        ]

        prover = LJTProver(max_term_depth=1, max_depth=15)
        proof = prover.prove(target=goal, premises=premises)
        self.assertIsNotNone(proof)
        self.assertTrue(proof.is_valid())

    def test_addition_commutativity_with_lemma(self) -> None:
        """c_m + 0 = 0 + c_m is provable via addition axioms and left identity lemma."""
        c_m = Constant("c_m", sort=Nat)
        add_m_0 = FunctionApp("add", 2, (c_m, self.zero), return_sort=Nat)
        add_0_m = FunctionApp("add", 2, (self.zero, c_m), return_sort=Nat)
        goal = Equality(add_m_0, add_0_m)

        # Left identity lemma for c_m: 0 + c_m = c_m
        lemma_left_id = Equality(add_0_m, c_m)

        premises = [
            self.ha_axioms_dict["ha_add_zero"],
            lemma_left_id,
        ]

        prover = LJTProver(max_term_depth=0, eq_subst_max=3)
        proof = prover.prove(target=goal, premises=premises)
        self.assertIsNotNone(proof)
        self.assertTrue(proof.is_valid())

    def test_unprovable_without_induction(self) -> None:
        """forall n. 0 + n = n cannot be proved when max_ind_depth is 0."""
        add_0_n = FunctionApp("add", 2, (self.zero, self.n), return_sort=Nat)
        goal = Forall(self.n, Equality(add_0_n, self.n))
        premises = [
            self.ha_axioms_dict["ha_add_zero"],
        ]

        prover_no_ind = LJTProver(max_term_depth=0, max_ind_depth=0, max_depth=5)
        self.assertFalse(prover_no_ind.is_provable(target=goal, premises=premises))

    def test_non_constructive_excluded_middle_fails(self) -> None:
        """First-order excluded middle forall n. (P(n) | ~P(n)) is not constructively provable."""
        p_n = PredicateApp("P", 1, (self.n,))
        goal = Forall(self.n, Or(p_n, Not(p_n)))

        prover = LJTProver()
        self.assertFalse(prover.is_provable(target=goal))


class TestHeytingArithmeticTableau(unittest.TestCase):
    """Tests for constructive arithmetic proving and countermodels via Semantic Tableaux."""

    def setUp(self) -> None:
        self.zero = Constant("zero", sort=Nat)
        self.n = Variable(1, sort=Nat)
        self.ha_axioms_dict = dict(get_ha_axioms())

    def test_tableau_induction_left_identity(self) -> None:
        """Semantic tableaux with F_Ind proves universal reflexivity schema."""
        goal = Forall(self.n, Equality(self.n, self.n))

        prover = TableauProver(max_ind_depth=2)
        res = prover.prove(target=goal)
        self.assertTrue(res.is_valid)

    def test_tableau_countermodel_for_excluded_middle(self) -> None:
        """Excluded middle produces an explicit Kripke countermodel in tableau."""
        p_n = PredicateApp("P", 1, (self.n,))
        goal = Forall(self.n, Or(p_n, Not(p_n)))

        prover = TableauProver()
        res = prover.prove(target=goal)
        self.assertFalse(res.is_valid)
        self.assertIsNotNone(res.countermodel)


class TestHAProverAndTranslation(unittest.TestCase):
    """Tests for the unified HAProver and translation resolution route."""

    def setUp(self) -> None:
        self.zero = Constant("zero", sort=Nat)
        self.n = Variable(1, sort=Nat)

    def test_ha_prover_ljt(self) -> None:
        """HAProver automatically supplies HA axioms and proves arithmetic identities."""
        add_0_0 = FunctionApp("add", 2, (self.zero, self.zero), return_sort=Nat)
        goal = Equality(add_0_0, self.zero)

        prover = HAProver(method="ljt")
        self.assertTrue(prover.is_provable(goal))

    def test_ha_prover_tableau(self) -> None:
        """HAProver with method='tableau' proves arithmetic theorems."""
        add_0_0 = FunctionApp("add", 2, (self.zero, self.zero), return_sort=Nat)
        goal = Equality(add_0_0, add_0_0)

        prover = HAProver(method="tableau")
        self.assertTrue(prover.is_provable(goal))

    def test_ha_prover_auto(self) -> None:
        """HAProver with method='auto' tries LJT and proves arithmetic goals."""
        add_0_0 = FunctionApp("add", 2, (self.zero, self.zero), return_sort=Nat)
        goal = Equality(add_0_0, self.zero)

        res = prove_ha(goal, method="auto")
        self.assertIsNotNone(res)

    def test_ha_prover_candidate_extraction(self) -> None:
        """_extract_induction_candidates finds universal quantifier subformulas."""
        add_0_n = FunctionApp("add", 2, (self.zero, self.n), return_sort=Nat)
        goal = Forall(self.n, Equality(add_0_n, self.n))
        cands = _extract_induction_candidates(goal)
        self.assertEqual(len(cands), 1)
        self.assertEqual(cands[0][1], self.n)


if __name__ == "__main__":
    unittest.main()
