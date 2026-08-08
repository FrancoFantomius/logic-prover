import unittest
from dataclasses import FrozenInstanceError

from logic.core.exceptions import InvalidFormulaError
from logic.core.sorts import Ind, Nat, Bool
from logic.core.ast import (
    VariableKind,
    Term,
    Formula,
    Variable,
    Constant,
    FunctionApp,
    PredicateApp,
    Equality,
    Not,
    And,
    Or,
    Implies,
    Iff,
    Forall,
    Exists,
    free_variables,
    bound_variables,
    formula_depth,
    formula_size,
    canonicalize_bound_variables,
)


class TestAST(unittest.TestCase):

    def test_variable_construction_and_validation(self) -> None:
        v0 = Variable(id=0)
        self.assertEqual(v0.id, 0)
        self.assertEqual(v0.sort, Ind)
        self.assertEqual(v0.kind, VariableKind.INDIVIDUAL)

        v1 = Variable(id=1, sort=Nat, kind=VariableKind.PREDICATE)
        self.assertEqual(v1.id, 1)
        self.assertEqual(v1.sort, Nat)
        self.assertEqual(v1.kind, VariableKind.PREDICATE)

        with self.assertRaises(InvalidFormulaError):
            Variable(id=-1)

    def test_constant_construction_and_validation(self) -> None:
        c = Constant(name="c", sort=Bool)
        self.assertEqual(c.name, "c")
        self.assertEqual(c.sort, Bool)

        with self.assertRaises(InvalidFormulaError):
            Constant(name="")

    def test_function_app_construction_and_validation(self) -> None:
        v0 = Variable(id=0)
        f_app = FunctionApp(func="f", arity=1, args=(v0,), return_sort=Nat)
        self.assertEqual(f_app.func, "f")
        self.assertEqual(f_app.arity, 1)
        self.assertEqual(f_app.args, (v0,))
        self.assertEqual(f_app.return_sort, Nat)
        self.assertEqual(f_app.sort, Nat)  # post_init sets sort = return_sort

        with self.assertRaises(InvalidFormulaError):
            FunctionApp(func="", arity=0, args=())

        with self.assertRaises(InvalidFormulaError):
            FunctionApp(func="f", arity=-1, args=())

        with self.assertRaises(InvalidFormulaError):
            FunctionApp(func="f", arity=2, args=(v0,))

    def test_predicate_app_construction_and_validation(self) -> None:
        v0 = Variable(id=0)
        p_app = PredicateApp(pred="P", arity=1, args=(v0,))
        self.assertEqual(p_app.pred, "P")
        self.assertEqual(p_app.arity, 1)
        self.assertEqual(p_app.args, (v0,))

        with self.assertRaises(InvalidFormulaError):
            PredicateApp(pred="", arity=0, args=())

        with self.assertRaises(InvalidFormulaError):
            PredicateApp(pred="P", arity=-1, args=())

        with self.assertRaises(InvalidFormulaError):
            PredicateApp(pred="P", arity=1, args=(v0, v0))

    def test_logical_connectives_and_quantifiers(self) -> None:
        v0 = Variable(id=0)
        v1 = Variable(id=1)
        c = Constant(name="c")

        p = PredicateApp("P", 1, (v0,))
        q = PredicateApp("Q", 1, (v1,))
        eq = Equality(v0, c)

        n = Not(p)
        a = And(p, q)
        o = Or(p, q)
        imp = Implies(p, q)
        iff = Iff(p, q)
        fa = Forall(v0, p)
        ex = Exists(v1, q)

        self.assertEqual(n.operand, p)
        self.assertEqual(a.left, p)
        self.assertEqual(a.right, q)
        self.assertEqual(o.left, p)
        self.assertEqual(o.right, q)
        self.assertEqual(imp.left, p)
        self.assertEqual(imp.right, q)
        self.assertEqual(iff.left, p)
        self.assertEqual(iff.right, q)
        self.assertEqual(fa.variable, v0)
        self.assertEqual(fa.body, p)
        self.assertEqual(ex.variable, v1)
        self.assertEqual(ex.body, q)

    def test_immutability_and_hashing(self) -> None:
        v0 = Variable(id=0)
        v0_same = Variable(id=0)
        v1 = Variable(id=1)

        self.assertEqual(v0, v0_same)
        self.assertEqual(hash(v0), hash(v0_same))
        self.assertNotEqual(v0, v1)

        p1 = PredicateApp("P", 1, (v0,))
        p2 = PredicateApp("P", 1, (v0_same,))
        self.assertEqual(p1, p2)
        self.assertEqual(hash(p1), hash(p2))

        # Check set and dict usage
        s = {p1, p2}
        self.assertEqual(len(s), 1)

        d = {p1: "value"}
        self.assertEqual(d[p2], "value")

        # Confirm frozen immutability
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            v0.id = 5  # type: ignore

        with self.assertRaises((FrozenInstanceError, AttributeError)):
            p1.pred = "Q"  # type: ignore

    def test_free_variables(self) -> None:
        v0 = Variable(id=0)
        v1 = Variable(id=1)
        v2 = Variable(id=2)
        c = Constant(name="c")

        self.assertEqual(free_variables(v0), {v0})
        self.assertEqual(free_variables(c), set())

        f_app = FunctionApp("f", 2, (v0, v1))
        self.assertEqual(free_variables(f_app), {v0, v1})

        p_app = PredicateApp("P", 2, (v1, v0))
        self.assertEqual(free_variables(p_app), {v0, v1})

        eq = Equality(v0, v2)
        self.assertEqual(free_variables(eq), {v0, v2})

        # Forall(v1, P(v1, v0)) -> free vars is {v0}
        fa = Forall(v1, PredicateApp("P", 2, (v1, v0)))
        self.assertEqual(free_variables(fa), {v0})

        # Exists(v0, Forall(v1, P(v1, v0))) -> free vars is empty set
        ex = Exists(v0, fa)
        self.assertEqual(free_variables(ex), set())

        # Connectives
        self.assertEqual(free_variables(Not(p_app)), {v0, v1})
        self.assertEqual(free_variables(And(p_app, eq)), {v0, v1, v2})
        self.assertEqual(free_variables(Or(p_app, eq)), {v0, v1, v2})
        self.assertEqual(free_variables(Implies(p_app, eq)), {v0, v1, v2})
        self.assertEqual(free_variables(Iff(p_app, eq)), {v0, v1, v2})

        with self.assertRaises(InvalidFormulaError):
            free_variables(123)  # type: ignore

    def test_bound_variables(self) -> None:
        v0 = Variable(id=0)
        v1 = Variable(id=1)
        v2 = Variable(id=2)
        c = Constant(name="c")

        self.assertEqual(bound_variables(v0), set())
        self.assertEqual(bound_variables(c), set())
        self.assertEqual(bound_variables(PredicateApp("P", 1, (v0,))), set())

        fa_ex = Forall(v1, Exists(v2, Equality(v1, v2)))
        self.assertEqual(bound_variables(fa_ex), {v1, v2})

        # Connectives
        self.assertEqual(bound_variables(Not(fa_ex)), {v1, v2})
        self.assertEqual(
            bound_variables(And(Forall(v0, PredicateApp("P", 1, (v0,))), fa_ex)),
            {v0, v1, v2},
        )

        with self.assertRaises(InvalidFormulaError):
            bound_variables(123)  # type: ignore

    def test_formula_depth(self) -> None:
        v0 = Variable(id=0)
        v1 = Variable(id=1)
        c = Constant(name="c")

        p = PredicateApp("P", 1, (v0,))
        eq = Equality(v0, c)

        self.assertEqual(formula_depth(p), 1)
        self.assertEqual(formula_depth(eq), 1)
        self.assertEqual(formula_depth(Not(p)), 2)
        self.assertEqual(formula_depth(And(p, eq)), 2)
        self.assertEqual(formula_depth(And(p, Not(eq))), 3)
        self.assertEqual(formula_depth(Forall(v0, Exists(v1, p))), 3)

        with self.assertRaises(InvalidFormulaError):
            formula_depth(v0)  # type: ignore

    def test_formula_size(self) -> None:
        v0 = Variable(id=0)
        v1 = Variable(id=1)
        c = Constant(name="c")
        f = FunctionApp("f", 1, (v1,))

        p = PredicateApp("P", 2, (v0, c))  # size: 1 (P) + 1 (v0) + 1 (c) = 3
        self.assertEqual(formula_size(p), 3)

        eq = Equality(v0, f)  # size: 1 (=) + 1 (v0) + (1 + 1) (f(v1)) = 4
        self.assertEqual(formula_size(eq), 4)

        n = Not(p)  # size: 1 (Not) + 3 (p) = 4
        self.assertEqual(formula_size(n), 4)

        a = And(p, eq)  # size: 1 (And) + 3 (p) + 4 (eq) = 8
        self.assertEqual(formula_size(a), 8)

        fa = Forall(v0, p)  # size: 1 (Forall) + 1 (v0) + 3 (p) = 5
        self.assertEqual(formula_size(fa), 5)

        with self.assertRaises(InvalidFormulaError):
            formula_size(v0)  # type: ignore

    def test_canonicalize_bound_variables(self) -> None:
        # 1. Alpha equivalence equality
        v5 = Variable(id=5)
        v99 = Variable(id=99)
        f1 = Forall(v5, PredicateApp("P", 1, (v5,)))
        f2 = Forall(v99, PredicateApp("P", 1, (v99,)))

        c1 = canonicalize_bound_variables(f1)
        c2 = canonicalize_bound_variables(f2)

        v0_canon = Variable(id=0)
        expected_canon = Forall(v0_canon, PredicateApp("P", 1, (v0_canon,)))

        self.assertEqual(c1, expected_canon)
        self.assertEqual(c2, expected_canon)
        self.assertEqual(c1, c2)

        # 2. Idempotency: canonicalize(canonicalize(f)) == canonicalize(f)
        self.assertEqual(canonicalize_bound_variables(c1), c1)

        # 3. Free variable preservation & non-collision
        # Formula: Forall(v2, P(v0, v2)) where v0 is free
        v0 = Variable(id=0)
        v2 = Variable(id=2)
        f_free = Forall(v2, PredicateApp("P", 2, (v0, v2)))

        c_free = canonicalize_bound_variables(f_free)
        # v0 is free (id 0), so index generator skips 0, assigning id 1 to bound v2
        v1_canon = Variable(id=1)
        expected_c_free = Forall(v1_canon, PredicateApp("P", 2, (v0, v1_canon)))

        self.assertEqual(c_free, expected_c_free)
        self.assertEqual(free_variables(c_free), free_variables(f_free))

        # 4. Multiple quantifiers & nested connectives
        v10 = Variable(id=10)
        v20 = Variable(id=20)
        f_nested = Forall(
            v10,
            Exists(
                v20,
                And(
                    Equality(v10, v20),
                    Or(
                        Implies(PredicateApp("P", 1, (v10,)), PredicateApp("Q", 1, (v20,))),
                        Iff(PredicateApp("R", 1, (v10,)), Not(PredicateApp("S", 1, (v20,)))),
                    ),
                ),
            ),
        )

        c_nested = canonicalize_bound_variables(f_nested)
        self.assertEqual(free_variables(c_nested), set())
        self.assertEqual(bound_variables(c_nested), {Variable(id=0), Variable(id=1)})
        self.assertEqual(canonicalize_bound_variables(c_nested), c_nested)

        # 5. Shadowing
        v1 = Variable(id=1)
        f_shadow = Forall(
            v1,
            And(
                PredicateApp("P", 1, (v1,)),
                Forall(v1, PredicateApp("Q", 1, (v1,))),
            ),
        )
        c_shadow = canonicalize_bound_variables(f_shadow)
        v0_c = Variable(id=0)
        v1_c = Variable(id=1)
        expected_c_shadow = Forall(
            v0_c,
            And(
                PredicateApp("P", 1, (v0_c,)),
                Forall(v1_c, PredicateApp("Q", 1, (v1_c,))),
            ),
        )
        self.assertEqual(c_shadow, expected_c_shadow)

        with self.assertRaises(InvalidFormulaError):
            canonicalize_bound_variables("not_a_formula")  # type: ignore


if __name__ == "__main__":
    unittest.main()
