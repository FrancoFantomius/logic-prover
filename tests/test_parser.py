import unittest

from logic_prover.core.ast import (
    Variable, Constant, FunctionApp, PredicateApp, Equality, Not, And, Or, Implies, Iff, Forall, Exists
)
from logic_prover.core.sorts import Ind, Nat, ParameterizedSort
from logic_prover.core.signature import Signature
from logic_prover.core.exceptions import ParseError
from logic_prover.core.parser import tokenize, TokenType, parse_formula, parse_term, to_string


class TestParser(unittest.TestCase):

    def setUp(self) -> None:
        self.sig = Signature()
        self.sig.register_predicate("P", 1, (Ind,))
        self.sig.register_predicate("Q", 1, (Ind,))
        self.sig.register_predicate("R", 1, (Ind,))
        self.sig.register_predicate("BinaryP", 2, (Ind, Ind))
        self.sig.register_predicate("Prop", 0, ())
        self.sig.register_function("f", 1, (Ind,), return_sort=Ind)
        self.sig.register_function("g", 2, (Ind, Ind), return_sort=Ind)
        self.sig.register_constant("c", sort=Ind)
        self.sig.register_constant("d", sort=Ind)

    def test_lexer_tokenization(self) -> None:
        text = "forall v0 : Ind, (P(v0) => Q(v0))"
        tokens = tokenize(text)
        expected_types = [
            TokenType.QUANTIFIER, TokenType.VARIABLE, TokenType.COLON, TokenType.IDENTIFIER,
            TokenType.COMMA, TokenType.LPAREN, TokenType.IDENTIFIER, TokenType.LPAREN,
            TokenType.VARIABLE, TokenType.RPAREN, TokenType.IMPLIES, TokenType.IDENTIFIER,
            TokenType.LPAREN, TokenType.VARIABLE, TokenType.RPAREN, TokenType.RPAREN,
            TokenType.EOF
        ]
        self.assertEqual([t.type for t in tokens], expected_types)

    def test_lexer_line_and_column_tracking(self) -> None:
        text = "P(v0) &\n Q(v0)"
        tokens = tokenize(text)
        # P: line 1, col 1
        self.assertEqual((tokens[0].line, tokens[0].col), (1, 1))
        # &: line 1, col 7
        self.assertEqual((tokens[4].line, tokens[4].col), (1, 7))
        # Q: line 2, col 2
        self.assertEqual((tokens[5].line, tokens[5].col), (2, 2))

    def test_lexer_invalid_character(self) -> None:
        with self.assertRaises(ParseError) as cm:
            tokenize("P(v0) # Q(v0)")
        self.assertIn("Unexpected character '#'", str(cm.exception))

    def test_operator_precedence_and_associativity(self) -> None:
        # P(v0) & Q(v0) | R(v0) -> Or(And(P(v0), Q(v0)), R(v0))
        f1 = parse_formula("P(v0) & Q(v0) | R(v0)", self.sig)
        v0 = Variable(id=0, sort=Ind)
        expected1 = Or(
            left=And(left=PredicateApp("P", 1, (v0,)), right=PredicateApp("Q", 1, (v0,))),
            right=PredicateApp("R", 1, (v0,))
        )
        self.assertEqual(f1, expected1)

        # P(v0) => Q(v0) => R(v0) -> Right-associative: Implies(P(v0), Implies(Q(v0), R(v0)))
        f2 = parse_formula("P(v0) => Q(v0) => R(v0)", self.sig)
        expected2 = Implies(
            left=PredicateApp("P", 1, (v0,)),
            right=Implies(left=PredicateApp("Q", 1, (v0,)), right=PredicateApp("R", 1, (v0,)))
        )
        self.assertEqual(f2, expected2)

        # ~P(v0) & Q(v0) -> And(Not(P(v0)), Q(v0))
        f3 = parse_formula("~P(v0) & Q(v0)", self.sig)
        expected3 = And(
            left=Not(operand=PredicateApp("P", 1, (v0,))),
            right=PredicateApp("Q", 1, (v0,))
        )
        self.assertEqual(f3, expected3)

    def test_quantifier_and_sort_parsing(self) -> None:
        f1 = parse_formula("forall v0 : Nat, P(v0)", self.sig)
        self.assertIsInstance(f1, Forall)
        assert isinstance(f1, Forall)
        self.assertEqual(f1.variable.sort, Nat)

        f2 = parse_formula("exists v1 : List(Nat), Q(v1)", self.sig)
        self.assertIsInstance(f2, Exists)
        assert isinstance(f2, Exists)
        self.assertEqual(f2.variable.sort, ParameterizedSort("List", (Nat,)))

    def test_error_diagnostics(self) -> None:
        # Unclosed parenthesis
        with self.assertRaises(ParseError) as cm:
            parse_formula("P(v0) & (Q(v0)", self.sig)
        self.assertIn("RPAREN", str(cm.exception))

        # Undeclared predicate
        with self.assertRaises(ParseError) as cm:
            parse_formula("Unknown(v0)", self.sig)
        self.assertIn("Undeclared predicate symbol 'Unknown'", str(cm.exception))

        # Arity mismatch: BinaryP takes 2 args, called with 1
        with self.assertRaises(ParseError) as cm:
            parse_formula("BinaryP(v0)", self.sig)
        self.assertIn("expects 2 arguments, but got 1", str(cm.exception))

    def test_term_parsing(self) -> None:
        v0 = Variable(id=0, sort=Ind)
        c = Constant(name="c", sort=Ind)

        t1 = parse_term("v0", self.sig)
        self.assertEqual(t1, v0)

        t2 = parse_term("c", self.sig)
        self.assertEqual(t2, c)

        t3 = parse_term("f(c)", self.sig)
        self.assertEqual(t3, FunctionApp("f", 1, (c,), return_sort=Ind))

        t4 = parse_term("g(v0, f(c))", self.sig)
        self.assertEqual(t4, FunctionApp("g", 2, (v0, FunctionApp("f", 1, (c,), return_sort=Ind)), return_sort=Ind))

    def test_round_trip_infix(self) -> None:
        v0 = Variable(id=0, sort=Ind)
        v1 = Variable(id=1, sort=Ind)
        c = Constant(name="c", sort=Ind)

        formulas = [
            PredicateApp("P", 1, (v0,)),
            Equality(left=FunctionApp("f", 1, (v0,), return_sort=Ind), right=c),
            Not(operand=PredicateApp("Prop", 0, ())),
            And(left=PredicateApp("P", 1, (v0,)), right=PredicateApp("Q", 1, (v1,))),
            Or(left=PredicateApp("P", 1, (v0,)), right=PredicateApp("Q", 1, (v1,))),
            Implies(left=PredicateApp("P", 1, (v0,)), right=PredicateApp("Q", 1, (v0,))),
            Iff(left=PredicateApp("P", 1, (v0,)), right=PredicateApp("Q", 1, (v0,))),
            Forall(variable=v0, body=Implies(left=PredicateApp("P", 1, (v0,)), right=PredicateApp("Q", 1, (v0,)))),
            Exists(variable=v1, body=And(left=PredicateApp("P", 1, (v1,)), right=Equality(left=v1, right=c)))
        ]

        for f in formulas:
            text = to_string(f, notation="infix")
            parsed = parse_formula(text, self.sig)
            self.assertEqual(parsed, f, f"Round-trip failed for formula: {text}")

    def test_prefix_parsing(self) -> None:
        v0 = Variable(id=0, sort=Ind)
        c = Constant(name="c", sort=Ind)

        # Prefix predicate: (P v0)
        f1 = parse_formula("(P v0)", self.sig)
        self.assertEqual(f1, PredicateApp("P", 1, (v0,)))

        # Prefix equality: (= (f v0) c)
        f2 = parse_formula("(= (f v0) c)", self.sig)
        self.assertEqual(f2, Equality(left=FunctionApp("f", 1, (v0,), return_sort=Ind), right=c))

        # Prefix quantifier and implication: (forall (v0 : Ind) (=> (P v0) (Q v0)))
        f3 = parse_formula("(forall (v0 : Ind) (=> (P v0) (Q v0)))", self.sig)
        expected3 = Forall(
            variable=v0,
            body=Implies(left=PredicateApp("P", 1, (v0,)), right=PredicateApp("Q", 1, (v0,)))
        )
        self.assertEqual(f3, expected3)


if __name__ == "__main__":
    unittest.main()
