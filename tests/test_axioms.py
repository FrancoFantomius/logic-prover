"""Comprehensive test suite for logic_prover.axioms mathematical theories."""

from __future__ import annotations
import unittest

from logic_prover.core.ast import (
    Variable, Constant, FunctionApp, PredicateApp, Equality, Forall, Implies, And, Not
)
from logic_prover.core.validator import validate_formula
from logic_prover.axioms import (
    Theory,
    get_theory,
    list_theories,
    get_all_theories,
    get_all_axioms,
    get_extended_axioms,
    get_combined_signature,
    group_theory,
    abelian_group_theory,
    peano_theory,
    zfc_theory,
    analysis_theory,
    linear_algebra_theory,
    ring_theory,
    field_theory,
    partial_order_theory,
    total_order_theory,
    lattice_theory,
    boolean_algebra_theory,
    relation_theory,
    equivalence_relation_theory,
    function_theory,
    equality_theory,
    fol_theory,
    GroupElem,
    RelElem,
    OrderElem,
    SetElem,
    SetType,
    Dom,
    Codom,
    FuncSort,
    Real,
    Vector,
    Scalar,
    RingElem,
    BoolElem,
)
from logic_prover.core.sorts import Nat, Ind


class TestAxioms(unittest.TestCase):
    """Test suite verifying signature well-formedness, AST validation, and prover execution across all theories."""

    def test_theory_registry(self) -> None:
        theories = list_theories()
        self.assertIn("group_theory", theories)
        self.assertIn("peano", theories)
        self.assertIn("zfc", theories)
        self.assertIn("analysis", theories)
        self.assertIn("linear_algebra", theories)
        self.assertIn("ring_theory", theories)
        self.assertIn("field_theory", theories)
        self.assertIn("partial_order", theories)
        self.assertIn("total_order", theories)
        self.assertIn("lattice_theory", theories)
        self.assertIn("boolean_algebra", theories)
        self.assertIn("relations", theories)
        self.assertIn("equivalence_relations", theories)
        self.assertIn("functions", theories)
        self.assertIn("equality", theories)
        self.assertIn("logic", theories)

        all_th = get_all_theories()
        self.assertEqual(len(all_th), len(theories))
        for name in theories:
            self.assertIsNotNone(get_theory(name))

    def test_all_theories_validate(self) -> None:
        """Verify that theory.validate() passes with zero errors for all registered theories."""
        for name, th in get_all_theories().items():
            errors = th.validate()
            self.assertEqual(errors, [], f"Theory '{name}' failed validation: {errors}")

    def test_combined_signature_and_all_axioms(self) -> None:
        sig = get_combined_signature()
        self.assertTrue(sig.has_symbol("op"))
        self.assertTrue(sig.has_symbol("add"))
        self.assertTrue(sig.has_symbol("vadd"))
        self.assertTrue(sig.has_symbol("bmeet"))
        self.assertTrue(sig.has_symbol("rmul"))
        self.assertTrue(sig.has_symbol("choice"))
        self.assertTrue(sig.has_symbol("dist"))

        all_ax = get_all_axioms()
        self.assertGreater(len(all_ax), 30)
        for name, formula, category in all_ax:
            errors = validate_formula(formula, sig)
            self.assertEqual(errors, [], f"Axiom '{name}' in category '{category}' failed validation: {errors}")

    def test_group_theory_prover(self) -> None:
        """Prove that a right identity element e' with op(x, e') = x satisfies e' = e."""
        v0 = Variable(0, sort=GroupElem)
        e = Constant("e", sort=GroupElem)
        i = Variable(0, sort=GroupElem)
        x = Variable(1, sort=GroupElem)

        id_right = Forall(v0, Equality(FunctionApp("op", 2, (v0, e), return_sort=GroupElem), v0))
        op_i_x = FunctionApp("op", 2, (i, x), return_sort=GroupElem)
        target = Forall(i, Implies(Forall(x, Equality(op_i_x, x)), Equality(i, e)))

        proof = group_theory.prove(target=target, premises=[id_right], include_theory_axioms=False, timeout_sec=5.0)
        self.assertTrue(proof.is_valid())

    def test_linear_algebra_theory_properties(self) -> None:
        sig = linear_algebra_theory.signature
        self.assertTrue(sig.has_symbol("vadd"))
        self.assertTrue(sig.has_symbol("smul_v"))
        self.assertTrue(sig.has_symbol("dot"))
        self.assertTrue(sig.has_symbol("orthogonal"))
        self.assertEqual(len(linear_algebra_theory.axioms), 14)

    def test_analysis_theory_properties(self) -> None:
        sig = analysis_theory.signature
        self.assertTrue(sig.has_symbol("real_add"))
        self.assertTrue(sig.has_symbol("real_mul"))
        self.assertTrue(sig.has_symbol("dist"))
        self.assertTrue(sig.has_symbol("abs_val"))
        self.assertGreaterEqual(len(analysis_theory.axioms), 20)

    def test_zfc_theory_prover(self) -> None:
        """Prove subset transitivity from ZFC subset definition."""
        A = Variable(0, sort=SetType)
        B = Variable(1, sort=SetType)
        C = Variable(2, sort=SetType)
        x = Variable(3, sort=SetElem)

        in_xA = PredicateApp("in_set", 2, (x, A))
        in_xB = PredicateApp("in_set", 2, (x, B))
        sub_AB = PredicateApp("subset", 2, (A, B))
        sub_BC = PredicateApp("subset", 2, (B, C))
        sub_AC = PredicateApp("subset", 2, (A, C))

        subset_def = Forall(A, Forall(B, Equality(sub_AB, Forall(x, Implies(in_xA, in_xB)))))
        # Using zfc_theory's zfc_subset_def axiom
        subset_ax = zfc_theory.get_axiom("zfc_subset_def")
        self.assertIsNotNone(subset_ax)

        target = Forall(A, Forall(B, Forall(C, Implies(And(sub_AB, sub_BC), sub_AC))))
        proof = zfc_theory.prove(target=target, premises=[subset_ax], include_theory_axioms=False, timeout_sec=5.0)
        self.assertTrue(proof.is_valid())

    def test_relation_theory_prover(self) -> None:
        """Prove that irreflexive and transitive relation implies asymmetric."""
        x = Variable(0, sort=RelElem)
        y = Variable(1, sort=RelElem)
        z = Variable(2, sort=RelElem)

        r_xx = PredicateApp("R", 2, (x, x))
        r_xy = PredicateApp("R", 2, (x, y))
        r_yz = PredicateApp("R", 2, (y, z))
        r_xz = PredicateApp("R", 2, (x, z))
        r_yx = PredicateApp("R", 2, (y, x))

        rel_irreflexive = Forall(x, Not(r_xx))
        rel_transitive = Forall(x, Forall(y, Forall(z, Implies(And(r_xy, r_yz), r_xz))))
        target = Forall(x, Forall(y, Implies(r_xy, Not(r_yx))))

        proof = relation_theory.prove(
            target=target,
            premises=[rel_irreflexive, rel_transitive],
            include_theory_axioms=False,
            timeout_sec=5.0,
        )
        self.assertTrue(proof.is_valid())

    def test_boolean_algebra_properties(self) -> None:
        sig = boolean_algebra_theory.signature
        self.assertTrue(sig.has_symbol("bmeet"))
        self.assertTrue(sig.has_symbol("bjoin"))
        self.assertTrue(sig.has_symbol("bneg"))
        self.assertTrue(sig.has_symbol("top"))
        self.assertTrue(sig.has_symbol("bot"))
        self.assertEqual(len(boolean_algebra_theory.axioms), 12)

    def test_ring_and_field_properties(self) -> None:
        self.assertEqual(len(ring_theory.axioms), 9)
        self.assertEqual(len(field_theory.axioms), 12)
        self.assertTrue(field_theory.signature.has_symbol("rinv"))


if __name__ == "__main__":
    unittest.main()
