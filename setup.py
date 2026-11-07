"""Optional Cython extension compilation setup script for logic library."""

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import os

USE_CYTHON = False
try:
    from Cython.Build import cythonize
    USE_CYTHON = True
except ImportError:
    USE_CYTHON = False


class OptionalBuildExt(build_ext):
    """Custom build_ext command that enables parallel compilation and gracefully falls back to pure Python if C compilation fails."""

    def finalize_options(self):
        """Configure build options with automatic CPU core parallelism.

        Parameters:
            None.

        Returns:
            None: Modifies self.parallel in-place.
        """
        super().finalize_options()
        if not self.parallel:
            self.parallel = os.cpu_count() or 1

    def build_extension(self, ext):
        """Build an individual C extension with graceful failure handling.

        Parameters:
            ext (setuptools.Extension): The extension module to compile.

        Returns:
            None: Compiles the extension or catches compilation errors.
        """
        try:
            super().build_extension(ext)
        except Exception as e:
            print(f"WARNING: Building C extension '{ext.name}' failed: {e}. Falling back to pure Python implementation.")


ext_modules = []
if USE_CYTHON:
    hotspot_files = [
        "logic_prover/core/ast.py",
        "logic_prover/core/substitutions.py",
        "logic_prover/core/visitors.py",
        "logic_prover/prover/clausifier.py",
        "logic_prover/prover/rules.py",
        "logic_prover/prover/engine.py",
        "logic_prover/constructive/common.py",
        "logic_prover/constructive/kripke.py",
        "logic_prover/constructive/prefix.py",
        "logic_prover/constructive/matrix.py",
        "logic_prover/constructive/ljt.py",
        "logic_prover/constructive/wallen.py",
        "logic_prover/constructive/tableau/ast.py",
        "logic_prover/constructive/tableau/branch.py",
        "logic_prover/constructive/tableau/prover.py",
        "logic_prover/constructive/resolution/clauses.py",
        "logic_prover/constructive/resolution/prefixed.py",
        "logic_prover/constructive/resolution/translation.py",
        "logic_prover/constructive/resolution/prover.py",
    ]
    # Filter files that exist
    valid_files = [f for f in hotspot_files if os.path.exists(f)]
    if valid_files:
        extensions = [
            Extension(
                f.replace("/", ".").replace("\\", ".").replace(".py", ""),
                [f],
            )
            for f in valid_files
        ]
        cpu_count = os.cpu_count() or 1
        ext_modules = cythonize(
            extensions,
            nthreads=cpu_count,
            compiler_directives={
                "language_level": "3",
                "boundscheck": False,
                "wraparound": True,
                "nonecheck": False,
                "initializedcheck": False,
            },
            quiet=True,
        )

setup(
    cmdclass={"build_ext": OptionalBuildExt} if ext_modules else {},
    ext_modules=ext_modules,
)
