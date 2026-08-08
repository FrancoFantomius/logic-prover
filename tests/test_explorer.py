from __future__ import annotations
import os
import tempfile
import unittest

from logic.config import SolverConfig
from logic.core.ast import (
    Variable, Constant, FunctionApp, PredicateApp, Equality,
    Not, And, Or, Implies, Iff, Forall, Exists
)
from logic.core.sorts import Ind, Nat
from logic.core.signature import Signature
from logic.core.validator import validate_formula, is_well_formed
from logic.core.database import KnowledgeDatabase
from logic.kb import get_all_axioms, get_combined_signature
from logic.explorer import (
    DiversityMetrics,
    calculate_symbol_entropy,
    calculate_diversity_scores,
    composite_interestingness,
    is_redundant_structure,
    FormulaFilter,
    FormulaExplorer,
    anti_unify_terms,
    anti_unify_formulas
)
from logic.__main__ import main


class TestExplorerHeuristics(unittest.TestCase):

    def setUp(self):
        self.x = Variable(id=0, sort=Ind)
        self.y = Variable(id=1, sort=Ind)
        self.px = PredicateApp(pred="P", arity=1, args=(self.x,))
        self.py = PredicateApp(pred="P", arity=1, args=(self.y,))
        self.qy = PredicateApp(pred="Q", arity=1, args=(self.y,))
        self.rxy = PredicateApp(pred="R", arity=2, args=(self.x, self.y))

    def test_symbol_entropy(self):
        # Repetitive formula P(x) & P(x)
        repetitive = And(left=self.px, right=self.px)
        # Rich formula (P(x) & Q(y)) => R(x, y)
        rich = Implies(left=And(left=self.px, right=self.qy), right=self.rxy)

        entropy_rep = calculate_symbol_entropy(repetitive)
        entropy_rich = calculate_symbol_entropy(rich)

        self.assertLess(entropy_rep, entropy_rich)

    def test_is_redundant_structure(self):
        # Self-equality: x = x
        self_eq = Equality(left=self.x, right=self.x)
        self.assertTrue(is_redundant_structure(self_eq))

        # Self-implication: P(x) => P(x)
        self_imp = Implies(left=self.px, right=self.px)
        self.assertTrue(is_redundant_structure(self_imp))

        # Self-conjunction: P(x) & P(x)
        self_conj = And(left=self.px, right=self.px)
        self.assertTrue(is_redundant_structure(self_conj))

        # Contradiction: P(x) & ~P(x)
        contradiction = And(left=self.px, right=Not(operand=self.px))
        self.assertTrue(is_redundant_structure(contradiction))

        # Double negation: ~~P(x)
        double_neg = Not(operand=Not(operand=self.px))
        self.assertTrue(is_redundant_structure(double_neg))

        # Vacuous quantification: forall x, P(y) (where x is not free in P(y))
        vacuous = Forall(variable=self.x, body=self.qy)
        self.assertTrue(is_redundant_structure(vacuous))

        # Non-redundant formula: P(x) => Q(y)
        valid_formula = Implies(left=self.px, right=self.qy)
        self.assertFalse(is_redundant_structure(valid_formula))

    def test_diversity_scores_and_interestingness(self):
        formula = Forall(variable=self.x, body=Implies(left=self.px, right=self.qy))
        metrics = calculate_diversity_scores(formula)
        self.assertIsInstance(metrics, DiversityMetrics)
        self.assertGreater(metrics.ast_size, 0)
        self.assertGreater(metrics.symbol_entropy, 0.0)

        score = composite_interestingness(metrics)
        self.assertIsInstance(score, float)
        d_dict = metrics.to_dict()
        self.assertIn("symbol_entropy", d_dict)


