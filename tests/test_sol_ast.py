import unittest
from solver.core.ast import Variable, Constant, FunctionApp, PredicateApp, Forall, And, Equality
from solver.core.sorts import Ind, Nat
from solver.core.exceptions import InvalidFormulaError
from solver.sol.ast_ext import (
    PredicateVariable, FunctionVariable,
    ForallPred, ExistsPred, ForallFunc, ExistsFunc,
    free_predicate_variables, bound_predicate_variables,
    free_function_variables, bound_function_variables
)


class TestSOLAST(unittest.TestCase):

    def test_predicate_variable_valid(self):
        pv = PredicateVariable(index=1, arity=2)
        self.assertEqual(pv.index, 1)
        self.assertEqual(pv.arity, 2)
        self.assertEqual(pv.name, "P_1")

    def test_predicate_variable_invalid(self):
        with self.assertRaises(InvalidFormulaError):
            PredicateVariable(index=-1, arity=1)
        with self.assertRaises(InvalidFormulaError):
            PredicateVariable(index=0, arity=-1)

    def test_function_variable_valid(self):
        fv = FunctionVariable(index=0, arity=1, arg_sorts=(Nat,), return_sort=Nat)
        self.assertEqual(fv.index, 0)
        self.assertEqual(fv.arity, 1)
        self.assertEqual(fv.name, "F_0")
        self.assertEqual(fv.arg_sorts, (Nat,))

    def test_function_variable_invalid(self):
        with self.assertRaises(InvalidFormulaError):
            FunctionVariable(index=-1, arity=1, arg_sorts=(Nat,))
        with self.assertRaises(InvalidFormulaError):
            FunctionVariable(index=0, arity=2, arg_sorts=(Nat,))  # Arity mismatch

    def test_immutability_and_hashing(self):
        p1 = PredicateVariable(0, 1)
        p2 = PredicateVariable(0, 1)
        p3 = PredicateVariable(1, 1)
        self.assertEqual(p1, p2)
        self.assertEqual(hash(p1), hash(p2))
        self.assertNotEqual(p1, p3)

        s = {p1, p3}
        self.assertIn(p2, s)

    def test_predicate_variable_extraction(self):
        p0 = PredicateVariable(0, 1)
        p1 = PredicateVariable(1, 1)
        v0 = Variable(0, sort=Ind)

        app0 = PredicateApp(pred=p0, arity=1, args=(v0,))
        app1 = PredicateApp(pred=p1, arity=1, args=(v0,))
        body = And(left=app0, right=app1)
        quantified = ForallPred(variable=p0, body=body)

        free_preds = free_predicate_variables(quantified)
        bound_preds = bound_predicate_variables(quantified)

        self.assertEqual(free_preds, {p1})
        self.assertEqual(bound_preds, {p0})

    def test_function_variable_extraction(self):
        f0 = FunctionVariable(0, 1, arg_sorts=(Ind,))
        f1 = FunctionVariable(1, 1, arg_sorts=(Ind,))
        v0 = Variable(0, sort=Ind)

        term0 = FunctionApp(func=f0, arity=1, args=(v0,), return_sort=Ind)
        term1 = FunctionApp(func=f1, arity=1, args=(v0,), return_sort=Ind)
        eq = Equality(left=term0, right=term1)
        quantified = ForallFunc(variable=f0, body=eq)

        free_funcs = free_function_variables(quantified)
        bound_funcs = bound_function_variables(quantified)

        self.assertEqual(free_funcs, {f1})
        self.assertEqual(bound_funcs, {f0})


if __name__ == "__main__":
    unittest.main()
