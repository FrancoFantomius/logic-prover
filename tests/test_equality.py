import unittest
from typing import List

from logic.core.ast import (
    Variable, Constant, FunctionApp, PredicateApp, Equality,
    Not, And, Or, Implies, Iff, Forall, Exists
)
from logic.core.sorts import Ind
from logic.core.equality import CongruenceClosure, equality_substitution


class TestEquality(unittest.TestCase):

    def setUp(self) -> None:
        self.a = Constant("a", sort=Ind)
        self.b = Constant("b", sort=Ind)
        self.c = Constant("c", sort=Ind)
        self.d = Constant("d", sort=Ind)
        self.x = Variable(1, sort=Ind)

        self.fa = FunctionApp("f", 1, (self.a,), return_sort=Ind)
        self.fb = FunctionApp("f", 1, (self.b,), return_sort=Ind)
        self.gfa = FunctionApp("g", 1, (self.fa,), return_sort=Ind)
        self.gfb = FunctionApp("g", 1, (self.fb,), return_sort=Ind)

        self.fac = FunctionApp("f", 2, (self.a, self.c), return_sort=Ind)
        self.fbd = FunctionApp("f", 2, (self.b, self.d), return_sort=Ind)

    # -------------------------------------------------------------------------
    # 1. Equivalence Properties
    # -------------------------------------------------------------------------

    def test_reflexivity(self) -> None:
        cc = CongruenceClosure()
        self.assertTrue(cc.are_equal(self.a, self.a))
        self.assertTrue(cc.are_equal(self.x, self.x))
        self.assertTrue(cc.are_equal(self.fa, self.fa))

    def test_symmetry(self) -> None:
        cc = CongruenceClosure()
        cc.merge(self.a, self.b)
        self.assertTrue(cc.are_equal(self.a, self.b))
        self.assertTrue(cc.are_equal(self.b, self.a))

    def test_transitivity(self) -> None:
        cc = CongruenceClosure()
        cc.merge(self.a, self.b)
        cc.merge(self.b, self.c)
        self.assertTrue(cc.are_equal(self.a, self.c))
        self.assertTrue(cc.are_equal(self.c, self.a))

    # -------------------------------------------------------------------------
    # 2. Congruence Propagation
    # -------------------------------------------------------------------------

    def test_congruence_propagation_simple(self) -> None:
        cc = CongruenceClosure()
        cc.add_term(self.fa)
        cc.add_term(self.fb)
        self.assertFalse(cc.are_equal(self.fa, self.fb))

        cc.merge(self.a, self.b)
        self.assertTrue(cc.are_equal(self.fa, self.fb))

    def test_congruence_propagation_deep(self) -> None:
        cc = CongruenceClosure()
        cc.add_term(self.gfa)
        cc.add_term(self.gfb)
        self.assertFalse(cc.are_equal(self.gfa, self.gfb))

        cc.merge(self.a, self.b)
        self.assertTrue(cc.are_equal(self.gfa, self.gfb))

    def test_congruence_propagation_multi_arg(self) -> None:
        cc = CongruenceClosure()
        cc.add_term(self.fac)
        cc.add_term(self.fbd)

        cc.merge(self.a, self.b)
        self.assertFalse(cc.are_equal(self.fac, self.fbd))

        cc.merge(self.c, self.d)
        self.assertTrue(cc.are_equal(self.fac, self.fbd))

    # -------------------------------------------------------------------------
    # 3. Explanation Chains
    # -------------------------------------------------------------------------

    def test_explain_direct(self) -> None:
        cc = CongruenceClosure()
        cc.merge(self.a, self.b)
        exp = cc.explain(self.a, self.b)
        self.assertIsNotNone(exp)
        assert exp is not None
        self.assertEqual(len(exp), 1)
        self.assertEqual(exp[0], Equality(self.a, self.b))

    def test_explain_transitive(self) -> None:
        cc = CongruenceClosure()
        cc.merge(self.a, self.b)
        cc.merge(self.b, self.c)
        exp = cc.explain(self.a, self.c)
        self.assertIsNotNone(exp)
        assert exp is not None
        self.assertEqual(len(exp), 2)

    def test_explain_congruence(self) -> None:
        cc = CongruenceClosure()
        cc.add_term(self.fa)
        cc.add_term(self.fb)
        cc.merge(self.a, self.b)
        exp = cc.explain(self.fa, self.fb)
        self.assertIsNotNone(exp)

    def test_explain_unrelated(self) -> None:
        cc = CongruenceClosure()
        cc.add_term(self.a)
        cc.add_term(self.b)
        self.assertIsNone(cc.explain(self.a, self.b))

    def test_explain_identical(self) -> None:
        cc = CongruenceClosure()
        exp = cc.explain(self.a, self.a)
        self.assertEqual(exp, [])

    # -------------------------------------------------------------------------
    # 4. Equality Substitution
    # -------------------------------------------------------------------------

    def test_equality_substitution_atomic(self) -> None:
        eq = Equality(self.a, self.b)
        p_a = PredicateApp("P", 1, (self.a,))
        res = equality_substitution(eq, p_a)
        self.assertEqual(res, [PredicateApp("P", 1, (self.b,))])

    def test_equality_substitution_nested(self) -> None:
        eq = Equality(self.a, self.b)
        ga = FunctionApp("g", 1, (self.a,), return_sort=Ind)
        formula = Equality(self.fa, ga)

        res = equality_substitution(eq, formula)
        gb = FunctionApp("g", 1, (self.b,), return_sort=Ind)

        expected = {
            Equality(self.fb, ga),
            Equality(self.fa, gb),
            Equality(self.fb, gb),
        }
        self.assertEqual(set(res), expected)


if __name__ == "__main__":
    unittest.main()