class TestFormulaFilter(unittest.TestCase):

    def setUp(self):
        self.x = Variable(id=0, sort=Ind)
        self.y = Variable(id=1, sort=Ind)
        self.px = PredicateApp(pred="P", arity=1, args=(self.x,))
        self.py = PredicateApp(pred="P", arity=1, args=(self.y,))

    def test_filter_add_and_alpha_equivalence(self):
        filter_inst = FormulaFilter()
        f1 = Forall(variable=self.x, body=self.px)
        f2 = Forall(variable=self.y, body=self.py)

        self.assertFalse(filter_inst.is_seen(f1))
        filter_inst.add(f1)
        self.assertTrue(filter_inst.is_seen(f1))
        # Alpha-equivalent formula f2 must also be seen
        self.assertTrue(filter_inst.is_seen(f2))
        self.assertEqual(len(filter_inst), 1)

    def test_filter_persistence(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "filter.json")
            f1 = Forall(variable=self.x, body=self.px)

            filter1 = FormulaFilter(storage_path=path)
            filter1.add(f1)
            filter1.save_state()

            self.assertTrue(os.path.exists(path))

            filter2 = FormulaFilter(storage_path=path)
            self.assertTrue(filter2.is_seen(f1))
            self.assertEqual(len(filter2), 1)


class TestAntiUnification(unittest.TestCase):

    def setUp(self):
        self.x = Variable(id=0, sort=Ind)
        self.y = Variable(id=1, sort=Ind)
        self.a = Constant("a", sort=Ind)
        self.b = Constant("b", sort=Ind)

    def test_anti_unify_terms_identical(self):
        bindings = {}
        counter = [10]
        res = anti_unify_terms(self.a, self.a, bindings, counter)
        self.assertEqual(res, self.a)

    def test_anti_unify_terms_matching_func(self):
        f_a = FunctionApp("f", 1, (self.a,), return_sort=Ind)
        f_b = FunctionApp("f", 1, (self.b,), return_sort=Ind)
        bindings = {}
        counter = [10]
        res = anti_unify_terms(f_a, f_b, bindings, counter)
        self.assertIsInstance(res, FunctionApp)
        self.assertEqual(res.func, "f")
        self.assertIsInstance(res.args[0], Variable)

    def test_anti_unify_formulas(self):
        p_a = PredicateApp("P", 1, (self.a,))
        p_b = PredicateApp("P", 1, (self.b,))
        gen = anti_unify_formulas(p_a, p_b)
        self.assertIsNotNone(gen)
        # Should result in forall v, P(v)
        self.assertIsInstance(gen, Forall)
        self.assertIsInstance(gen.body, PredicateApp)
        self.assertEqual(gen.body.pred, "P")


class TestFormulaExplorer(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_explorer.db")
        self.db = KnowledgeDatabase(self.db_path)
        self.signature = get_combined_signature()
        
        # Populate DB with axioms
        axioms = get_all_axioms()
        for name, formula, category in axioms:
            self.db.add_axiom(name, formula, category)

        self.config = SolverConfig(db_path=self.db_path)
        self.explorer = FormulaExplorer(
            db=self.db,
            signature=self.signature,
            config=self.config
        )

    def tearDown(self):
        self.db.close()
        self.tmp_dir.cleanup()

    def test_generate_candidates_strategies(self):
        strategies = ["axiom_rewrite", "anti_unification", "saturation", "lemma_combination", "mixed"]
        for strat in strategies:
            candidates = self.explorer.generate_candidates(strategy=strat, max_depth=5, count=10)
            self.assertIsInstance(candidates, list)
            for f in candidates:
                # Ensure all generated candidates are valid according to signature
                self.assertTrue(is_well_formed(f, self.signature), f"Candidate {f} failed signature validation")
                self.assertFalse(is_redundant_structure(f), f"Candidate {f} is redundant")

    def test_rank_and_select_deduplication(self):
        candidates = self.explorer.generate_candidates(strategy="mixed", max_depth=5, count=20)
        selected = self.explorer.rank_and_select(candidates, top_k=5)
        self.assertLessEqual(len(selected), 5)

        # Calling rank_and_select again on the previously selected candidates should yield 0 unseen candidates
        selected_again = self.explorer.rank_and_select(selected, top_k=5)
        self.assertEqual(len(selected_again), 0)

    def test_cli_explore_command(self):
        filter_file = os.path.join(self.tmp_dir.name, "filter.json")
        try:
            main([
                "explore",
                "--strategy", "mixed",
                "--depth", "4",
                "--count", "15",
                "--top-k", "3",
                "--db-path", self.db_path,
                "--filter-file", filter_file
            ])
            self.assertTrue(os.path.exists(filter_file))
        except SystemExit as e:
            self.assertEqual(e.code, 0)


if __name__ == "__main__":
    unittest.main()
