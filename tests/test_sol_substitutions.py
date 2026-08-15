import unittest
from logic_prover.core.ast import (
    Variable, Constant, FunctionApp, PredicateApp, Forall, And, Equality, Implies
)
from logic_prover.core.sorts import Ind
from logic_prover.sol.ast_ext import PredicateVariable, FunctionVariable
from logic_prover.sol.substitutions_ext import (
    is_ho_pattern, ho_pattern_unify, beta_reduce_predicate, beta_reduce_function,
    substitute_predicate, substitute_function
)


class TestSOLSubstitutions(unittest.TestCase):

    def setUp(self):
        self.p0 = PredicateVariable(0, 1)
        self.p0_2 = PredicateVariable(0, 2)
        self.f0 = FunctionVariable(0, 1, (Ind,))
        self.v0 = Variable(0, sort=Ind)
        self.v1 = Variable(1, sort=Ind)
        self.c0 = Constant("c", sort=Ind)
        self.f_const = FunctionApp("f", 1, (self.v0,), return_sort=Ind)

    def test_is_ho_pattern_valid(self):
        app = PredicateApp(pred=self.p0_2, arity=2, args=(self.v0, self.v1))
        self.assertTrue(is_ho_pattern(app, {self.v0, self.v1}))

    def test_is_ho_pattern_duplicate_arg(self):
        app = PredicateApp(pred=self.p0_2, arity=2, args=(self.v0, self.v0))
        self.assertFalse(is_ho_pattern(app, {self.v0}))

    def test_is_ho_pattern_constant_arg(self):
        app = PredicateApp(pred=self.p0, arity=1, args=(self.c0,))
        self.assertFalse(is_ho_pattern(app, set()))

    def test_is_ho_pattern_nested_term_arg(self):
        app = PredicateApp(pred=self.p0, arity=1, args=(self.f_const,))
        self.assertFalse(is_ho_pattern(app, {self.v0}))

    def test_ho_pattern_unify_success(self):
        pattern = PredicateApp(pred=self.p0, arity=1, args=(self.v0,))
        target = Equality(left=self.v0, right=self.c0)
        subst = ho_pattern_unify(pattern, target, bound_vars={self.v0})

        self.assertIsNotNone(subst)
        self.assertIn(self.p0, subst)
        params, template = subst[self.p0]
        self.assertEqual(params, (self.v0,))
        self.assertEqual(template, target)

    def test_ho_pattern_unify_scope_check_failure(self):
        pattern = PredicateApp(pred=self.p0, arity=1, args=(self.v0,))
        # target contains v1 which is in bound_vars but not in pattern args (v0)
        target = Equality(left=self.v0, right=self.v1)
        subst = ho_pattern_unify(pattern, target, bound_vars={self.v0, self.v1})
        self.assertIsNone(subst)

    def test_ho_pattern_unify_occurrences_check_failure(self):
        pattern = PredicateApp(pred=self.p0, arity=1, args=(self.v0,))
        # target contains P0 itself
        target = And(left=pattern, right=Equality(left=self.v0, right=self.c0))
        subst = ho_pattern_unify(pattern, target, bound_vars={self.v0})
        self.assertIsNone(subst)

    def test_beta_reduce_predicate(self):
        x1 = Variable(0, sort=Ind)
        x2 = Variable(1, sort=Ind)
        template = Equality(left=x1, right=x2)
        t1 = Constant("a", sort=Ind)
        t2 = Constant("b", sort=Ind)

        reduced = beta_reduce_predicate(template, (x1, x2), (t1, t2))
        self.assertEqual(reduced, Equality(left=t1, right=t2))

    def test_substitute_predicate(self):
        p_var = PredicateVariable(0, 2)
        x1 = Variable(10, sort=Ind)
        x2 = Variable(11, sort=Ind)
        template = Equality(left=x1, right=x2)

        app = PredicateApp(pred=p_var, arity=2, args=(self.v0, self.v1))
        formula = Implies(left=app, right=app)

        res = substitute_predicate(formula, {p_var: ((x1, x2), template)})
        expected_eq = Equality(left=self.v0, right=self.v1)
        self.assertEqual(res, Implies(left=expected_eq, right=expected_eq))


if __name__ == "__main__":
    unittest.main()
