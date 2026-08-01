"""
Automated docstring coverage test suite (tests/test_docstrings.py).

Verifies that all public modules, classes, functions, and methods in solver have docstrings.
"""

from __future__ import annotations
import dataclasses
import importlib
import inspect
import pkgutil
import unittest

import solver


def get_all_solver_modules():
    """Recursively retrieves all public modules in the solver package."""
    modules = []
    for importer, modname, ispkg in pkgutil.walk_packages(solver.__path__, solver.__name__ + "."):
        if "__main__" in modname:
            continue
        try:
            mod = importlib.import_module(modname)
            modules.append(mod)
        except Exception:
            pass
    return modules


class TestDocstrings(unittest.TestCase):
    """Test case asserting docstring coverage for all public symbols across solver."""

    def test_all_public_symbols_have_docstrings(self) -> None:
        """Verify that every public module, class, method, and function carries a non-empty docstring."""
        modules = get_all_solver_modules()
        missing_docstrings = []

        for module in modules:
            if not module.__doc__ or not module.__doc__.strip():
                missing_docstrings.append(f"Module missing docstring: {module.__name__}")

            for name, obj in inspect.getmembers(module):
                if name.startswith("_"):
                    continue

                if inspect.isclass(obj) and obj.__module__ == module.__name__:
                    if not obj.__doc__ or not obj.__doc__.strip():
                        missing_docstrings.append(f"Class missing docstring: {module.__name__}.{name}")

                    is_dc = dataclasses.is_dataclass(obj)
                    for mname, mobj in inspect.getmembers(obj, predicate=inspect.isfunction):
                        if mname.startswith("_") and mname != "__init__":
                            continue
                        if mname == "__init__" and is_dc:
                            continue
                        if mobj.__module__ != module.__name__:
                            continue
                        if mname.startswith("visit_"):
                            continue

                        if not mobj.__doc__ or not mobj.__doc__.strip():
                            missing_docstrings.append(
                                f"Method missing docstring: {module.__name__}.{name}.{mname}"
                            )
                elif inspect.isfunction(obj) and obj.__module__ == module.__name__:
                    if not obj.__doc__ or not obj.__doc__.strip():
                        missing_docstrings.append(f"Function missing docstring: {module.__name__}.{name}")

        if missing_docstrings:
            self.fail("Found missing docstrings:\n" + "\n".join(missing_docstrings))


if __name__ == "__main__":
    unittest.main()
