import unittest
from logic.core.ast import (
    Variable, Constant, FunctionApp, PredicateApp, Equality,
    Not, And, Or, Implies, Iff, Forall, Exists
)
from logic.core.sorts import Ind
from logic.core.signature import Signature
from logic.prover.clausifier import (
    Literal, Clause, eliminate_implications, to_nnf,
    standardize_variables, skolemize, distribute_cnf, to_cnf,
    negate_and_clausify, reset_skolem_counters
)

class TestClausifier(unittest.TestCase):

    def setUp(self):
        reset_skolem_counters()

    def test_literal_and_clause_properties(self):
        p_x = PredicateApp(pred="P", arity=1, args=(Variable(id=0),))
        l1 = Literal(atom=p_x, positive=True)
        l2 = Literal(atom=p_x, positive=False)

        self.assertEqual(l1.negate(), l2)
        self.assertEqual(l2.negate(), l1)
        self.assertEqual(l1.free_variables(), {Variable(id=0)})

        c_taut = Clause(frozenset([l1, l2]))
        self.assertTrue(c_taut.is_tautology)
        self.assertFalse(c_taut.is_empty)
        self.assertFalse(c_taut.is_unit)

        c_unit = Clause(frozenset([l1]))
        self.assertFalse(c_unit.is_tautology)
        self.assertTrue(c_unit.is_unit)
        self.assertEqual(c_unit.free_variables(), {Variable(id=0)})

        c_empty = Clause(frozenset())
        self.assertTrue(c_empty.is_empty)
        self.assertEqual(c_empty.to_string(), "□")

    def test_eliminate_implications(self):
        p = PredicateApp(pred="P", arity=0, args=())
        q = PredicateApp(pred="Q", arity=0, args=())

        # P => Q -> ~P | Q
        imp = Implies(left=p, right=q)
        elim = eliminate_implications(imp)
        self.assertEqual(elim, Or(left=Not(operand=p), right=q))

        # P <=> Q -> (~P | Q) & (~Q | P)
        iff = Iff(left=p, right=q)
        elim_iff = eliminate_implications(iff)
        expected = And(
            left=Or(left=Not(operand=p), right=q),
            right=Or(left=Not(operand=q), right=p)
        )
        self.assertEqual(elim_iff, expected)

    def test_to_nnf(self):
        x = Variable(id=0)
        p_x = PredicateApp(pred="P", arity=1, args=(x,))
        q_x = PredicateApp(pred="Q", arity=1, args=(x,))

        # ~~(P(x)) -> P(x)
        nnf1 = to_nnf(Not(operand=Not(operand=p_x)))
        self.assertEqual(nnf1, p_x)

        # ~(P(x) & Q(x)) -> ~P(x) | ~Q(x)
        nnf2 = to_nnf(Not(operand=And(left=p_x, right=q_x)))
        expected2 = Or(left=Not(operand=p_x), right=Not(operand=q_x))
        self.assertEqual(nnf2, expected2)

        # ~(forall x, P(x)) -> exists x, ~P(x)
        nnf3 = to_nnf(Not(operand=Forall(variable=x, body=p_x)))
        expected3 = Exists(variable=x, body=Not(operand=p_x))
        self.assertEqual(nnf3, expected3)

    def test_skolemization(self):
        sig = Signature()
        sig.register_predicate("P", 1, (Ind,))
        sig.register_predicate("R", 2, (Ind, Ind))

        # exists x, P(x) -> P(sk_c0)
        x = Variable(id=0)
        p_x = PredicateApp(pred="P", arity=1, args=(x,))
        f_exists = Exists(variable=x, body=p_x)
        sk1 = skolemize(f_exists, signature=sig)
        self.assertIsInstance(sk1, PredicateApp)
        self.assertIsInstance(sk1.args[0], Constant)
        self.assertTrue(sk1.args[0].name.startswith("sk_c"))

        # forall y, exists x, R(x, y) -> forall y, R(sk_f0(y), y)
        reset_skolem_counters()
        y = Variable(id=1)
        r_xy = PredicateApp(pred="R", arity=2, args=(x, y))
        f_forall_exists = Forall(variable=y, body=Exists(variable=x, body=r_xy))
        sk2 = skolemize(f_forall_exists, signature=sig)
        self.assertIsInstance(sk2, Forall)
        self.assertIsInstance(sk2.body, PredicateApp)
        arg0 = sk2.body.args[0]
        self.assertIsInstance(arg0, FunctionApp)
        self.assertEqual(arg0.func, "sk_f0")
        self.assertEqual(arg0.args, (y,))

    def test_distribute_cnf(self):
        p = PredicateApp(pred="P", arity=0, args=())
        q = PredicateApp(pred="Q", arity=0, args=())
        r = PredicateApp(pred="R", arity=0, args=())

        # P | (Q & R) -> (P | Q) & (P | R)
        f = Or(left=p, right=And(left=q, right=r))
        cnf = distribute_cnf(f)
        expected = And(
            left=Or(left=p, right=q),
            right=Or(left=p, right=r)
        )
        self.assertEqual(cnf, expected)

    def test_to_cnf_tautology_removal(self):
        p = PredicateApp(pred="P", arity=0, args=())
        # P | ~P should result in 0 clauses (tautology filtered out)
        f_taut = Or(left=p, right=Not(operand=p))
        clauses = to_cnf(f_taut)
        self.assertEqual(len(clauses), 0)

        # P & Q should result in 2 unit clauses
        q = PredicateApp(pred="Q", arity=0, args=())
        f_and = And(left=p, right=q)
        clauses2 = to_cnf(f_and)
        self.assertEqual(len(clauses2), 2)
        for c in clauses2:
            self.assertTrue(c.is_unit)


if __name__ == "__main__":
    unittest.main()
