import unittest
import os
import tempfile
from solver.database import TheoryDatabase
from solver.graph_exporter import build_theory_graph, export_graph_dot, export_graph_json, export_graph_html


class TestGraphExporter(unittest.TestCase):
    def setUp(self):
        self.temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db_file.close()
        self.db = TheoryDatabase(db_path=self.temp_db_file.name)

    def tearDown(self):
        if os.path.exists(self.temp_db_file.name):
            os.remove(self.temp_db_file.name)

    def test_build_theory_graph_nodes_and_edges(self):
        self.db.add_axiom("ax1", "p -> q")
        steps = [
            {'step_idx': 0, 'formula_str': 'p -> q', 'justification_type': 'Axiom', 'ref_name': 'ax1', 'substitution_json': None},
            {'step_idx': 1, 'formula_str': 'p', 'justification_type': 'Hypothesis', 'ref_name': 'h0', 'substitution_json': None},
            {'step_idx': 2, 'formula_str': 'q', 'justification_type': 'MP', 'arg1': 1, 'arg2': 0, 'ref_name': None, 'substitution_json': None}
        ]
        self.db.save_theorem(
            name="thm_demo",
            thesis_str="q",
            hypotheses=["p"],
            steps=steps,
            is_verified=1
        )

        graph_data = build_theory_graph(self.db)
        self.assertIn("nodes", graph_data)
        self.assertIn("edges", graph_data)
        self.assertTrue(len(graph_data["nodes"]) >= 3)
        self.assertTrue(len(graph_data["edges"]) >= 2)

    def test_export_formats(self):
        self.db.add_axiom("ax_base", "A -> B")

        with tempfile.TemporaryDirectory() as tmpdir:
            dot_path = os.path.join(tmpdir, "graph.dot")
            json_path = os.path.join(tmpdir, "graph.json")
            html_path = os.path.join(tmpdir, "graph.html")

            dot_content = export_graph_dot(self.db, dot_path)
            json_content = export_graph_json(self.db, json_path)
            html_content = export_graph_html(self.db, html_path)

            self.assertTrue(os.path.exists(dot_path))
            self.assertTrue(os.path.exists(json_path))
            self.assertTrue(os.path.exists(html_path))

            self.assertIn("digraph TheoryGraph", dot_content)
            self.assertIn("nodes", json_content)
            self.assertIn("vis.Network", html_content)


if __name__ == "__main__":
    unittest.main()
