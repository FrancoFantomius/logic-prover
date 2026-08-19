"""Unit and integration tests for Intuitionistic First-Order Logic with Equality (iFOL=)."""

from __future__ import annotations
import unittest

from logic_prover.core.ast import (
    Variable, Constant, FunctionApp, PredicateApp, Equality,
    Not, And, Or, Implies, Iff, Forall, Exists
)
from logic_prover.core.sorts import Ind
from logic_prover.constructive.common import (
    _is_atomic,
    collect_equalities,
    kbo_weight,
    kbo_compare,
    normalize_formula,
    fresh_constant,
    FALSUM,
    VERUM,
)
from logic_prover.constructive.ljt import (
    Sequent,
    LJTProofNode,
    LJTProofTree,
    LJTProver,
    prove_ljt,
)
from logic_prover.constructive.kripke import (
    World,
    KripkeModel,
)
from logic_prover.constructive.tableau import (
    TableauProver,
    prove_tableau,
)
from logic_prover.constructive.resolution import (
    PrefixedLiteral,
    PrefixedClause,
    resolve_prefixed_clauses,
    factor_prefixed_clause,
    _paramodulate_clauses,
    PrefixedResolutionProver,
    prove_prefixed_resolution,
    TranslationResolutionProver,
    prove_translation_resolution,
)


class TestEqualityHelpers(unittest.TestCase):
    """Tests for shared equality helpers: atomicity, collection, KBO comparison."""

    def setUp(self) -> None:
        self.a = Constant("a")
        self.b = Constant("b")
        self.c = Constant("c")
        self.x = Variable(1)
        self.eq_ab = Equality(self.a, self.b)
        self.eq_bc = Equality(self.b, self.c)
        self.fa = FunctionApp("f", 1, (self.a,))
        self.fb = FunctionApp("f", 1, (self.b,))
        self.ffa = FunctionApp("f", 1, (self.fa,))

    def test_is_atomic_equality(self) -> None:
        """Equality AST nodes are treated as atomic formulas in constructive logic."""
        self.assertTrue(_is_atomic(self.eq_ab))
        self.assertFalse(_is_atomic(And(self.eq_ab, self.eq_bc)))
        self.assertFalse(_is_atomic(Implies(self.eq_ab, self.eq_bc)))

    def test_collect_equalities(self) -> None:
        """collect_equalities retrieves equality subformulas with polarity awareness."""
        f = And(self.eq_ab, Not(self.eq_bc))
        all_eqs = collect_equalities(f)
        self.assertEqual(all_eqs, {self.eq_ab, self.eq_bc})

        pos_eqs = collect_equalities(f, sign="T")
        self.assertEqual(pos_eqs, {self.eq_ab})

        neg_eqs = collect_equalities(f, sign="F")
        self.assertEqual(neg_eqs, {self.eq_bc})

    def test_kbo_weight_and_compare(self) -> None:
        """KBO assigns consistent weights and orders heavier terms over lighter terms."""
        self.assertEqual(kbo_weight(self.a), 1)
        self.assertEqual(kbo_weight(self.x), 1)
        self.assertEqual(kbo_weight(self.fa), 2)
        self.assertEqual(kbo_weight(self.ffa), 3)

        self.assertEqual(kbo_compare(self.fa, self.a), "gt")
        self.assertEqual(kbo_compare(self.a, self.fa), "lt")
        self.assertEqual(kbo_compare(self.a, self.a), "eq")
        self.assertEqual(kbo_compare(self.ffa, self.fa), "gt")


