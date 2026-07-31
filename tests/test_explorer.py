import unittest
import os
import tempfile

from solver.database import TheoryDatabase
from solver.explorer import generate_candidates, explore_consequences
from solver.formula import Var, Not, Implies


class TestExplorer(unittest.TestCase):
    def setUp(self):
        self.temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db_file.close()
        self.db = TheoryDatabase(db_path=self.temp_db_file.name)

    def tearDown(self):
        if os.path.exists(self.temp_db_file.name):
            os.remove(self.temp_db_file.name)

    def test_generate_candidates(self):
        candidates = generate_candidates(basic_vars=['p'], max_depth=1)
        self.assertTrue(len(candidates) > 0)
        var_p = Var('p')
        self.assertIn(var_p, candidates)
        self.assertIn(Not(var_p), candidates)
        self.assertIn(Implies(var_p, var_p), candidates)

    def test_explore_consequences_runs(self):
        # Add basic propositional axioms to db
        self.db.add_axiom("ax1", "p -> (q -> p)")
        count = explore_consequences(self.db, basic_vars=['p'], max_depth=1, max_theorems=5)
        self.assertIsInstance(count, int)
        self.assertGreaterEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
