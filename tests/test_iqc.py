"""Unit and integration tests for Intuitionistic First-Order Logic (IQC / iFOL)."""

from __future__ import annotations
import unittest

from logic_prover.core.ast import (
    Variable, Constant, FunctionApp, PredicateApp, Equality,
    Not, And, Or, Implies, Iff, Forall, Exists
)
from logic_prover.core.sorts import Ind
from logic_prover.constructive.common import (
    _is_atomic,
    normalize_formula,
    _formula_weight,
    fresh_variable,
    fresh_constant,
    ground_terms,
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
    translate_ipc_to_fol,
    get_frame_axioms,
    _extract_predicate_declarations,
    TranslationResolutionProver,
)
from logic_prover.__main__ import main


class TestCommonQuantifierFixes(unittest.TestCase):
    """Tests for shared AST utility updates supporting quantifiers."""

    def setUp(self) -> None:
        self.x = Variable(id=1, sort=Ind)
        self.px = PredicateApp(pred="P", arity=1, args=(self.x,))
        self.forall_px = Forall(variable=self.x, body=self.px)
        self.exists_px = Exists(variable=self.x, body=self.px)

    def test_is_atomic_with_quantifiers(self) -> None:
        """Verifies that quantifiers are recognized as compound formulas, not atoms."""
        self.assertFalse(_is_atomic(self.forall_px))
        self.assertFalse(_is_atomic(self.exists_px))
        self.assertTrue(_is_atomic(self.px))
        self.assertTrue(_is_atomic(FALSUM))
        self.assertTrue(_is_atomic(VERUM))

    def test_normalize_formula_quantifiers(self) -> None:
        """Verifies normalization descends into quantifier bodies."""
        f = Forall(variable=self.x, body=Not(operand=self.px))
        norm = normalize_formula(f)
        self.assertIsInstance(norm, Forall)
        self.assertIsInstance(norm.body, Implies)
        self.assertEqual(norm.body.right, FALSUM)

        e = Exists(variable=self.x, body=Iff(left=self.px, right=self.px))
        norm_e = normalize_formula(e)
        self.assertIsInstance(norm_e, Exists)
        self.assertIsInstance(norm_e.body, And)

    def test_formula_weight_quantifiers(self) -> None:
        """Verifies formula weight calculation for quantifiers."""
        w_atom = _formula_weight(self.px)
        self.assertEqual(w_atom, 1)
        w_forall = _formula_weight(self.forall_px)
        self.assertEqual(w_forall, 2)
        w_exists = _formula_weight(self.exists_px)
        self.assertEqual(w_exists, 2)

    def test_fresh_variable_and_constant(self) -> None:
        """Verifies generation of distinct fresh variables and constants."""
        v1 = fresh_variable([Variable(1), Variable(2)])
        self.assertEqual(v1.id, 3)

        c1 = fresh_constant(prefix="c", existing_constants=[Constant("c0")])
        self.assertNotEqual(c1.name, "c0")

    def test_ground_terms_generation(self) -> None:
        """Verifies recursive ground term generation up to max_depth."""
        c = Constant("c0")
        terms_d0 = ground_terms([c], functions=[("f", 1)], max_depth=0)
        self.assertEqual(terms_d0, [c])

        terms_d1 = ground_terms([c], functions=[("f", 1)], max_depth=1)
        self.assertEqual(len(terms_d1), 2)
        self.assertIn(FunctionApp("f", 1, (c,)), terms_d1)