class TestLJTEquality(unittest.TestCase):
    """Tests for LJT sequent calculus equality rules (R_Refl, L_Refl, L_Eq_Subst)."""

    def setUp(self) -> None:
        self.prover = LJTProver()
        self.a = Constant("a")
        self.b = Constant("b")
        self.c = Constant("c")
        self.x = Variable(1)
        self.y = Variable(2)
        self.z = Variable(3)

    def test_reflexivity_axiom(self) -> None:
        """t = t is valid by R_Refl."""
        refl = Equality(self.a, self.a)
        proof = self.prover.prove(refl)
        self.assertIsNotNone(proof)
        self.assertTrue(proof.is_valid())
        self.assertIn("R_Refl", proof.to_ascii())

    def test_symmetry(self) -> None:
        """x = y => y = x is provable in LJT."""
        eq_xy = Equality(self.a, self.b)
        eq_yx = Equality(self.b, self.a)
        symm = Implies(eq_xy, eq_yx)
        self.assertTrue(self.prover.is_provable(symm))

    def test_transitivity(self) -> None:
        """(a = b & b = c) => a = c is provable in LJT."""
        eq_ab = Equality(self.a, self.b)
        eq_bc = Equality(self.b, self.c)
        eq_ac = Equality(self.a, self.c)
        trans = Implies(And(eq_ab, eq_bc), eq_ac)
        self.assertTrue(self.prover.is_provable(trans))

    def test_function_congruence(self) -> None:
        """a = b => f(a) = f(b) is provable in LJT."""
        eq_ab = Equality(self.a, self.b)
        fa = FunctionApp("f", 1, (self.a,))
        fb = FunctionApp("f", 1, (self.b,))
        eq_fa_fb = Equality(fa, fb)
        cong = Implies(eq_ab, eq_fa_fb)
        self.assertTrue(self.prover.is_provable(cong))

    def test_predicate_substitution_leibniz(self) -> None:
        """(a = b & P(a)) => P(b) is provable in LJT."""
        eq_ab = Equality(self.a, self.b)
        pa = PredicateApp("P", 1, (self.a,))
        pb = PredicateApp("P", 1, (self.b,))
        leibniz = Implies(And(eq_ab, pa), pb)
        self.assertTrue(self.prover.is_provable(leibniz))

    def test_invalid_equality_formulas(self) -> None:
        """Non-theorems are not provable."""
        # a = b without premises
        self.assertFalse(self.prover.is_provable(Equality(self.a, self.b)))
        # forall x y. x = y
        all_eq = Forall(self.x, Forall(self.y, Equality(self.x, self.y)))
        self.assertFalse(self.prover.is_provable(all_eq))


class TestKripkeEquality(unittest.TestCase):
    """Tests for Kripke semantics with equalities, per-world CC cache, and monotonicity."""

    def setUp(self) -> None:
        self.model = KripkeModel()
        self.w0 = World(0, "w0")
        self.w1 = World(1, "w1")
        self.model.add_world(self.w0)
        self.model.add_world(self.w1)
        self.model.add_relation(self.w0, self.w1)

        self.a = Constant("a")
        self.b = Constant("b")
        self.c = Constant("c")
        self.fa = FunctionApp("f", 1, (self.a,))
        self.fb = FunctionApp("f", 1, (self.b,))

    def test_reflexivity_always_forced(self) -> None:
        """Reflexivity t = t is forced at every world automatically."""
        refl = Equality(self.a, self.a)
        self.assertTrue(self.model.evaluate(refl, self.w0))
        self.assertTrue(self.model.evaluate(refl, self.w1))

    def test_equality_assertion_and_congruence(self) -> None:
        """Asserting a = b at w0 forces b = a, f(a) = f(b), and propagates to w1."""
        eq_ab = Equality(self.a, self.b)
        self.assertFalse(self.model.evaluate(eq_ab, self.w0))

        self.model.add_equality(self.w0, eq_ab)

        # Direct equality & symmetry
        self.assertTrue(self.model.evaluate(eq_ab, self.w0))
        self.assertTrue(self.model.evaluate(Equality(self.b, self.a), self.w0))

        # Congruence closure
        self.assertTrue(self.model.evaluate(Equality(self.fa, self.fb), self.w0))

        # Monotonicity propagation to w1
        self.assertTrue(self.model.evaluate(eq_ab, self.w1))
        self.assertTrue(self.model.evaluate(Equality(self.fa, self.fb), self.w1))

    def test_serialization(self) -> None:
        """KripkeModel includes equalities in to_dict and to_string."""
        self.model.add_equality(self.w0, Equality(self.a, self.b))
        d = self.model.to_dict()
        self.assertIn("equalities", d)
        self.assertIn("w0", d["equalities"])
        self.assertIn("Equalities E(w):", self.model.to_string())


