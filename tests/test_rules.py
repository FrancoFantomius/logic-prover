import unittest
from solver.core.ast import (
    Variable, Constant, FunctionApp, PredicateApp, Equality, Not
)
from solver.core.sorts import Ind
from solver.prover.clausifier import Literal, Clause
from solver.prover.rules import (
    standardize_clause_variables, resolve_clauses, factor_clause,
    paramodulate, get_resolution_rules, get_reconstruction_rules
)

class TestRules(unittest.TestCase):

    def test_standardize_clause_variables(self):
        x = Variable(id=0)
        p_x = PredicateApp(pred="P", arity=1, args=(x,))
        q_x = PredicateApp(pred="Q", arity=1, args=(x,))

        c1 = Clause(frozenset([Literal(atom=p_x, positive=True)]))
        c2 = Clause(frozenset([Literal(atom=q_x, positive=False)]))

        std_c1, std_c2, var_map = standardize_clause_variables(c1, c2)
        vars1 = std_c1.free_variables()
        vars2 = std_c2.free_variables()
        self.assertEqual(len(vars1 & vars2), 0)

    def test_resolve_clauses(self):
        x = Variable(id=0)
        a = Constant(name="a", sort=Ind)
        p_x = PredicateApp(pred="P", arity=1, args=(x,))
        p_a = PredicateApp(pred="P", arity=1, args=(a,))
        q_x = PredicateApp(pred="Q", arity=1, args=(x,))

        # c1: P(x) v Q(x), c2: ~P(a)
        l1 = Literal(atom=p_x, positive=True)
        l2 = Literal(atom=q_x, positive=True)
        l3 = Literal(atom=p_a, positive=False)

        c1 = Clause(frozenset([l1, l2]))
        c2 = Clause(frozenset([l3]))

        resolvents = resolve_clauses(c1, c2)
        self.assertEqual(len(resolvents), 1)

        res_clause, mgu, (l_c1, l_c2) = resolvents[0]
        self.assertEqual(len(res_clause.literals), 1)
        res_lit = list(res_clause.literals)[0]
        self.assertEqual(res_lit.atom, PredicateApp(pred="Q", arity=1, args=(a,)))

    def test_factor_clause(self):
        x = Variable(id=0)
        a = Constant(name="a", sort=Ind)
        p_x = PredicateApp(pred="P", arity=1, args=(x,))
        p_a = PredicateApp(pred="P", arity=1, args=(a,))

        # c: P(x) v P(a)
        l1 = Literal(atom=p_x, positive=True)
        l2 = Literal(atom=p_a, positive=True)
        c = Clause(frozenset([l1, l2]))

        factored_results = factor_clause(c)
        self.assertEqual(len(factored_results), 1)
        factored_c, mgu = factored_results[0]
        self.assertEqual(len(factored_c.literals), 1)
        self.assertEqual(list(factored_c.literals)[0].atom, p_a)

    def test_paramodulate(self):
        a = Constant(name="a", sort=Ind)
        b = Constant(name="b", sort=Ind)
        eq_ab = Equality(left=a, right=b)

        p_a = PredicateApp(pred="P", arity=1, args=(a,))

        # c1: a = b, c2: P(a)
        c1 = Clause(frozenset([Literal(atom=eq_ab, positive=True)]))
        c2 = Clause(frozenset([Literal(atom=p_a, positive=True)]))

        param_results = paramodulate(c1, c2)
        self.assertGreaterEqual(len(param_results), 1)

        found_pb = False
        for param_c, mgu in param_results:
            if any(lit.atom == PredicateApp(pred="P", arity=1, args=(b,)) for lit in param_c.literals):
                found_pb = True
                break
        self.assertTrue(found_pb)

    def test_get_rules(self):
        res_rules = get_resolution_rules()
        rec_rules = get_reconstruction_rules()
        self.assertEqual(len(res_rules), 3)
        self.assertGreaterEqual(len(rec_rules), 10)


if __name__ == "__main__":
    unittest.main()
