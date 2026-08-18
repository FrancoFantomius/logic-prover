from __future__ import annotations
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from logic_prover.config import SolverConfig
from logic_prover.core.ast import (
    Formula, Variable, Constant, PredicateApp, Equality, Not, And, Or, Implies, Iff, Forall, Exists
)
from logic_prover.core.sorts import Ind, Nat
from logic_prover.core.exceptions import DatabaseError, SolverError
from logic_prover.core.validator import is_well_formed
from logic_prover.core.database import KnowledgeDatabase
from logic_prover.axioms import get_all_axioms, get_combined_signature
from logic_prover.__main__ import main


class TestSolverConfig(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_config_defaults(self) -> None:
        config = SolverConfig()
        self.assertEqual(config.db_path, "logic_data.db")
        self.assertEqual(config.explorer_max_depth, 4)
        self.assertEqual(config.prover_timeout_sec, 10.0)

    def test_config_json_roundtrip(self) -> None:
        json_file = self.temp_path / "config.json"
        config = SolverConfig(db_path="custom.db", explorer_max_depth=10)
        config.save(json_file)

        loaded = SolverConfig.from_file(json_file)
        self.assertEqual(loaded.db_path, "custom.db")
        self.assertEqual(loaded.explorer_max_depth, 10)

    def test_config_unknown_keys_filtering(self) -> None:
        json_file = self.temp_path / "extra_config.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump({"db_path": "filtered.db", "unknown_setting": 12345}, f)

        loaded = SolverConfig.from_file(json_file)
        self.assertEqual(loaded.db_path, "filtered.db")
        self.assertFalse(hasattr(loaded, "unknown_setting"))

    def test_config_missing_file(self) -> None:
        missing_file = self.temp_path / "nonexistent.json"
        with self.assertRaises(FileNotFoundError):
            SolverConfig.from_file(missing_file)


class TestKBAxioms(unittest.TestCase):

    def test_all_axioms_well_formed(self) -> None:
        sig = get_combined_signature()
        axioms = get_all_axioms()
        self.assertGreater(len(axioms), 0)

        for name, formula, category in axioms:
            self.assertTrue(
                is_well_formed(formula, sig),
                f"Axiom '{name}' in category '{category}' failed signature validation."
            )


class TestKnowledgeDatabase(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_logic.db"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_database_creation(self) -> None:
        db = KnowledgeDatabase(self.db_path)
        self.assertTrue(self.db_path.exists())

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        expected_tables = {"formulas", "axioms", "theorems", "proofs", "metadata"}
        self.assertTrue(expected_tables.issubset(tables))
        db.close()

    def test_add_and_get_axioms(self) -> None:
        db = KnowledgeDatabase(self.db_path)
        all_axioms = get_all_axioms()

        for name, formula, category in all_axioms:
            db.add_axiom(name, formula, category)

        eq_axioms = db.get_axioms("equality")
        logic_axioms = db.get_axioms("logic")
        peano_axioms = db.get_axioms("peano")

        self.assertGreater(len(eq_axioms), 0)
        self.assertGreater(len(logic_axioms), 0)
        self.assertGreater(len(peano_axioms), 0)

        total_retrieved = len(db.get_axioms())
        self.assertEqual(total_retrieved, len(all_axioms))
        db.close()

    def test_persistence_across_restarts(self) -> None:
        db1 = KnowledgeDatabase(self.db_path)
        x = Variable(0, sort=Ind)
        formula = Forall(x, Equality(x, x))
        proof_data = {"root": "step1", "steps": []}

        db1.add_axiom("eq_refl", formula, "equality")
        db1.add_theorem("thm_refl", formula, proof=proof_data, category="equality")
        db1.close()

        # Re-open database from same file path
        db2 = KnowledgeDatabase(self.db_path)
        axioms = db2.get_axioms()
        theorems = db2.get_theorems()
        retrieved_proof = db2.get_proof("thm_refl")

        self.assertEqual(len(axioms), 1)
        self.assertEqual(axioms[0][0], "eq_refl")
        self.assertEqual(len(theorems), 1)
        self.assertEqual(theorems[0][0], "thm_refl")
        self.assertEqual(retrieved_proof, proof_data)
        db2.close()

    def test_contains_formula_alpha_equivalence(self) -> None:
        db = KnowledgeDatabase(self.db_path)
        x = Variable(0, sort=Ind)
        f1 = Forall(x, PredicateApp("P", 1, (x,)))
        db.add_axiom("forall_p_x", f1, "logic")

        # Alpha-equivalent formula using variable ID 99
        y = Variable(99, sort=Ind)
        f2 = Forall(y, PredicateApp("P", 1, (y,)))

        self.assertTrue(db.contains_formula(f1))
        self.assertTrue(db.contains_formula(f2))

        # Different formula
        f3 = Forall(x, PredicateApp("Q", 1, (x,)))
        self.assertFalse(db.contains_formula(f3))
        db.close()

    def test_hash_stability(self) -> None:
        db = KnowledgeDatabase(self.db_path)
        x = Variable(0, sort=Ind)
        formula = Forall(x, Equality(x, x))

        hash1 = db._compute_ast_hash(formula)
        hash2 = db._compute_ast_hash(formula)
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)  # SHA-256 hex digest length
        db.close()

    def test_search_formulas_indexing(self) -> None:
        db = KnowledgeDatabase(self.db_path)
        x = Variable(0, sort=Ind)
        y = Variable(1, sort=Ind)

        f1 = PredicateApp("P", 1, (x,))
        f2 = And(PredicateApp("P", 1, (x,)), PredicateApp("Q", 1, (y,)))
        f3 = Forall(x, Forall(y, Implies(PredicateApp("P", 1, (x,)), PredicateApp("Q", 1, (y,)))))

        db.add_axiom("f1", f1, "cat1")
        db.add_axiom("f2", f2, "cat2")
        db.add_axiom("f3", f3, "cat1")

        # Search by predicate name
        results_p = db.search_formulas(predicate_name="P")
        self.assertEqual(len(results_p), 3)

        results_q = db.search_formulas(predicate_name="Q")
        self.assertEqual(len(results_q), 2)

        # Search by max_depth
        shallow = db.search_formulas(max_depth=1)
        self.assertEqual(len(shallow), 1)

        # Search by category
        cat1_formulas = db.search_formulas(category="cat1")
        self.assertEqual(len(cat1_formulas), 2)
        db.close()

    def test_duplicate_axiom_error(self) -> None:
        db = KnowledgeDatabase(self.db_path)
        x = Variable(0, sort=Ind)
        formula = Equality(x, x)
        db.add_axiom("same_name", formula)

        with self.assertRaises(DatabaseError):
            db.add_axiom("same_name", formula)
        db.close()

    def test_transaction_rollback(self) -> None:
        db = KnowledgeDatabase(self.db_path)
        x = Variable(0, sort=Ind)
        formula = Equality(x, x)
        db.add_axiom("valid_ax", formula)

        # Attempting to add an invalid axiom duplicate should roll back transaction
        with self.assertRaises(DatabaseError):
            db.add_axiom("valid_ax", formula)

        # Verify DB is still healthy and operational
        axioms = db.get_axioms()
        self.assertEqual(len(axioms), 1)
        db.close()

    def test_context_manager(self) -> None:
        with KnowledgeDatabase(self.db_path) as db:
            x = Variable(0, sort=Ind)
            db.add_axiom("ctx_ax", Equality(x, x))
            self.assertIsNotNone(db._conn)

        self.assertIsNone(db._conn)

        # Reopen to verify context manager committed changes
        with KnowledgeDatabase(self.db_path) as db:
            axioms = db.get_axioms()
            self.assertEqual(len(axioms), 1)
            self.assertEqual(axioms[0][0], "ctx_ax")

    def test_cli_init(self) -> None:
        cli_db_path = Path(self.temp_dir.name) / "cli_init.db"
        main(["init", "--db-path", str(cli_db_path), "--force"])

        self.assertTrue(cli_db_path.exists())
        with KnowledgeDatabase(cli_db_path) as db:
            axioms = db.get_axioms()
            self.assertGreater(len(axioms), 0)


if __name__ == "__main__":
    unittest.main()
