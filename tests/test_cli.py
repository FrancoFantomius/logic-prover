"""
Integration tests for the logic CLI entry point (logic/__main__.py).
"""

from __future__ import annotations
import os
import shutil
import tempfile
import unittest

from logic_prover.__main__ import main
from logic_prover.core.database import KnowledgeDatabase
from logic_prover.core.parser import parse_formula
from logic_prover.kb import get_combined_signature


class TestSolverCLI(unittest.TestCase):
    """Test suite executing all 7 CLI commands end-to-end."""

    def setUp(self) -> None:
        """Create a temporary directory and database path for CLI execution."""
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp_dir, "test_cli.db")
        self.sig = get_combined_signature()

    def tearDown(self) -> None:
        """Clean up temporary directory."""
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_cli_init(self) -> None:
        """Test 'init' command creates and populates database."""
        ret = main(["init", "--db-path", self.db_path, "--force"])
        self.assertEqual(ret, 0)
        self.assertTrue(os.path.exists(self.db_path))

    def test_cli_explore(self) -> None:
        """Test 'explore' command generates and prints candidates."""
        main(["init", "--db-path", self.db_path])
        ret = main(["explore", "--count", "5", "--top-k", "2", "--db-path", self.db_path])
        self.assertEqual(ret, 0)

    def test_cli_prove_positional(self) -> None:
        """Test 'prove' command with positional target formula string."""
        ret = main(["prove", "P(v0) => P(v0)"])
        self.assertEqual(ret, 0)

    def test_cli_prove_option(self) -> None:
        """Test 'prove' command with --target argument option."""
        ret = main(["prove", "--target", "P(v0) => P(v0)"])
        self.assertEqual(ret, 0)

    def test_cli_prove_stubs_only(self) -> None:
        """Test 'prove' command with --stubs-only flag."""
        ret = main(["prove", "forall v0 : Ind, P(v0)", "--stubs-only"])
        self.assertEqual(ret, 0)

    def test_cli_analyze(self) -> None:
        """Test 'analyze' command performs network dependency analysis."""
        db = KnowledgeDatabase(self.db_path)
        db.add_axiom("ax1", parse_formula("P(v0) => P(v0)", self.sig), "test")
        db.add_axiom("ax2", parse_formula("Q(v0) => Q(v0)", self.sig), "test")
        db.close()

        out_json = os.path.join(self.tmp_dir, "graph.json")
        ret = main(["analyze", "--db-path", self.db_path, "--category", "test", "--output", out_json])
        self.assertEqual(ret, 0)
        self.assertTrue(os.path.exists(out_json))

    def test_cli_export_lean(self) -> None:
        """Test 'export lean' command generates LEAN formal file."""
        db = KnowledgeDatabase(self.db_path)
        db.add_axiom("ax1", parse_formula("P(v0) => P(v0)", self.sig), "test")
        db.close()

        out_lean = os.path.join(self.tmp_dir, "output.lean")
        ret = main(["export", "lean", "--output", out_lean, "--stubs-only", "--db-path", self.db_path])
        self.assertEqual(ret, 0)
        self.assertTrue(os.path.exists(out_lean))

    def test_cli_export_graph(self) -> None:
        """Test 'export graph' command produces HTML dependency visualization."""
        db = KnowledgeDatabase(self.db_path)
        db.add_axiom("ax1", parse_formula("P(v0) => P(v0)", self.sig), "test")
        db.close()

        out_html = os.path.join(self.tmp_dir, "graph.html")
        ret = main(["export", "graph", "--type", "dependency", "--output", out_html, "--db-path", self.db_path])
        self.assertEqual(ret, 0)
        self.assertTrue(os.path.exists(out_html))

    def test_cli_docs(self) -> None:
        """Test 'docs' command generates markdown documentation files."""
        docs_dir = os.path.join(self.tmp_dir, "docs")
        ret = main(["docs", "--output-dir", docs_dir])
        self.assertEqual(ret, 0)
        self.assertTrue(os.path.exists(os.path.join(docs_dir, "index.md")))

    def test_cli_invalid_args(self) -> None:
        """Test invalid subcommand returns non-zero status code."""
        ret = main(["non_existent_command"])
        self.assertNotEqual(ret, 0)


if __name__ == "__main__":
    unittest.main()