class TestLJTQuantifiers(unittest.TestCase):
    """Tests for LJT / G4ip sequent calculus with first-order quantifiers."""

    def setUp(self) -> None:
        self.x = Variable(id=1, sort=Ind)
        self.y = Variable(id=2, sort=Ind)
        self.px = PredicateApp(pred="P", arity=1, args=(self.x,))
        self.qx = PredicateApp(pred="Q", arity=1, args=(self.x,))
        self.rxy = PredicateApp(pred="R", arity=2, args=(self.x, self.y))
        self.p_atom = PredicateApp(pred="P0", arity=0, args=())
        self.prover = LJTProver()

    def test_universal_distribution_implication(self) -> None:
        """Tests IQC theorem: (forall x. (P(x) => Q(x))) => ((forall x. P(x)) => (forall x. Q(x)))."""
        premise = Forall(variable=self.x, body=Implies(left=self.px, right=self.qx))
        antecedent = Forall(variable=self.x, body=self.px)
        consequent = Forall(variable=self.x, body=self.qx)
        target = Implies(left=premise, right=Implies(left=antecedent, right=consequent))

        proof = self.prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid())

    def test_existential_conjunction_distribution(self) -> None:
        """Tests IQC theorem: (exists x. (P(x) | Q(x))) => ((exists x. P(x)) | (exists x. Q(x)))."""
        target = Implies(
            left=Exists(variable=self.x, body=Or(left=self.px, right=self.qx)),
            right=Or(
                left=Exists(variable=self.x, body=self.px),
                right=Exists(variable=self.x, body=self.qx),
            ),
        )
        proof = self.prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid())

    def test_quantifier_swap_exists_forall(self) -> None:
        """Tests IQC theorem: (exists x. forall y. R(x, y)) => (forall y. exists x. R(x, y))."""
        premise = Exists(variable=self.x, body=Forall(variable=self.y, body=self.rxy))
        consequent = Forall(variable=self.y, body=Exists(variable=self.x, body=self.rxy))
        target = Implies(left=premise, right=consequent)

        proof = self.prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid())

    def test_forall_and_distributivity(self) -> None:
        """Tests IQC theorem: (forall x. (P0 & Q(x))) => (P0 & (forall x. Q(x)))."""
        left = Forall(variable=self.x, body=And(left=self.p_atom, right=self.qx))
        right = And(left=self.p_atom, right=Forall(variable=self.x, body=self.qx))
        target = Implies(left=left, right=right)

        proof = self.prover.prove(target=target)
        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertTrue(proof.is_valid())

    def test_first_order_excluded_middle_unprovable(self) -> None:
        """Tests that first-order excluded middle forall x. (P(x) | ~P(x)) is unprovable in IQC."""
        target = Forall(variable=self.x, body=Or(left=self.px, right=Not(operand=self.px)))
        proof = self.prover.prove(target=target)
        self.assertIsNone(proof)

    def test_drinker_paradox_unprovable(self) -> None:
        """Tests that the classical Drinker's paradox exists x. (P(x) => forall y. P(y)) is unprovable in IQC."""
        target = Exists(
            variable=self.x,
            body=Implies(left=self.px, right=Forall(variable=self.y, body=PredicateApp("P", 1, (self.y,))))
        )
        proof = self.prover.prove(target=target)
        self.assertIsNone(proof)


class TestKripkeFOL(unittest.TestCase):
    """Tests for First-Order Kripke Semantics with expanding domains."""

    def setUp(self) -> None:
        self.w0 = World(0, "w0")
        self.w1 = World(1, "w1")
        self.c0 = Constant("c0")
        self.c1 = Constant("c1")
        self.x = Variable(1)
        self.px = PredicateApp("P", 1, (self.x,))
        self.pc0 = PredicateApp("P", 1, (self.c0,))
        self.pc1 = PredicateApp("P", 1, (self.c1,))

    def test_expanding_domain_and_quantifier_evaluation(self) -> None:
        """Tests forcing conditions for Forall and Exists under expanding domains."""
        model = KripkeModel()
        model.add_world(self.w0)
        model.add_world(self.w1)
        model.add_relation(self.w0, self.w1)

        model.add_domain_element(self.w0, self.c0)
        model.add_domain_element(self.w1, self.c1)

        # In w0: P(c0) is true, but not P(c1). In w1: P(c0) and P(c1) are true.
        model.add_valuation(self.w0, self.pc0)
        model.add_valuation(self.w1, self.pc1)

        # Forall x. P(x) is true at w0 because at w0 (D={c0}) P(c0) holds, and at w1 (D={c0,c1}) both hold.
        self.assertTrue(model.evaluate(Forall(self.x, self.px), self.w0))
        self.assertTrue(model.evaluate(Forall(self.x, self.px), self.w1))

        # Exists x. P(x) holds at w0
        self.assertTrue(model.evaluate(Exists(self.x, self.px), self.w0))

    def test_kripke_model_serialization(self) -> None:
        """Tests KripkeModel to_dict and to_string serialization with domains."""
        model = KripkeModel()
        model.add_world(self.w0)
        model.add_domain_element(self.w0, self.c0)
        model.add_valuation(self.w0, self.pc0)

        d = model.to_dict()
        self.assertIn("domains", d)
        self.assertIn("w0", d["domains"])
        self.assertIn("c0", d["domains"]["w0"])

        s = model.to_string()
        self.assertIn("Domains D(w)", s)


