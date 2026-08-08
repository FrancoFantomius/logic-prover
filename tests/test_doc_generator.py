"""
Unit tests for the doc generator subsystem (logic/utils/doc_generator.py).
"""

from __future__ import annotations
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from logic.utils.doc_generator import (
    parse_google_docstring,
    extract_docstrings_from_module,
    render_markdown_module,
    build_markdown_docs,
    ModuleDoc,
)


class TestDocGenerator(unittest.TestCase):
    """Test suite for docstring parsing, AST metadata extraction, and Markdown doc generation."""

    def test_parse_google_docstring(self) -> None:
        """Test parsing Google-style docstring blocks."""
        docstring = """
        Summary line of function.

        Detailed description paragraph with more information.

        Args:
            x (int): The x coordinate.
            y (str): The name.

        Returns:
            bool: True if valid.

        Raises:
            ValueError: If x is negative.
        """
        summary, desc, params, returns, raises = parse_google_docstring(docstring)

        self.assertEqual(summary, "Summary line of function.")
        self.assertIn("Detailed description", desc)
        self.assertEqual(len(params), 2)
        self.assertEqual(params[0].name, "x")
        self.assertEqual(params[0].type_hint, "int")
        self.assertEqual(params[0].description, "The x coordinate.")
        self.assertEqual(params[1].name, "y")
        self.assertEqual(params[1].type_hint, "str")
        self.assertIsNotNone(returns)
        self.assertEqual(returns.type_hint, "bool")
        self.assertEqual(returns.description, "True if valid.")
        self.assertEqual(len(raises), 1)
        self.assertEqual(raises[0].type_name, "ValueError")
        self.assertEqual(raises[0].description, "If x is negative.")

    def test_extract_docstrings_from_module(self) -> None:
        """Test AST docstring extraction on a sample Python module file."""
        code = '''"""Module summary line."""

class DummyClass:
    """Class summary."""

    def dummy_method(self, a: int) -> str:
        """
        Method summary.

        Args:
            a (int): An integer.

        Returns:
            str: Output string.
        """
        return str(a)

def dummy_func(x: float) -> int:
    """Function summary."""
    return int(x)
'''
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        try:
            mod_doc = extract_docstrings_from_module(tmp_path)
            self.assertEqual(mod_doc.summary, "Module summary line.")
            self.assertEqual(len(mod_doc.classes), 1)
            self.assertEqual(mod_doc.classes[0].name, "DummyClass")
            self.assertEqual(len(mod_doc.classes[0].methods), 1)
            self.assertEqual(mod_doc.classes[0].methods[0].name, "dummy_method")
            self.assertEqual(len(mod_doc.functions), 1)
            self.assertEqual(mod_doc.functions[0].name, "dummy_func")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_extract_non_existent_file(self) -> None:
        """Test FileNotFoundError when extracting non-existent module file."""
        with self.assertRaises(FileNotFoundError):
            extract_docstrings_from_module("non_existent_file_path_xyz.py")

    def test_render_markdown_module(self) -> None:
        """Test rendering ModuleDoc into Markdown format."""
        code = '''"""Test module summary."""

def sample_function(param: int) -> bool:
    """Sample function summary."""
    return True
'''
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        try:
            mod_doc = extract_docstrings_from_module(tmp_path)
            markdown = render_markdown_module(mod_doc)
            self.assertIn("# Module", markdown)
            self.assertIn("Test module summary.", markdown)
            self.assertIn("`def sample_function", markdown)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_build_markdown_docs(self) -> None:
        """Test scanning codebase and writing Markdown documentation portal."""
        tmp_dir = tempfile.mkdtemp()
        try:
            docs = build_markdown_docs(source_dir="logic", output_docs_dir=tmp_dir)
            self.assertTrue(len(docs) > 0)
            index_path = Path(tmp_dir) / "index.md"
            self.assertTrue(index_path.exists())
            index_content = index_path.read_text(encoding="utf-8")
            self.assertIn("Logic Documentation Portal", index_content)

            api_dir = Path(tmp_dir) / "api"
            self.assertTrue(api_dir.exists())
            api_files = list(api_dir.glob("*.md"))
            self.assertTrue(len(api_files) > 0)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
