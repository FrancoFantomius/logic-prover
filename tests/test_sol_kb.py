import unittest
from solver.core.ast import Variable, Constant, FunctionApp, PredicateApp, Equality, Forall, Implies, And
from solver.core.sorts import Nat, Ind
from solver.sol.ast_ext import PredicateVariable, ExistsPred
from solver.sol.kb_ext import get_sol_axioms, instantiate_comprehension, instantiate_induction


class TestSOLKB(unittest.TestCase):

    def test_get_sol_axioms(self):
        axioms = get_sol_axioms()
        self.assertGreaterEqual(len(axioms), 4)
        names = [name for name, _ in axioms]
        self.assertIn("sol_comprehension_unary", names)
        self.assertIn("sol_comprehension_binary", names)
        self.assertIn("sol_peano_induction", names)

    def test_instantiate_comprehension(self):
        p_var = PredicateVariable(0, 1)
        x = Variable(0, sort=Ind)
        c = Constant("c", sort=Ind)
        body = Equality(left=x, right=c)

        comp = instantiate_comprehension(p_var, (x,), body)
        self.assertTrue(isinstance(comp, ExistsPred))

    def test_instantiate_induction(self):
        n = Variable(0, sort=Nat)
        zero = Constant("zero", sort=Nat)
        add_n_zero = FunctionApp("add", 2, (n, zero), return_sort=Nat)
        prop_formula = Equality(left=add_n_zero, right=n)

        ind_instance = instantiate_induction(prop_formula, n)
        self.assertTrue(isinstance(ind_instance, Implies))
        self.assertTrue(isinstance(ind_instance.left, And))
        self.assertTrue(isinstance(ind_instance.right, Forall))


if __name__ == "__main__":
    unittest.main()