class TestTableauEquality(unittest.TestCase):
    """Tests for Semantic Tableaux with equality store and Kripke countermodel extraction."""

    def setUp(self) -> None:
        self.prover = TableauProver()
        self.a = Constant("a")
        self.b = Constant("b")
        self.c = Constant("c")
        self.fa = FunctionApp("f", 1, (self.a,))
        self.fb = FunctionApp("f", 1, (self.b,))

    def test_reflexivity_clash(self) -> None:
        """Proving t = t closes immediately via reflexivity."""
        res = self.prover.prove(Equality(self.a, self.a))
        self.assertTrue(res.is_valid)

    def test_symmetry_and_transitivity(self) -> None:
        """Symmetry and transitivity are valid in tableau."""
        eq_ab = Equality(self.a, self.b)
        eq_ba = Equality(self.b, self.a)
        self.assertTrue(self.prover.is_valid(Implies(eq_ab, eq_ba)))

        eq_bc = Equality(self.b, self.c)
        eq_ac = Equality(self.a, self.c)
        self.assertTrue(self.prover.is_valid(Implies(And(eq_ab, eq_bc), eq_ac)))

    def test_function_congruence(self) -> None:
        """a = b => f(a) = f(b) is provable in tableau."""
        eq_ab = Equality(self.a, self.b)
        eq_fa_fb = Equality(self.fa, self.fb)
        self.assertTrue(self.prover.is_valid(Implies(eq_ab, eq_fa_fb)))

    def test_countermodel_for_invalid_equality(self) -> None:
        """Invalid equality formula produces an explicit Kripke countermodel."""
        res = self.prover.prove(Equality(self.a, self.b))
        self.assertFalse(res.is_valid)
        self.assertIsNotNone(res.countermodel)
        cm = res.countermodel
        self.assertFalse(cm.evaluate(Equality(self.a, self.b), cm.worlds[0]))


class TestPrefixedResolutionEquality(unittest.TestCase):
    """Tests for Prefixed Resolution and Translation Resolution with equality."""

    def setUp(self) -> None:
        self.a = Constant("a")
        self.b = Constant("b")
        self.c = Constant("c")
        self.fa = FunctionApp("f", 1, (self.a,))
        self.fb = FunctionApp("f", 1, (self.b,))

    def test_prefixed_resolution_refl_and_symm(self) -> None:
        """Prefixed resolution proves reflexivity and symmetry."""
        prover = PrefixedResolutionProver()
        # Reflexivity
        res_refl = prover.prove(Equality(self.a, self.a))
        self.assertIsNotNone(res_refl)
        self.assertTrue(res_refl.is_valid)

        # Symmetry
        symm = Implies(Equality(self.a, self.b), Equality(self.b, self.a))
        res_symm = prover.prove(symm)
        self.assertIsNotNone(res_symm)
        self.assertTrue(res_symm.is_valid)

    def test_translation_resolution_equality(self) -> None:
        """Translation resolution proves equality properties via first-order superposition."""
        prover = TranslationResolutionProver()
        # Reflexivity
        res_refl = prover.prove(Equality(self.a, self.a))
        self.assertIsNotNone(res_refl)
        self.assertTrue(res_refl.is_valid)

        # Symmetry
        symm = Implies(Equality(self.a, self.b), Equality(self.b, self.a))
        res_symm = prover.prove(symm)
        self.assertIsNotNone(res_symm)
        self.assertTrue(res_symm.is_valid)

        # Transitivity
        trans = Implies(And(Equality(self.a, self.b), Equality(self.b, self.c)), Equality(self.a, self.c))
        res_trans = prover.prove(trans)
        self.assertIsNotNone(res_trans)
        self.assertTrue(res_trans.is_valid)


class TestShowcaseGroupTheory(unittest.TestCase):
    """Showcase test: Group equality property op(inv(a), op(a, b)) = b from group axioms."""

    def test_group_cancellation_ljt_and_tableau(self) -> None:
        """Proves op(inv(a), op(a, b)) = b from associativity and left inverse in LJT & Tableau."""
        a = Constant("a")
        b = Constant("b")
        e = Constant("e")

        def op(x, y):
            return FunctionApp("op", 2, (x, y))

        def inv(x):
            return FunctionApp("inv", 1, (x,))

        # Hypotheses:
        # 1. Associativity instance: op(inv(a), op(a, b)) = op(op(inv(a), a), b)
        hyp_assoc = Equality(op(inv(a), op(a, b)), op(op(inv(a), a), b))
        # 2. Left inverse instance: op(inv(a), a) = e
        hyp_inv = Equality(op(inv(a), a), e)
        # 3. Left identity instance: op(e, b) = b
        hyp_ident = Equality(op(e, b), b)

        premises = [hyp_assoc, hyp_inv, hyp_ident]
        goal = Equality(op(inv(a), op(a, b)), b)

        # LJT proof
        ljt_proof = prove_ljt(goal, premises=premises)
        self.assertIsNotNone(ljt_proof)
        self.assertTrue(ljt_proof.is_valid())

        # Tableau proof
        tab_res = prove_tableau(goal, premises=premises)
        self.assertTrue(tab_res.is_valid)


if __name__ == "__main__":
    unittest.main()
