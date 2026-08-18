import random
import string
import unittest

from logic_prover.core.ast import (
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
)
from logic_prover.core.sorts import Ind, Nat, Bool, PrimitiveSort
from logic_prover.core.exceptions import UnificationError, SortMismatchError
from logic_prover.core.substitutions import (
    substitute_term,
    substitute_formula,
    apply_substitution,
    compose_substitutions,
    unify_terms,
    unify_formulas,
    SubstitutionTransformer,
)


class TestSubstitutions(unittest.TestCase):

    # -------------------------------------------------------------------------
    # 1. Term & Formula Substitution Tests
    # -------------------------------------------------------------------------

    def test_substitute_term_simple(self) -> None:
        x = Variable(1, sort=Ind)
        y = Variable(2, sort=Ind)
        c = Constant("c", sort=Ind)
        t = FunctionApp("f", 2, (x, y), Ind)

        # Substitute x -> c
        res = substitute_term(t, {x: c})
        self.assertEqual(res, FunctionApp("f", 2, (c, y), Ind))

        # Empty substitution returns identical term
        self.assertEqual(substitute_term(t, {}), t)

    def test_substitute_term_multiple(self) -> None:
        x = Variable(1, sort=Ind)
        y = Variable(2, sort=Ind)
        c1 = Constant("c1", sort=Ind)
        c2 = Constant("c2", sort=Ind)
        t = FunctionApp("f", 2, (x, y), Ind)

        res = substitute_term(t, {x: c1, y: c2})
        self.assertEqual(res, FunctionApp("f", 2, (c1, c2), Ind))

    def test_substitute_formula_atomic(self) -> None:
        x = Variable(1, sort=Ind)
        c = Constant("c", sort=Ind)

        p = PredicateApp("P", 1, (x,))
        eq = Equality(x, c)

        self.assertEqual(substitute_formula(p, {x: c}), PredicateApp("P", 1, (c,)))
        self.assertEqual(substitute_formula(eq, {x: c}), Equality(c, c))

    def test_substitute_formula_connectives(self) -> None:
        x = Variable(1, sort=Ind)
        y = Variable(2, sort=Ind)
        c = Constant("c", sort=Ind)

        p = PredicateApp("P", 1, (x,))
        q = PredicateApp("Q", 1, (y,))

        n = Not(p)
        a = And(p, q)
        o = Or(p, q)
        imp = Implies(p, q)
        iff = Iff(p, q)

        subst = {x: c}
        self.assertEqual(substitute_formula(n, subst), Not(PredicateApp("P", 1, (c,))))
        self.assertEqual(
            substitute_formula(a, subst),
            And(PredicateApp("P", 1, (c,)), PredicateApp("Q", 1, (y,))),
        )
        self.assertEqual(
            substitute_formula(o, subst),
            Or(PredicateApp("P", 1, (c,)), PredicateApp("Q", 1, (y,))),
        )
        self.assertEqual(
            substitute_formula(imp, subst),
            Implies(PredicateApp("P", 1, (c,)), PredicateApp("Q", 1, (y,))),
        )
        self.assertEqual(
            substitute_formula(iff, subst),
            Iff(PredicateApp("P", 1, (c,)), PredicateApp("Q", 1, (y,))),
        )

    def test_substitute_formula_shadowing(self) -> None:
        x = Variable(1, sort=Ind)
        c = Constant("c", sort=Ind)

        # Forall(x, P(x)) with mapping x -> c
        # Bound x shadows free x, so inside Forall, x must NOT be substituted
        body = PredicateApp("P", 1, (x,))
        f_forall = Forall(x, body)
        f_exists = Exists(x, body)

        self.assertEqual(substitute_formula(f_forall, {x: c}), f_forall)
        self.assertEqual(substitute_formula(f_exists, {x: c}), f_exists)

    def test_substitute_formula_capture_avoidance(self) -> None:
        x = Variable(1, sort=Ind)
        y = Variable(2, sort=Ind)

        # Formula: Forall(y, P(x, y))
        # Substitute x -> y
        # Direct substitution would yield Forall(y, P(y, y)) capturing y.
        # Capture avoidance must alpha-rename bound y to a fresh variable.
        body = PredicateApp("P", 2, (x, y))
        formula = Forall(y, body)

        res = substitute_formula(formula, {x: y})
        self.assertIsInstance(res, Forall)
        self.assertNotEqual(res.variable, y)
        self.assertNotEqual(res.variable, x)
        self.assertEqual(free_variables(res), {y})

        # Check Exists as well
        formula_ex = Exists(y, body)
        res_ex = substitute_formula(formula_ex, {x: y})
        self.assertIsInstance(res_ex, Exists)
        self.assertNotEqual(res_ex.variable, y)
        self.assertNotEqual(res_ex.variable, x)
        self.assertEqual(free_variables(res_ex), {y})

    def test_substitute_sort_mismatch(self) -> None:
        x_nat = Variable(1, sort=Nat)
        c_bool = Constant("c", sort=Bool)

        with self.assertRaises(SortMismatchError):
            substitute_term(x_nat, {x_nat: c_bool})

        with self.assertRaises(SortMismatchError):
            p = PredicateApp("P", 1, (x_nat,))
            substitute_formula(p, {x_nat: c_bool})

    # -------------------------------------------------------------------------
    # 2. Substitution Composition Tests
    # -------------------------------------------------------------------------

    def test_apply_substitution_wrapper(self) -> None:
        x = Variable(1, sort=Ind)
        c = Constant("c", sort=Ind)
        self.assertEqual(apply_substitution({x: c}, x), c)

    def test_compose_substitutions_basic(self) -> None:
        x = Variable(1, sort=Ind)
        y = Variable(2, sort=Ind)
        a = Constant("a", sort=Ind)

        s1 = {y: a}
        s2 = {x: y}

        composed = compose_substitutions(s1, s2)
        # s1 o s2 applied to x: s1(s2(x)) = s1(y) = a
        self.assertEqual(apply_substitution(composed, x), a)
        self.assertEqual(
            apply_substitution(composed, x),
            apply_substitution(s1, apply_substitution(s2, x)),
        )

    def test_compose_substitutions_identity_elimination(self) -> None:
        x = Variable(1, sort=Ind)
        s1 = {x: x}
        s2 = {}
        composed = compose_substitutions(s1, s2)
        self.assertEqual(composed, {})

    def test_compose_substitutions_overlapping(self) -> None:
        x = Variable(1, sort=Ind)
        y = Variable(2, sort=Ind)
        z = Variable(3, sort=Ind)
        c = Constant("c", sort=Ind)

        s1 = {y: c, z: x}
        s2 = {x: y}

        # (s1 o s2)(x) = s1(s2(x)) = s1(y) = c
        # (s1 o s2)(y) = s1(y) = c
        # (s1 o s2)(z) = s1(z) = x
        composed = compose_substitutions(s1, s2)
        self.assertEqual(composed[x], c)
        self.assertEqual(composed[y], c)
        self.assertEqual(composed[z], x)

    def test_compose_substitutions_sort_mismatch(self) -> None:
        x_nat = Variable(1, sort=Nat)
        c_bool = Constant("c", sort=Bool)

        with self.assertRaises(SortMismatchError):
            compose_substitutions({x_nat: c_bool}, {})

        with self.assertRaises(SortMismatchError):
            compose_substitutions({}, {x_nat: c_bool})

    # -------------------------------------------------------------------------
    # 3. Unification Tests
    # -------------------------------------------------------------------------

    def test_unify_terms_identical(self) -> None:
        x = Variable(1, sort=Ind)
        c = Constant("c", sort=Ind)
        f = FunctionApp("f", 1, (x,), Ind)

        self.assertEqual(unify_terms(x, x), {})
        self.assertEqual(unify_terms(c, c), {})
        self.assertEqual(unify_terms(f, f), {})

    def test_unify_terms_variable_term(self) -> None:
        x = Variable(1, sort=Ind)
        c = Constant("c", sort=Ind)

        subst = unify_terms(x, c)
        self.assertEqual(subst, {x: c})

        subst_rev = unify_terms(c, x)
        self.assertEqual(subst_rev, {x: c})

    def test_unify_terms_occur_check(self) -> None:
        x = Variable(1, sort=Ind)
        fx = FunctionApp("f", 1, (x,), Ind)

        with self.assertRaises(UnificationError):
            unify_terms(x, fx)

        with self.assertRaises(UnificationError):
            unify_terms(fx, x)

    def test_unify_terms_occur_check_transitive(self) -> None:
        x = Variable(1, sort=Ind)
        y = Variable(2, sort=Ind)
        fy = FunctionApp("f", 1, (y,), Ind)

        # Context has y -> x, now unifying x with f(y) which is f(x)
        with self.assertRaises(UnificationError):
            unify_terms(x, fy, {y: x})

    def test_unify_terms_sort_mismatch(self) -> None:
        x_nat = Variable(1, sort=Nat)
        c_bool = Constant("c", sort=Bool)

        with self.assertRaises(SortMismatchError):
            unify_terms(x_nat, c_bool)

    def test_unify_terms_constant_mismatch(self) -> None:
        c1 = Constant("c1", sort=Ind)
        c2 = Constant("c2", sort=Ind)

        with self.assertRaises(UnificationError):
            unify_terms(c1, c2)

    def test_unify_terms_function_mismatch(self) -> None:
        x = Variable(1, sort=Ind)
        f1 = FunctionApp("f", 1, (x,), Ind)
        g1 = FunctionApp("g", 1, (x,), Ind)
        f2 = FunctionApp("f", 2, (x, x), Ind)

        with self.assertRaises(UnificationError):
            unify_terms(f1, g1)

        with self.assertRaises(UnificationError):
            unify_terms(f1, f2)

    def test_unify_terms_function_return_sort_mismatch(self) -> None:
        x = Variable(1, sort=Ind)
        f_nat = FunctionApp("f", 1, (x,), Nat)
        f_bool = FunctionApp("f", 1, (x,), Bool)

        with self.assertRaises(SortMismatchError):
            unify_terms(f_nat, f_bool)

    def test_unify_terms_transitive_substitution(self) -> None:
        x = Variable(1, sort=Ind)
        y = Variable(2, sort=Ind)
        c = Constant("c", sort=Ind)

        # Unify f(x, y) with f(y, c) -> x = y, y = c -> x = c, y = c
        t1 = FunctionApp("f", 2, (x, y), Ind)
        t2 = FunctionApp("f", 2, (y, c), Ind)

        subst = unify_terms(t1, t2)
        self.assertEqual(subst[y], c)
        self.assertEqual(subst[x], c)

    def test_unify_terms_incompatible_structures(self) -> None:
        c = Constant("c", sort=Ind)
        x = Variable(1, sort=Ind)
        f = FunctionApp("f", 1, (x,), Ind)

        with self.assertRaises(UnificationError):
            unify_terms(c, f)

    # -------------------------------------------------------------------------
    # 4. Formula Unification Tests
    # -------------------------------------------------------------------------

    def test_unify_formulas_predicate_app(self) -> None:
        x = Variable(1, sort=Ind)
        y = Variable(2, sort=Ind)
        a = Constant("a", sort=Ind)
        b = Constant("b", sort=Ind)

        f1 = PredicateApp("P", 2, (x, b))
        f2 = PredicateApp("P", 2, (a, y))

        subst = unify_formulas(f1, f2)
        self.assertEqual(subst, {x: a, y: b})

    def test_unify_formulas_equality(self) -> None:
        x = Variable(1, sort=Ind)
        y = Variable(2, sort=Ind)
        a = Constant("a", sort=Ind)
        b = Constant("b", sort=Ind)

        eq1 = Equality(x, b)
        eq2 = Equality(a, y)

        subst = unify_formulas(eq1, eq2)
        self.assertEqual(subst, {x: a, y: b})

    def test_unify_formulas_predicate_mismatch(self) -> None:
        x = Variable(1, sort=Ind)
        f1 = PredicateApp("P", 1, (x,))
        f2 = PredicateApp("Q", 1, (x,))

        with self.assertRaises(UnificationError):
            unify_formulas(f1, f2)

    def test_unify_formulas_non_atomic_raises(self) -> None:
        x = Variable(1, sort=Ind)
        p = PredicateApp("P", 1, (x,))
        n = Not(p)
        a = And(p, p)
        fa = Forall(x, p)

        with self.assertRaises(UnificationError):
            unify_formulas(n, n)

        with self.assertRaises(UnificationError):
            unify_formulas(a, a)

        with self.assertRaises(UnificationError):
            unify_formulas(fa, fa)

        with self.assertRaises(UnificationError):
            unify_formulas(p, Equality(x, x))

    # -------------------------------------------------------------------------
    # 5. Property-based Invariant Verification
    # -------------------------------------------------------------------------

    def _verify_composition_invariant(
        self, var_id1: int, var_id2: int, const_name: str
    ) -> None:
        """Verifies substitution composition associativity/invariant for given IDs and constant.

        Args:
            var_id1 (int): First variable integer identifier.
            var_id2 (int): Second variable integer identifier.
            const_name (str): Constant name string.

        Returns:
            None

        Example:
            >>> # Verifies apply(compose(s1, s2), x) == apply(s1, apply(s2, x))
        """
        x = Variable(var_id1, sort=Ind)
        y = Variable(var_id2, sort=Ind)
        c = Constant(const_name, sort=Ind)

        s2 = {x: y}
        s1 = {y: c}

        composed = compose_substitutions(s1, s2)

        # apply(compose(s1, s2), x) == apply(s1, apply(s2, x))
        left = apply_substitution(composed, x)
        right = apply_substitution(s1, apply_substitution(s2, x))
        self.assertEqual(left, right)

    def _verify_unification_idempotency_and_commutativity(
        self, var_id: int, const_name: str
    ) -> None:
        """Verifies unification commutativity and idempotent application for given ID and constant.

        Args:
            var_id (int): Variable integer identifier.
            const_name (str): Constant name string.

        Returns:
            None

        Example:
            >>> # Verifies unify_terms(x, c) == unify_terms(c, x) and apply(subst, x) == apply(subst, c)
        """
        x = Variable(var_id, sort=Ind)
        c = Constant(const_name, sort=Ind)

        subst1 = unify_terms(x, c)
        subst2 = unify_terms(c, x)

        self.assertEqual(subst1, subst2)
        self.assertEqual(apply_substitution(subst1, x), apply_substitution(subst1, c))

    def test_property_composition_invariant(self) -> None:
        """Verifies substitution composition associativity across boundary cases and pseudo-random inputs.

        Args:
            None

        Returns:
            None

        Example:
            >>> test_inst = TestSubstitutions()
            >>> test_inst.test_property_composition_invariant()
        """
        # 1. Deterministic boundary cases
        boundary_cases = [
            (0, 1, "c"),
            (0, 100, "const_val"),
            (42, 43, "a"),
            (999, 1000, "z"),
        ]
        for v1, v2, c_name in boundary_cases:
            self._verify_composition_invariant(v1, v2, c_name)

        # 2. Pseudo-random property verification with fixed seed
        rng = random.Random(42)
        for _ in range(100):
            v1 = rng.randint(0, 500)
            v2 = rng.randint(501, 1000)
            length = rng.randint(1, 12)
            c_name = "".join(rng.choice(string.ascii_lowercase) for _ in range(length))
            self._verify_composition_invariant(v1, v2, c_name)

    def test_property_unification_idempotency_and_commutativity(self) -> None:
        """Verifies unification commutativity and idempotent application across boundary and pseudo-random inputs.

        Args:
            None

        Returns:
            None

        Example:
            >>> test_inst = TestSubstitutions()
            >>> test_inst.test_property_unification_idempotency_and_commutativity()
        """
        # 1. Deterministic boundary cases
        boundary_cases = [
            (0, "c"),
            (42, "alpha"),
            (100, "const"),
            (9999, "omega"),
        ]
        for v, c_name in boundary_cases:
            self._verify_unification_idempotency_and_commutativity(v, c_name)

        # 2. Pseudo-random property verification with fixed seed
        rng = random.Random(42)
        for _ in range(100):
            v = rng.randint(0, 1000)
            length = rng.randint(1, 12)
            c_name = "".join(rng.choice(string.ascii_lowercase) for _ in range(length))
            self._verify_unification_idempotency_and_commutativity(v, c_name)


if __name__ == "__main__":
    unittest.main()