class TestTableauQuantifiers(unittest.TestCase):
    """Tests for Semantic Tableau with first-order quantifier rules and countermodels."""

    def setUp(self) -> None:
        self.x = Variable(1)
        self.px = PredicateApp("P", 1, (self.x,))
        self.qx = PredicateApp("Q", 1, (self.x,))
        self.prover = TableauProver()

    def test_tableau_proves_valid_quantified_formula(self) -> None:
        """Tests that Tableau successfully proves universal distribution over implication."""
        target = Implies(
            left=Forall(self.x, Implies(self.px, self.qx)),
            right=Implies(Forall(self.x, self.px), Forall(self.x, self.qx)),
        )
        res = self.prover.prove(target=target)
        self.assertTrue(res.is_valid)

    def test_tableau_countermodel_for_first_order_lem(self) -> None:
        """Tests countermodel extraction for unprovable first-order excluded middle."""
        target = Forall(self.x, Or(self.px, Not(self.px)))
        res = self.prover.prove(target=target)
        self.assertFalse(res.is_valid)
        self.assertIsNotNone(res.countermodel)
        assert res.countermodel is not None
        self.assertGreaterEqual(len(res.countermodel.worlds), 1)


class TestTranslationQuantifiers(unittest.TestCase):
    """Tests for Relational Translation of First-Order Logic to Classical FOL."""

    def setUp(self) -> None:
        self.x = Variable(1)
        self.px = PredicateApp("P", 1, (self.x,))
        self.qx = PredicateApp("Q", 1, (self.x,))

    def test_translation_quantifier_syntax(self) -> None:
        """Tests the AST structure produced by translate_ipc_to_fol on quantifiers."""
        f_forall = Forall(self.x, self.px)
        fol_f = translate_ipc_to_fol(f_forall)
        self.assertIsInstance(fol_f, Forall)

        f_exists = Exists(self.x, self.px)
        fol_e = translate_ipc_to_fol(f_exists)
        self.assertIsInstance(fol_e, Exists)

    def test_frame_axioms_multi_arity(self) -> None:
        """Tests generation of monotonicity axioms for n-ary predicates."""
        axioms = get_frame_axioms([("P", 1), ("R_pred", 2)])
        self.assertGreaterEqual(len(axioms), 4)

    def test_translation_prover_quantified_implication(self) -> None:
        """Tests TranslationResolutionProver on quantified distribution."""
        prover = TranslationResolutionProver(max_steps=500)
        target = Implies(
            left=Forall(self.x, Implies(self.px, self.qx)),
            right=Implies(Forall(self.x, self.px), Forall(self.x, self.qx)),
        )
        res = prover.prove(target=target)
        self.assertIsNotNone(res)
        assert res is not None
        self.assertTrue(res.is_valid)


class TestCLIIntuitionistic(unittest.TestCase):
    """Tests for the prove-intuitionistic CLI subcommand."""

    def test_cli_prove_intuitionistic_ljt(self) -> None:
        """Tests CLI invocation of prove-intuitionistic with LJT engine."""
        code = main(["prove-intuitionistic", "P => P", "--method", "ljt"])
        self.assertEqual(code, 0)

    def test_cli_prove_intuitionistic_tableau(self) -> None:
        """Tests CLI invocation of prove-intuitionistic with Tableau engine."""
        code = main(["prove-intuitionistic", "P => P", "--method", "tableau"])
        self.assertEqual(code, 0)

    def test_cli_prove_intuitionistic_invalid(self) -> None:
        """Tests CLI invocation on unprovable formula."""
        code = main(["prove-intuitionistic", "P | ~P", "--method", "tableau"])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
