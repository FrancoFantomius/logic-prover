import unittest
import time
from logic.core.ast import (
    Variable, Constant, FunctionApp, PredicateApp, Equality,
    Not, And, Or, Implies, Iff, Forall, Exists
)
from logic.core.sorts import Ind, Nat
from logic.core.signature import Signature
from logic.core.exceptions import ProofTimeoutError, ProofSearchExhaustedError
from logic.prover.engine import TheoremProver
from logic.kb.numbers import get_peano_signature, get_peano_axioms

class TestProver(unittest.TestCase):

    def setUp(self):
        self.sig = Signature()
        self.sig.register_predicate("P", 1, (Ind,))
        self.sig.register_predicate("Q", 1, (Ind,))
        self.sig.register_predicate("R", 2, (Ind, Ind))
        self.sig.register_predicate("PropP", 0, ())
        self.sig.register_predicate("PropQ", 0, ())
        self.sig.register_constant("a", Ind)
        self.sig.register_constant("b", Ind)
        self.prover = TheoremProver(signature=self.sig)

    def test_propositional_tautology_p_or_not_p(self):
        p = PredicateApp(pred="PropP", arity=0, args=())
        target = Or(left=p, right=Not(operand=p))
        proof = self.prover.prove(target=target)
        self.assertTrue(proof.is_valid())

    def test_propositional_modus_ponens(self):
        p = PredicateApp(pred="PropP", arity=0, args=())
        q = PredicateApp(pred="PropQ", arity=0, args=())
        premise = And(left=Implies(left=p, right=q), right=p)
        target = q
        proof = self.prover.prove(target=target, premises=[premise])
        self.assertTrue(proof.is_valid())

    def test_peirces_law(self):
        p = PredicateApp(pred="PropP", arity=0, args=())
        q = PredicateApp(pred="PropQ", arity=0, args=())
        # ((P => Q) => P) => P
        target = Implies(
            left=Implies(left=Implies(left=p, right=q), right=p),
            right=p
        )
        proof = self.prover.prove(target=target)
        self.assertTrue(proof.is_valid())

    def test_fol_forall_implies_exists(self):
        x = Variable(id=0, sort=Ind)
        p_x = PredicateApp(pred="P", arity=1, args=(x,))
        # (forall x, P(x)) => (exists x, P(x))
        target = Implies(
            left=Forall(variable=x, body=p_x),
            right=Exists(variable=x, body=p_x)
        )
        proof = self.prover.prove(target=target)
        self.assertTrue(proof.is_valid())

    def test_fol_forall_and_distributivity(self):
        x = Variable(id=0, sort=Ind)
        p_x = PredicateApp(pred="P", arity=1, args=(x,))
        q_x = PredicateApp(pred="Q", arity=1, args=(x,))
        # forall x (P(x) & Q(x)) => (forall x P(x) & forall x Q(x))
        target = Implies(
            left=Forall(variable=x, body=And(left=p_x, right=q_x)),
            right=And(
                left=Forall(variable=x, body=p_x),
                right=Forall(variable=x, body=q_x)
            )
        )
        proof = self.prover.prove(target=target)
        self.assertTrue(proof.is_valid())

    def test_fol_exists_forall_implies_forall_exists(self):
        x = Variable(id=0, sort=Ind)
        y = Variable(id=1, sort=Ind)
        r_xy = PredicateApp(pred="R", arity=2, args=(x, y))
        # (exists x forall y R(x, y)) => (forall y exists x R(x, y))
        target = Implies(
            left=Exists(variable=x, body=Forall(variable=y, body=r_xy)),
            right=Forall(variable=y, body=Exists(variable=x, body=r_xy))
        )
        proof = self.prover.prove(target=target)
        self.assertTrue(proof.is_valid())

    def test_peano_theorem_add_zero(self):
        peano_sig = get_peano_signature()
        peano_axioms = [formula for _, formula in get_peano_axioms()]
        prover = TheoremProver(signature=peano_sig)

        zero = Constant("zero", sort=Nat)
        add_0_0 = FunctionApp("add", 2, (zero, zero), return_sort=Nat)
        target = Equality(left=add_0_0, right=zero)

        proof = prover.prove(target=target, premises=peano_axioms)
        self.assertTrue(proof.is_valid())

    def test_proof_timeout_exception(self):
        p = PredicateApp(pred="P", arity=1, args=(Constant("a", sort=Ind),))
        with self.assertRaises(ProofTimeoutError):
            self.prover.prove(target=p, premises=[], timeout_sec=0.000001)

    def test_proof_search_exhausted_exception(self):
        p = PredicateApp(pred="P", arity=1, args=(Constant("a", sort=Ind),))
        with self.assertRaises(ProofSearchExhaustedError):
            self.prover.prove(target=p, premises=[], max_steps=5, timeout_sec=5.0)


if __name__ == "__main__":
    unittest.main()
