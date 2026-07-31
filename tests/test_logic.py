import unittest
import os
import tempfile

from solver.formula import parse_formula, Formula
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


class TestLogic(unittest.TestCase):
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

    def test_all_logic_axioms_dict(self):
        logic_axioms = get_all_logic_axioms()
        self.assertEqual(len(logic_axioms), len(LOGIC_AXIOMS))

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

    def test_load_all_logic_axioms_into_db(self):
        load_all_logic_axioms(self.db)
        db_axioms = self.db.get_all_axioms()
        for name in LOGIC_AXIOMS:
            self.assertIn(name, db_axioms)
            parsed = parse_formula(db_axioms[name])
            self.assertIsInstance(parsed, Formula)

    def test_all_axioms_parse_and_export_to_lean(self):
        for name, f_str in LOGIC_AXIOMS.items():
            parsed = parse_formula(f_str)
            lean_code = formula_to_lean(parsed)
            self.assertTrue(len(lean_code) > 0)


if __name__ == "__main__":
    unittest.main()
