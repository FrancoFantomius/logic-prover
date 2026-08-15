import unittest

from logic_prover.core.ast import (
    Variable, Constant, FunctionApp, PredicateApp, Equality,
    Not, And, Or, Implies, Iff, Forall, Exists
)
from logic_prover.core.sorts import Ind
from logic_prover.core.exceptions import RewriteDivergenceError, ValidationError
from logic_prover.core.rewriter import (
    RewriteRule, match_term, match_formula, rewrite, rewrite_all, normalize
)


class TestRewriter(unittest.TestCase):

    def setUp(self) -> None:
        self.x = Variable(1, sort=Ind)
        self.y = Variable(2, sort=Ind)
        self.a = Constant("a", sort=Ind)
        self.b = Constant("b", sort=Ind)
        self.zero = Constant("0", sort=Ind)

        self.px = PredicateApp("P", 1, (self.x,))
        self.pa = PredicateApp("P", 1, (self.a,))
        self.qa = PredicateApp("Q", 1, (self.a,))

        self.add_x_0 = FunctionApp("add", 2, (self.x, self.zero), return_sort=Ind)
        self.add_a_0 = FunctionApp("add", 2, (self.a, self.zero), return_sort=Ind)

    # -------------------------------------------------------------------------
    # 1. Pattern Matching Tests
    # -------------------------------------------------------------------------

    def test_match_term_variable(self) -> None:
        subst = match_term(self.x, self.a)
        self.assertEqual(subst, {self.x: self.a})

        f_x = FunctionApp("f", 1, (self.x,), return_sort=Ind)
        subst2 = match_term(self.x, f_x)
        self.assertEqual(subst2, {self.x: f_x})

    def test_match_term_inconsistent_variable(self) -> None:
        pattern = FunctionApp("f", 2, (self.x, self.x), return_sort=Ind)
        target = FunctionApp("f", 2, (self.a, self.b), return_sort=Ind)
        self.assertIsNone(match_term(pattern, target))

        target_consistent = FunctionApp("f", 2, (self.a, self.a), return_sort=Ind)
        self.assertEqual(match_term(pattern, target_consistent), {self.x: self.a})

    def test_match_formula_predicate_and_connectives(self) -> None:
        pattern = Not(self.px)
        target = Not(self.pa)
        self.assertEqual(match_formula(pattern, target), {self.x: self.a})

        pattern_and = And(self.px, PredicateApp("Q", 1, (self.y,)))
        target_and = And(self.pa, self.qa)
        self.assertEqual(match_formula(pattern_and, target_and), {self.x: self.a, self.y: self.a})

    # -------------------------------------------------------------------------
    # 2. RewriteRule Validation and Root Rewrite Tests
    # -------------------------------------------------------------------------

    def test_rewrite_rule_validation(self) -> None:
        with self.assertRaises(ValidationError):
            RewriteRule(lhs=self.x, rhs=self.pa)

        with self.assertRaises(ValidationError):
            RewriteRule(lhs=self.pa, rhs=self.x)

    def test_root_rewrite_double_negation(self) -> None:
        not_not_px = Not(Not(self.px))
        rule = RewriteRule(lhs=not_not_px, rhs=self.px, name="double_neg")

        target = Not(Not(self.pa))
        res = rewrite(target, rule)
        self.assertEqual(res, self.pa)

    def test_root_rewrite_identity(self) -> None:
        rule = RewriteRule(lhs=self.add_x_0, rhs=self.x, name="add_zero")
        res = rewrite(self.add_a_0, rule)
        self.assertEqual(res, self.a)

    def test_root_rewrite_conditional(self) -> None:
        # Rule: add(x, y) -> x IF y = 0
        cond = Equality(self.y, self.zero)
        rule = RewriteRule(
            lhs=FunctionApp("add", 2, (self.x, self.y), return_sort=Ind),
            rhs=self.x,
            condition=cond,
            name="add_cond"
        )
        # add(a, 0) matches and condition (0 = 0) holds
        res1 = rewrite(self.add_a_0, rule)
        self.assertEqual(res1, self.a)

        # add(a, b) matches but condition (b = 0) fails
        add_a_b = FunctionApp("add", 2, (self.a, self.b), return_sort=Ind)
        res2 = rewrite(add_a_b, rule)
        self.assertIsNone(res2)

    # -------------------------------------------------------------------------
    # 3. Bottom-Up rewrite_all Tests
    # -------------------------------------------------------------------------

    def test_rewrite_all_nested_double_negation(self) -> None:
        rule = RewriteRule(lhs=Not(Not(self.px)), rhs=self.px)
        deep = Not(Not(Not(Not(self.pa))))
        res = rewrite_all(deep, [rule])
        self.assertEqual(res, self.pa)

    def test_rewrite_all_cascading(self) -> None:
        rule = RewriteRule(lhs=self.add_x_0, rhs=self.x)
        # (a + 0) + 0 -> a
        nested = FunctionApp("add", 2, (self.add_a_0, self.zero), return_sort=Ind)
        res = rewrite_all(nested, [rule])
        self.assertEqual(res, self.a)

    # -------------------------------------------------------------------------
    # 4. Formula Normalization & Divergence Tests
    # -------------------------------------------------------------------------

    def test_normalize_fixed_point(self) -> None:
        rule1 = RewriteRule(lhs=Not(Not(self.px)), rhs=self.px)
        rule2 = RewriteRule(lhs=Implies(self.px, PredicateApp("Q", 1, (self.y,))),
                            rhs=Or(Not(self.px), PredicateApp("Q", 1, (self.y,))))

        f = Implies(Not(Not(self.pa)), self.qa)
        normalized = normalize(f, [rule1, rule2])
        expected = Or(Not(self.pa), self.qa)
        self.assertEqual(normalized, expected)

    def test_normalize_divergence_error(self) -> None:
        # Non-terminating rule: P(x) -> Not(Not(P(x)))
        circular_rule = RewriteRule(lhs=self.px, rhs=Not(Not(self.px)))

        with self.assertRaises(RewriteDivergenceError):
            normalize(self.pa, [circular_rule], max_steps=10)


if __name__ == "__main__":
    unittest.main()
