import unittest
from logic_prover.core.ast import Variable, Constant, FunctionApp, PredicateApp, Equality, Forall, Implies, Or, Iff
from logic_prover.core.sorts import Nat, Ind
from logic_prover.core.signature import Signature
from logic_prover.prover.engine import TheoremProver
from logic_prover.sol.ast_ext import PredicateVariable, ExistsPred
from logic_prover.sol.kb_ext import instantiate_induction, instantiate_comprehension, get_sol_axioms
from logic_prover.prover.rules import SOLInstantiateRule


class TestSOLProver(unittest.TestCase):

    def setUp(self):
        self.sig = Signature()
        self.sig.register_constant("zero", Nat)
        self.sig.register_constant("one", Nat)
        self.sig.register_function("succ", 1, (Nat,), Nat)
        self.sig.register_function("add", 2, (Nat, Nat), Nat)
        self.prover = TheoremProver(signature=self.sig)

    def test_sol_instantiate_rule(self):
        n = Variable(0, sort=Nat)
        zero = Constant("zero", sort=Nat)
        add_n_zero = FunctionApp("add", 2, (n, zero), return_sort=Nat)
        target = Forall(variable=n, body=Equality(left=add_n_zero, right=n))

        sol_axioms = get_sol_axioms()
        peano_ax = next(fmt for name, fmt in sol_axioms if name == "sol_peano_induction")

        rule = SOLInstantiateRule()
        clauses = rule.match_and_instantiate(peano_ax, target, signature=self.sig)
        self.assertGreater(len(clauses), 0)

    def test_inductive_proof(self):
        n = Variable(0, sort=Nat)
        zero = Constant("zero", sort=Nat)
        v_x = Variable(10, sort=Nat)
        v_y = Variable(11, sort=Nat)

        # add(0, y) = y
        ax1 = Forall(variable=v_y, body=Equality(left=FunctionApp("add", 2, (zero, v_y), return_sort=Nat), right=v_y))
        # add(succ(x), y) = succ(add(x, y))
        succ_x = FunctionApp("succ", 1, (v_x,), return_sort=Nat)
        add_x_y = FunctionApp("add", 2, (v_x, v_y), return_sort=Nat)
        ax2 = Forall(variable=v_x, body=Forall(variable=v_y, body=Equality(
            left=FunctionApp("add", 2, (succ_x, v_y), return_sort=Nat),
            right=FunctionApp("succ", 1, (add_x_y,), return_sort=Nat)
        )))

        # Target: add(zero, zero) = zero
        target = Equality(left=FunctionApp("add", 2, (zero, zero), return_sort=Nat), right=zero)

        proof = self.prover.prove(target=target, premises=[ax1, ax2])
        self.assertIsNotNone(proof)

    def test_comprehension_instantiation(self):
        x = Variable(0, sort=Nat)
        c0 = Constant("zero", sort=Nat)
        c1 = Constant("one", sort=Nat)
        body = Or(left=Equality(left=x, right=c0), right=Equality(left=x, right=c1))

        p_var = PredicateVariable(0, 1)
        comp_instance = instantiate_comprehension(p_var, (x,), body)
        self.assertTrue(isinstance(comp_instance, ExistsPred))


if __name__ == "__main__":
    unittest.main()
