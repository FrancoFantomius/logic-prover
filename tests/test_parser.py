import unittest

from solver.formula import (
    parse_formula, Formula, Var, Not, Implies, And, Or, Iff,
    Forall, Exists, Equals, Pred
)
from solver.lean_exporter import formula_to_lean


class TestParser(unittest.TestCase):
    def test_parse_propositional_connectives(self):
        f_not = parse_formula("~p")
        self.assertIsInstance(f_not, Not)

        f_impl = parse_formula("p -> q")
        self.assertIsInstance(f_impl, Implies)

        f_and = parse_formula("p & q")
        self.assertIsInstance(f_and, And)

        f_or = parse_formula("p | q")
        self.assertIsInstance(f_or, Or)

        f_iff = parse_formula("p <-> q")
        self.assertIsInstance(f_iff, Iff)

    def test_parse_quantifiers(self):
        f_forall = parse_formula("forall x, (P(x) -> Q(x))")
        self.assertIsInstance(f_forall, Forall)
        self.assertEqual(f_forall.var, "x")

        f_exists = parse_formula("exists y, P(y)")
        self.assertIsInstance(f_exists, Exists)
        self.assertEqual(f_exists.var, "y")

    def test_parse_equals_and_pred(self):
        f_eq = parse_formula("x = y")
        self.assertIsInstance(f_eq, Equals)

        f_pred = parse_formula("P(x, y)")
        self.assertIsInstance(f_pred, Pred)
        self.assertEqual(f_pred.name, "P")

    def test_formula_substitution(self):
        f = parse_formula("p -> q")
        sub = {'p': parse_formula("A & B"), 'q': parse_formula("C")}
        res = f.substitute(sub)
        self.assertEqual(str(res), "((A & B) -> C)")

    def test_formula_schema_matching(self):
        schema = parse_formula("(forall x, P(x)) -> P(t)")
        concrete = parse_formula("(forall x, Q(x)) -> Q(a)")
        match = concrete.match_schema(schema)
        self.assertIsNotNone(match)
        self.assertEqual(str(match['P']), "Q")
        self.assertEqual(str(match['t']), "a")

    def test_lean_conversion(self):
        f1 = parse_formula("forall x, (P(x) -> Q(x))")
        self.assertEqual(formula_to_lean(f1), "(∀ x, ((P x) → (Q x)))")

        f2 = parse_formula("exists y, (y = x)")
        self.assertEqual(formula_to_lean(f2), "(∃ y, (y = x))")


if __name__ == "__main__":
    unittest.main()
