import unittest
import tempfile
import os

from solver.formula import parse_formula, Var, Implies
from solver.database import TheoryDatabase
from solver.deducer import Deducer, deduce_consequences, Consequence, get_all_subformulas
from solver.verifier import verify_proof_local


class TestDeducer(unittest.TestCase):
    def setUp(self):
        self.temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db_file.close()
        self.db = TheoryDatabase(db_path=self.temp_db_file.name)

    def tearDown(self):
        if os.path.exists(self.temp_db_file.name):
            os.remove(self.temp_db_file.name)

    def test_modus_ponens_deduction(self):
        deducer = Deducer(db=self.db)
        hyps = ["p -> q", "p"]
        consequences = deducer.deduce(hyps, include_hypotheses=False)
        
        formula_strs = [c.formula_str for c in consequences]
        self.assertIn("q", formula_strs)
        
        # Check proof of q
        c_q = next(c for c in consequences if c.formula_str == "q")
        self.assertTrue(c_q.is_verified)
        self.assertEqual(c_q.justification_type, "MP")
        
        # Verify proof locally
        thm = {
            'name': 'test_mp',
            'thesis_str': 'q',
            'hypotheses': hyps,
            'steps': c_q.proof
        }
        ok, msg = verify_proof_local(thm, self.db)
        self.assertTrue(ok, f"Verification failed: {msg}")

    def test_chain_modus_ponens_deduction(self):
        deducer = Deducer(db=self.db)
        hyps = ["p -> q", "q -> r", "p"]
        consequences = deducer.deduce(hyps)
        
        formula_strs = [c.formula_str for c in consequences]
        self.assertIn("q", formula_strs)
        self.assertIn("r", formula_strs)
        
        c_r = next(c for c in consequences if c.formula_str == "r")
        self.assertTrue(c_r.is_verified)

    def test_deduction_with_axioms(self):
        deducer = Deducer(db=self.db, auto_load_axioms=True)
        hyps = ["p"]
        consequences = deducer.deduce(hyps, max_formulas=100)
        
        formula_strs = [c.formula_str for c in consequences]
        # With ax1: A -> (B -> A), substituting A=p yields p -> (p -> p) or p -> (~p -> p)
        # MP with p yields p -> p or ~p -> p
        self.assertTrue(any(f in formula_strs for f in ["(p -> (p -> p))", "(p -> p)", "(~p -> p)", "(p -> (~p -> p))"]))

    def test_deduction_with_previous_lemmas(self):
        # Save a verified theorem into database as a previous lemma
        lemma_steps = [
            {'step_idx': 0, 'formula_str': '(p -> ((p -> p) -> p))', 'justification_type': 'Axiom', 'ref_name': 'ax1', 'substitution_json': {'A': 'p', 'B': '(p -> p)'}},
            {'step_idx': 1, 'formula_str': '((p -> ((p -> p) -> p)) -> ((p -> (p -> p)) -> (p -> p)))', 'justification_type': 'Axiom', 'ref_name': 'ax2', 'substitution_json': {'A': 'p', 'B': '(p -> p)', 'C': 'p'}},
            {'step_idx': 2, 'formula_str': '((p -> (p -> p)) -> (p -> p))', 'justification_type': 'MP', 'arg1': 0, 'arg2': 1},
            {'step_idx': 3, 'formula_str': '(p -> (p -> p))', 'justification_type': 'Axiom', 'ref_name': 'ax1', 'substitution_json': {'A': 'p', 'B': 'p'}},
            {'step_idx': 4, 'formula_str': '(p -> p)', 'justification_type': 'MP', 'arg1': 3, 'arg2': 2}
        ]
        self.db.save_theorem(
            name='identity_lemma',
            thesis_str='(p -> p)',
            hypotheses=[],
            steps=lemma_steps,
            is_verified=1
        )
        
        deducer = Deducer(db=self.db)
        consequences = deducer.deduce(["a"])
        formula_strs = [c.formula_str for c in consequences]
        # Should be able to instantiate lemma for '(a -> a)'
        self.assertIn("(a -> a)", formula_strs)

    def test_deduce_consequences_helper_function(self):
        results = deduce_consequences(["A -> B", "A"], db=self.db)
        self.assertTrue(any(c.formula_str == "B" for c in results))

    def test_include_hypotheses_flag(self):
        deducer = Deducer(db=self.db)
        hyps = ["p -> q", "p"]
        consequences_excl = deducer.deduce(hyps, include_hypotheses=False)
        consequences_incl = deducer.deduce(hyps, include_hypotheses=True)
        
        self.assertNotIn("p", [c.formula_str for c in consequences_excl])
        self.assertIn("p", [c.formula_str for c in consequences_incl])

    def test_get_all_subformulas(self):
        f = parse_formula("forall x, (P(x) -> Q(x))")
        subs = get_all_subformulas(f)
        sub_strs = {str(s) for s in subs}
        self.assertIn("(forall x, (P(x) -> Q(x)))", sub_strs)
        self.assertIn("(P(x) -> Q(x))", sub_strs)
        self.assertIn("P(x)", sub_strs)
        self.assertIn("Q(x)", sub_strs)


if __name__ == "__main__":
    unittest.main()
