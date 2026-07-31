import unittest
import os
import tempfile

from solver.database import TheoryDatabase


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db_file.close()
        self.db = TheoryDatabase(db_path=self.temp_db_file.name)

    def tearDown(self):
        if os.path.exists(self.temp_db_file.name):
            os.remove(self.temp_db_file.name)

    def test_init_db_creates_tables(self):
        with self.db.connection_scope() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = {row[0] for row in cursor.fetchall()}
            self.assertIn("axioms", tables)
            self.assertIn("theorems", tables)
            self.assertIn("theorem_hypotheses", tables)
            self.assertIn("theorem_steps", tables)
            self.assertIn("dependencies", tables)

    def test_add_and_get_axiom(self):
        self.db.add_axiom("ax_test", "p -> q")
        self.assertEqual(self.db.get_axiom("ax_test"), "p -> q")
        self.assertIsNone(self.db.get_axiom("nonexistent"))

        # Duplicate addition should be ignored without raising exception
        self.db.add_axiom("ax_test", "p -> q")
        self.assertEqual(self.db.get_axiom("ax_test"), "p -> q")

    def test_get_all_axioms(self):
        self.db.add_axiom("ax1", "p -> (q -> p)")
        self.db.add_axiom("ax2", "(p -> (q -> r)) -> ((p -> q) -> (p -> r))")
        axioms = self.db.get_all_axioms()
        self.assertEqual(len(axioms), 2)
        self.assertIn("ax1", axioms)
        self.assertIn("ax2", axioms)

    def test_save_and_get_theorem(self):
        steps = [
            {'step_idx': 0, 'formula_str': 'p -> q', 'justification_type': 'Hypothesis', 'arg1': None, 'arg2': None, 'ref_name': None, 'substitution_json': None},
            {'step_idx': 1, 'formula_str': 'p', 'justification_type': 'Hypothesis', 'arg1': None, 'arg2': None, 'ref_name': None, 'substitution_json': None},
            {'step_idx': 2, 'formula_str': 'q', 'justification_type': 'MP', 'arg1': 1, 'arg2': 0, 'ref_name': None, 'substitution_json': None}
        ]
        self.db.save_theorem(
            name="test_thm",
            thesis_str="q",
            hypotheses=["p -> q", "p"],
            steps=steps,
            is_verified=1
        )
        thm = self.db.get_theorem("test_thm")
        self.assertIsNotNone(thm)
        self.assertEqual(thm['name'], "test_thm")
        self.assertEqual(thm['thesis_str'], "q")
        self.assertEqual(thm['is_verified'], 1)
        self.assertEqual(thm['hypotheses'], ["p -> q", "p"])
        self.assertEqual(len(thm['steps']), 3)

    def test_save_theorem_invalid_mp_index(self):
        steps = [
            {'step_idx': 0, 'formula_str': 'q', 'justification_type': 'MP', 'arg1': 1, 'arg2': 2, 'ref_name': None, 'substitution_json': None}
        ]
        with self.assertRaises(ValueError):
            self.db.save_theorem(
                name="invalid_mp",
                thesis_str="q",
                hypotheses=[],
                steps=steps
            )

    def test_get_dependencies_recursive(self):
        # Save base theorem
        self.db.save_theorem("base_thm", "p -> p", [], [], is_verified=1)
        # Save dependent theorem
        self.db.save_theorem("dep_thm", "p -> p", [], [], dependencies=["base_thm"], is_verified=1)

        deps = self.db.get_dependencies_recursive("dep_thm")
        self.assertEqual(deps, ["base_thm"])


if __name__ == "__main__":
    unittest.main()
