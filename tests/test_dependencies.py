import unittest
import os
import tempfile

from solver.formula import (
    parse_formula, Formula, Var, Not, Implies, And, Or, Iff,
    Forall, Exists, Equals, Pred
)
from solver.database import TheoryDatabase
from solver.dependencies import (
    FIRST_ORDER_AXIOMS,
    SECOND_ORDER_AXIOMS,
    LOGIC_AXIOMS,
    load_first_order_axioms,
    load_second_order_axioms,
    load_all_logic_axioms,
    get_first_order_axioms,
    get_second_order_axioms,
    get_all_logic_axioms,
)
from solver.lean_exporter import formula_to_lean


class TestLogicDependencies(unittest.TestCase):
    def setUp(self):
        self.temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db_file.close()
        self.db = TheoryDatabase(db_path=self.temp_db_file.name)

    def tearDown(self):
        if os.path.exists(self.temp_db_file.name):
            os.remove(self.temp_db_file.name)

    def test_first_order_axioms_dict(self):
        fol_axioms = get_first_order_axioms()
        self.assertIn("fol_k", fol_axioms)
        self.assertIn("fol_ui", fol_axioms)
        self.assertIn("eq_ref", fol_axioms)
        self.assertEqual(len(fol_axioms), len(FIRST_ORDER_AXIOMS))

    def test_second_order_axioms_dict(self):
        sol_axioms = get_second_order_axioms()
        self.assertIn("sol_ui", sol_axioms)
        self.assertIn("sol_comp", sol_axioms)
        self.assertIn("sol_induction", sol_axioms)
        self.assertEqual(len(sol_axioms), len(SECOND_ORDER_AXIOMS))

    def test_load_all_logic_axioms_into_db(self):
        load_all_logic_axioms(self.db)
        db_axioms = self.db.get_all_axioms()
        for name in LOGIC_AXIOMS:
            self.assertIn(name, db_axioms)
            # Verify formula parsing on every axiom string
            parsed = parse_formula(db_axioms[name])
            self.assertIsInstance(parsed, Formula)

    def test_fol_and_sol_parsing_and_lean_conversion(self):
        # Test Quantifier Parsing & Lean conversion
        f1 = parse_formula("forall x, (P(x) -> Q(x))")
        self.assertIsInstance(f1, Forall)
        self.assertEqual(formula_to_lean(f1), "(∀ x, ((P x) → (Q x)))")

        # Test Existential & Equals
        f2 = parse_formula("exists y, (y = x)")
        self.assertIsInstance(f2, Exists)
        self.assertIsInstance(f2.body, Equals)
        self.assertEqual(formula_to_lean(f2), "(∃ y, (y = x))")

        # Test And, Or, Iff
        f3 = parse_formula("(A & B) <-> (B | A)")
        self.assertIsInstance(f3, Iff)
        self.assertIsInstance(f3.left, And)
        self.assertIsInstance(f3.right, Or)

    def test_fol_schema_matching(self):
        # Match fol_ui: (forall x, P(x)) -> P(t)
        schema = parse_formula("(forall x, P(x)) -> P(t)")
        concrete = parse_formula("(forall x, Q(x)) -> Q(a)")
        match = concrete.match_schema(schema)
        self.assertIsNotNone(match)
        self.assertEqual(str(match['P']), "Q")
        self.assertEqual(str(match['t']), "a")


    def test_load_first_order_axioms(self):
        load_first_order_axioms(self.db)
        db_axioms = self.db.get_all_axioms()
        for name in FIRST_ORDER_AXIOMS:
            self.assertIn(name, db_axioms)

    def test_load_second_order_axioms(self):
        load_second_order_axioms(self.db)
        db_axioms = self.db.get_all_axioms()
        for name in SECOND_ORDER_AXIOMS:
            self.assertIn(name, db_axioms)

    def test_all_axioms_parse_and_export_to_lean(self):
        for name, f_str in LOGIC_AXIOMS.items():
            parsed = parse_formula(f_str)
            lean_code = formula_to_lean(parsed)
            self.assertTrue(len(lean_code) > 0)


if __name__ == "__main__":
    unittest.main()
