# Phase 13 — Documentation, Logging & Polish Implementation Plan

> **Phase Goal**: Implement a robust logging subsystem, an automated Markdown documentation generator, a production-grade CLI entry point supporting all 7 solver commands, repository packaging (`pyproject.toml`), comprehensive project documentation (`README.md` and `docs/`), and an automated docstring verification test suite enforcing $\ge 85\%$ line coverage across the entire `solver` codebase.

---

## 1. Overview & Architecture Strategy

Phase 13 is the final phase of the solver library implementation. It integrates all core logic components—AST, sorts, parser, unification, congruence closure, database, resolution prover, formula explorer, deducer, and exporters—into a unified, fully documented, and easily deployable Python package.

```
                  ┌──────────────────────────────────────────────┐
                  │            solver/__main__.py (CLI)           │
                  └──────┬───────────────────────────────┬───────┘
                         │                               │
       ┌─────────────────┼─────────────────┐             │
       ▼                 ▼                 ▼             ▼
┌──────────────┐ ┌──────────────┐ ┌────────────────┐ ┌─────────────┐
│ solver.init  │ │ solver.prove │ │ solver.explore │ │ solver.docs │
└──────┬───────┘ └──────┬───────┘ └──────┬─────────┘ └──────┬──────┘
       │                │                │                  │
       ▼                ▼                ▼                  ▼
┌──────────────┐ ┌──────────────┐ ┌────────────────┐ ┌─────────────┐
│ KnowledgeDB  │ │TheoremProver │ │FormulaExplorer │ │DocGenerator │
└──────────────┘ └──────────────┘ └────────────────┘ └─────────────┘
       ▲                ▲                ▲                  ▲
       └────────────────┴────────┬───────┴──────────────────┘
                                 │
                      ┌──────────┴──────────┐
                      │ solver.utils.logging│
                      └─────────────────────┘
```

### Key Architectural Decisions:

1. **Centralized Hierarchical Logging (`solver/utils/logging.py`)**:
   - Implements `setup_logging()` to configure Python's standard `logging` library across all `solver.*` namespaces.
   - Modules obtain loggers via `logger = logging.getLogger(__name__)`.
   - Supports configurable log levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`), custom formatting with ISO timestamps and module pathways, and handler direction to `sys.stderr` or log files.

2. **Automated Reflection & AST Documentation Generator (`solver/utils/doc_generator.py`)**:
   - Inspects Python source code using Python's `ast` (Abstract Syntax Tree) module combined with `inspect` reflection to extract module, class, function, parameter, type annotation, return type, exception, and docstring metadata.
   - Parses Google/Sphinx docstring conventions (`Args:`, `Returns:`, `Raises:`, `Examples:`).
   - Generates static, clean GitHub-flavored Markdown files under `docs/api/` and builds an interactive `docs/index.md` documentation portal.

3. **Production CLI Entry Point (`solver/__main__.py`)**:
   - Uses Python's `argparse` to provide an intuitive, end-to-end command-line interface executable via `python -m solver <command>`.
   - Supports 7 main CLI commands: `init`, `explore`, `prove`, `analyze`, `export lean`, `export graph`, and `docs`.
   - Strictly respects `SolverConfig` (loaded from `solver.toml` or defaults) and allows CLI flags to override configuration values dynamically.

4. **Testing, Coverage & Quality Assurance**:
   - Enforces automated docstring presence validation (`tests/test_docstrings.py`) to verify that all public functions, classes, and methods carry valid docstrings.
   - Standardizes test execution using `pytest` and `pytest-cov`, targeted at maintaining $\ge 85\%$ code coverage.
   - Includes end-to-end integration tests for all 7 CLI commands in `tests/test_cli.py`.

5. **Package Packaging & Documentation**:
   - Defines modern package configuration in `pyproject.toml` (compatible with `setuptools`, `flit`, or `hatchling`), including dependency specifications, optional visual/dev dependencies, and pytest defaults.
   - Provides a comprehensive `README.md` containing architectural overviews, quickstart guides, CLI examples, and Python library usage patterns.

---

## 2. Prerequisites

The following phases and components must be fully implemented and verified before Phase 13:

1. **Phase 1 — AST & Sort System**: `solver/core/ast.py`, `solver/core/sorts.py`, `solver/core/exceptions.py`.
2. **Phase 2 — Signature & Validator**: `solver/core/signature.py`, `solver/core/validator.py`.
3. **Phase 3 — Visitor Framework & Parser**: `solver/core/visitors.py`, `solver/core/parser.py`.
4. **Phase 4 — Substitution & Unification**: `solver/core/substitutions.py`.
5. **Phase 5 — Equality & Rewriting**: `solver/core/equality.py`, `solver/core/rewriter.py`.
6. **Phase 6 — Knowledge Base & Database**: `solver/kb/*.py`, `solver/core/database.py`, `solver/config.py`.
7. **Phase 7 — Theorem Prover**: `solver/prover/*.py`.
8. **Phase 8 — Formula Explorer**: `solver/explorer/*.py`.
9. **Phase 9 — Deducer**: `solver/deducer/*.py`.
10. **Phase 10 — Exporters**: `solver/exporters/lean_exporter.py`, `solver/exporters/graph_exporter.py`.
11. **Phase 11 — SOL Extension**: `solver/sol/*.py`.
12. **Phase 12 — Extended Knowledge Base**: `solver/kb/groups.py`, `solver/kb/relations.py`, `solver/kb/orders.py`, `solver/kb/sets.py`, `solver/kb/functions.py`.

---

## 3. Files to Create / Modify

| File Path | Action | Description |
| :--- | :--- | :--- |
| [solver/utils/logging.py](file:///C:/Users/franc/Programmazione/solver/solver/utils/logging.py) | Create | Central logging configuration (`setup_logging`, `get_logger`, custom formatter) |
| [solver/utils/doc_generator.py](file:///C:/Users/franc/Programmazione/solver/solver/utils/doc_generator.py) | Create | AST and reflection docstring extractor (`extract_docstrings_from_module`, `build_markdown_docs`) |
| [solver/__main__.py](file:///C:/Users/franc/Programmazione/solver/solver/__main__.py) | Modify | CLI entry point implementing all 7 commands (`init`, `explore`, `prove`, `analyze`, `export lean`, `export graph`, `docs`) |
| [pyproject.toml](file:///C:/Users/franc/Programmazione/solver/pyproject.toml) | Create | Package setup, build tool specs, dependencies, and `pytest-cov` settings (min 85% coverage) |
| [README.md](file:///C:/Users/franc/Programmazione/solver/README.md) | Create | Full repository README, quickstart guide, CLI reference, and code examples |
| [docs/index.md](file:///C:/Users/franc/Programmazione/solver/docs/index.md) | Create | Documentation site landing page and API overview |
| [tests/test_logging.py](file:///C:/Users/franc/Programmazione/solver/tests/test_logging.py) | Create | Unit tests for logger configuration, formatting, and level filtering |
| [tests/test_doc_generator.py](file:///C:/Users/franc/Programmazione/solver/tests/test_doc_generator.py) | Create | Unit tests for AST docstring extraction and Markdown page generation |
| [tests/test_docstrings.py](file:///C:/Users/franc/Programmazione/solver/tests/test_docstrings.py) | Create | Automated test verifying docstring presence on 100% of public functions/classes |
| [tests/test_cli.py](file:///C:/Users/franc/Programmazione/solver/tests/test_cli.py) | Create | Integration tests executing all 7 CLI commands end-to-end |

---

## 4. Detailed Module Specifications

### 4.1 `solver/utils/logging.py` (Section 3.18)

Provides central logging setup, log formatting, and hierarchical loggers for all library modules.

```python
import logging
import sys
from typing import Optional, TextIO, Union, Dict, Any
from solver.config import SolverConfig

class SolverLogFormatter(logging.Formatter):
    """
    Custom log formatter for the solver library providing structured output.
    
    Formats:
    - Standard: "[2026-08-01 15:30:00] [INFO] [solver.prover.engine]: Proof found in 4 steps."
    - Debug: Include line numbers and thread identifiers when verbosity is HIGH.
    """
    
    FMT_NORMAL = "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"
    FMT_DEBUG = "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d]: %(message)s"
    DATE_FMT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, debug_mode: bool = False) -> None:
        fmt = self.FMT_DEBUG if debug_mode else self.FMT_NORMAL
        super().__init__(fmt=fmt, datefmt=self.DATE_FMT)

def setup_logging(
    config: Optional[SolverConfig] = None,
    log_level: Optional[Union[str, int]] = None,
    log_file: Optional[str] = None,
    stream: Optional[TextIO] = None
) -> None:
    """
    Configures the root logger for the solver library ('solver').

    Args:
        config: Optional SolverConfig instance. If provided, log level is pulled from config.verbosity.
        log_level: Explicit string ('DEBUG', 'INFO', 'WARNING', 'ERROR') or logging level int.
        log_file: Optional path to write log output to disk.
        stream: Output stream for logging (defaults to sys.stderr).

    Raises:
        ValueError: If log_level is invalid.
    """
    pass

def get_logger(name: str) -> logging.Logger:
    """
    Retrieves a logger instance scoped under the 'solver' namespace.

    Args:
        name: Sub-module name (e.g. 'prover.engine' or 'solver.core.ast').

    Returns:
        logging.Logger configured to bubble events up to root 'solver' logger.
    """
    pass
```

#### Log Level Policy Matrix

| Level | Usage in Solver Modules | Example Call Site |
| :--- | :--- | :--- |
| `DEBUG` | Fine-grained execution details: unification substitutions, clause generation, rewrite steps | `logger.debug(f"Unified terms {t1} and {t2} with subst {subst}")` |
| `INFO` | Major operational milestones: proof search success/exhaustion, explorer batch metrics | `logger.info(f"Proof search succeeded for theorem '{name}' in {time:.3f}s")` |
| `WARNING` | Non-fatal anomalies: near timeout threshold (>80%), large search space warnings | `logger.warning(f"Proof search step count ({steps}) exceeding 80% of max_steps")` |
| `ERROR` | Recoverable or unrecoverable operation failures, database corruption, invalid CLI flags | `logger.error(f"Failed to parse formula '{raw_input}': {err}")` |

---

### 4.2 `solver/utils/doc_generator.py` (Section 3.19)

Extracts docstrings and type annotations via Python's AST and `inspect` reflection modules, generating clean Markdown documentation files.

```python
import ast
import inspect
import importlib
import os
import pkgutil
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple, Union

@dataclass
class ParamDoc:
    """Represents a parameter documentation entry."""
    name: str
    type_hint: str
    description: str

@dataclass
class ReturnDoc:
    """Represents a return value documentation entry."""
    type_hint: str
    description: str

@dataclass
class ExceptionDoc:
    """Represents an exception documentation entry."""
    type_name: str
    description: str

@dataclass
class FunctionDoc:
    """Represents a documented standalone function or method."""
    name: str
    signature: str
    summary: str
    description: str
    params: List[ParamDoc] = field(default_factory=list)
    returns: Optional[ReturnDoc] = None
    raises: List[ExceptionDoc] = field(default_factory=list)
    is_method: bool = False
    is_async: bool = False

@dataclass
class ClassDoc:
    """Represents a documented class."""
    name: str
    signature: str
    summary: str
    description: str
    bases: List[str] = field(default_factory=list)
    methods: List[FunctionDoc] = field(default_factory=list)

@dataclass
class ModuleDoc:
    """Represents a documented Python module."""
    module_path: str
    module_name: str
    summary: str
    description: str
    classes: List[ClassDoc] = field(default_factory=list)
    functions: List[FunctionDoc] = field(default_factory=list)

def parse_google_docstring(docstring: Optional[str]) -> Tuple[str, str, List[ParamDoc], Optional[ReturnDoc], List[ExceptionDoc]]:
    """
    Parses a Google-style docstring into structured components.

    Args:
        docstring: Raw docstring text.

    Returns:
        Tuple containing (summary, detailed_description, params_list, return_info, raises_list).
    """
    pass

def extract_docstrings_from_module(module_path: str) -> ModuleDoc:
    """
    Inspects docstrings and signatures from a Python module file using AST and reflection.

    Args:
        module_path: Absolute or relative file path to a .py file (e.g. 'solver/core/ast.py').

    Returns:
        ModuleDoc containing parsed classes, functions, signatures, and docstring sections.

    Raises:
        FileNotFoundError: If module_path does not exist.
        SyntaxError: If module_path contains invalid Python syntax.
    """
    pass

def render_markdown_module(module_doc: ModuleDoc) -> str:
    """
    Renders a ModuleDoc object into GitHub-flavored Markdown text.

    Args:
        module_doc: ModuleDoc instance.

    Returns:
        Formatted Markdown string.
    """
    pass

def build_markdown_docs(source_dir: str = "solver", output_docs_dir: str = "docs") -> Dict[str, str]:
    """
    Scans the source codebase, extracts docstrings from all modules, and writes Markdown documentation.

    Generates:
    - docs/api/<module_group>.md (e.g., docs/api/core.md, docs/api/prover.md)
    - docs/index.md (Landing page with module links and summary tables)

    Args:
        source_dir: Root package directory to scan (default 'solver').
        output_docs_dir: Target output directory for markdown files (default 'docs').

    Returns:
        Dictionary mapping created file paths to rendered content length.
    """
    pass
```

#### Markdown Formatting Template (`render_markdown_module`)

```markdown
# Module: `{module_name}`

{summary}

{description}

---

## Table of Contents
- [Classes](#classes)
- [Functions](#functions)

---

## Classes

### `class {class_name}({bases})`

{class_summary}

{class_description}

#### Methods

##### `def {method_name}{signature}`
{method_summary}

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `param_name` | `type_hint` | param_description |

**Returns:** `return_type` — return_description

**Raises:** `ExceptionType` — exception_description

---

## Functions

### `def {func_name}{signature}`
{func_summary}

...
```

---

### 4.3 `solver/__main__.py` (Section 3.20)

CLI entry point providing a complete command interface with subcommands, option parsing, config integration, and user-friendly error output.

```python
import argparse
import sys
import os
from typing import List, Optional
from solver.config import SolverConfig
from solver.utils.logging import setup_logging, get_logger
from solver.core.exceptions import SolverError, ParseError, ProofTimeoutError

logger = get_logger("cli")

def build_parser() -> argparse.ArgumentParser:
    """
    Constructs the top-level ArgumentParser and all subcommand parsers.

    Subcommands:
    - init: Initialize database with axioms
    - explore: Run formula explorer
    - prove: Prove target formula from premises
    - analyze: Run deducer hypothesis analysis
    - export lean: Export to LEAN 4 code
    - export graph: Export interactive proof/dependency HTML graph
    - docs: Regenerate static API documentation

    Returns:
        Configured argparse.ArgumentParser instance.
    """
    pass

def cmd_init(args: argparse.Namespace, config: SolverConfig) -> int:
    """Executes the 'init' command."""
    pass

def cmd_explore(args: argparse.Namespace, config: SolverConfig) -> int:
    """Executes the 'explore' command."""
    pass

def cmd_prove(args: argparse.Namespace, config: SolverConfig) -> int:
    """Executes the 'prove' command."""
    pass

def cmd_analyze(args: argparse.Namespace, config: SolverConfig) -> int:
    """Executes the 'analyze' command."""
    pass

def cmd_export_lean(args: argparse.Namespace, config: SolverConfig) -> int:
    """Executes the 'export lean' command."""
    pass

def cmd_export_graph(args: argparse.Namespace, config: SolverConfig) -> int:
    """Executes the 'export graph' command."""
    pass

def cmd_docs(args: argparse.Namespace, config: SolverConfig) -> int:
    """Executes the 'docs' command."""
    pass

def main(argv: Optional[List[str]] = None) -> int:
    """
    Main entry point for CLI invocation.

    Args:
        argv: Optional list of argument strings (defaults to sys.argv[1:]).

    Returns:
        Exit code: 0 for success, non-zero for failure.
    """
    pass

if __name__ == "__main__":
    sys.exit(main())
```

#### Detailed Command Line Interface Specification

1. **Initialize Database**:
   ```bash
   python -m solver init [--db-path PATH] [--reset]
   ```
   - `--db-path`: Path to SQLite database (defaults to `config.db_path`).
   - `--reset`: Force re-creation of tables and reloading of core axioms (`kb.logic`, `kb.equality`, `kb.numbers`).

2. **Explore Candidate Formulas**:
   ```bash
   python -m solver explore [--strategy STR] [--depth N] [--count N] [--top-k N] [--db-path PATH]
   ```
   - `--strategy`: Formula generation strategy (`axiom_rewrite`, `proof_frontier`, `saturation`, `all`, default: `all`).
   - `--depth`: Maximum search depth (default: 3).
   - `--count`: Number of candidates to generate (default: 50).
   - `--top-k`: Number of top-ranked candidates to display (default: 10).

3. **Prove Theorem**:
   ```bash
   python -m solver prove FORMULA [--premises P1 P2 ...] [--timeout SEC] [--max-steps N] [--stubs-only]
   ```
   - `FORMULA`: Positional string representing target formula to prove (e.g. `"(forall x (P x -> Q x)) -> ((forall x P x) -> (forall x Q x))"`).
   - `--premises`: Space-separated list of premise formula strings.
   - `--timeout`: Maximum proving wall-clock timeout in seconds (default: 10.0).
   - `--max-steps`: Maximum given-clause iterations (default: 1000).

4. **Analyze Axioms & Hypotheses**:
   ```bash
   python -m solver analyze [--category CAT] [--pairwise] [--db-path PATH]
   ```
   - `--category`: Axiom category to analyze (e.g., `logic`, `equality`, `peano`).
   - `--pairwise`: Run full pairwise independence and equivalence analysis.

5. **Export to Lean 4**:
   ```bash
   python -m solver export lean [--output FILE] [--theorems T1 T2 ...] [--stubs-only]
   ```
   - `--output`: File destination path for generated Lean 4 code (default: `output.lean`).
   - `--theorems`: Specific theorem names or IDs to export.
   - `--stubs-only`: Emit theorem declarations with `sorry` stubs instead of complete tactic proofs.

6. **Export Interactive HTML Graph**:
   ```bash
   python -m solver export graph [--output FILE] [--type proof|dependency] [--theorem THM]
   ```
   - `--output`: Output HTML file path (default: `graph.html`).
   - `--type`: Graph visualization type (`proof` for single proof DAG or `dependency` for full knowledge base DAG).
   - `--theorem`: Target theorem name (required when `--type proof`).

7. **Generate Documentation**:
   ```bash
   python -m solver docs [--output-dir DIR]
   ```
   - `--output-dir`: Output directory for generated markdown docs (default: `docs`).

---

### 4.4 Packaging & Quality Assurance Configuration

#### `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "solver"
version = "1.0.0"
description = "A formal logic theorem prover, explorer, deducer, and LEAN exporter in Python."
readme = "README.md"
authors = [
    { name = "Solver Development Team", email = "info@solver.org" }
]
license = { text = "MIT" }
requires-python = ">=3.10"
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Science/Research",
    "Topic :: Scientific/Engineering :: Mathematics",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
dependencies = [
    "lark>=1.1.0",
    "tomli>=2.0.0; python_version < '3.11'",
]

[project.optional-dependencies]
vis = [
    "jinja2>=3.0.0",
]
dev = [
    "pytest>=7.2.0",
    "pytest-cov>=4.0.0",
    "hypothesis>=6.70.0",
    "mypy>=1.0.0",
    "ruff>=0.1.0",
]

[project.scripts]
solver = "solver.__main__:main"

[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
addopts = "--cov=solver --cov-report=term-missing --cov-report=html --cov-fail-under=85 -v"
filterwarnings = [
    "ignore::DeprecationWarning",
]

[tool.coverage.run]
source = ["solver"]
branch = true
omit = [
    "solver/__main__.py",
]

[tool.coverage.report]
show_missing = true
precision = 2
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

---

### 4.5 Package Documentation (`README.md`)

`README.md` provides an end-to-end overview, installation guide, quickstart, CLI reference, and API usage guide.

```markdown
# Solver — Formal Logic Theorem Prover & Explorer in Python

`solver` is a Python library for formal logic, featuring First-Order Logic (FOL) AST manipulation, term rewriting, automated resolution theorem proving, formula exploration, dependency graph deduction, higher-order logic extensions, and Lean 4 export.

---

## Features
- **First-Order & Second-Order Logic AST**: Full support for parameterized sorts, canonical variable renaming, and substitutions.
- **Resolution Prover with Equality**: Otter/Discount given-clause loop with superposition and natural deduction proof reconstruction.
- **Formula Explorer**: Diversity-guided formula generation and interestingness heuristic ranking.
- **Deducer**: Network-level minimal hypothesis detection and equivalence classification.
- **Lean 4 Export**: High-fidelity translation of formulas, statements, and tactic proofs into Lean 4 code.
- **Interactive HTML Graphs**: Proof DAG and dependency graph visualizer.

---

## Quickstart & CLI

```bash
# Initialize Knowledge Database
python -m solver init --reset

# Prove a Theorem
python -m solver prove "(forall x (P x -> Q x)) -> ((forall x P x) -> (forall x Q x))"

# Explore Candidate Formulas
python -m solver explore --strategy saturation --count 20 --top-k 5

# Export to Lean 4
python -m solver export lean --output theorem.lean --theorems thm_001

# Export Interactive Proof Graph
python -m solver export graph --type proof --theorem thm_001 --output proof.html

# Generate API Documentation
python -m solver docs --output-dir docs
```

---

## Python API Example

```python
from solver.core.parser import parse_formula
from solver.prover.engine import TheoremProver
from solver.config import SolverConfig

config = SolverConfig(timeout_sec=5.0, max_steps=500)
prover = TheoremProver(config=config)

hypothesis = parse_formula("forall x, (P(x) -> Q(x))")
conclusion = parse_formula("(forall x, P(x)) -> (forall x, Q(x))")

proof_result = prover.prove(conclusion, premises=[hypothesis])
if proof_result.is_success:
    print("Proof Found!")
    print(proof_result.proof_dag.to_string())
```
```

---

## 5. Step-by-Step Implementation Order

```
┌───────────────────────────────────────────────────────────┐
│ Step 1: Logging Subsystem                                 │
│ Implement solver/utils/logging.py & tests/test_logging.py │
└─────────────────────────────┬─────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│ Step 2: Doc Generator Subsystem                           │
│ Implement solver/utils/doc_generator.py                   │
│ & tests/test_doc_generator.py                             │
└─────────────────────────────┬─────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│ Step 3: CLI Entry Point & Subcommands                     │
│ Implement solver/__main__.py & tests/test_cli.py          │
└─────────────────────────────┬─────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│ Step 4: Packaging & Repository Setup                      │
│ Create pyproject.toml & README.md                         │
└─────────────────────────────┬─────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│ Step 5: Automated Docstring Verification                  │
│ Implement tests/test_docstrings.py & run full coverage   │
└─────────────────────────────┬─────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│ Step 6: Documentation Site Generation                      │
│ Run 'python -m solver docs' to build docs/ & docs/api/   │
└───────────────────────────────────────────────────────────┘
```

1. **Step 1: Logging Subsystem (`solver/utils/logging.py`)**:
   - Implement `setup_logging()`, `get_logger()`, and `SolverLogFormatter`.
   - Add unit tests in `tests/test_logging.py` testing log formatting, file writing, stream capturing, and level filtering.

2. **Step 2: Automated Documentation Generator (`solver/utils/doc_generator.py`)**:
   - Implement `extract_docstrings_from_module()`, `parse_google_docstring()`, `render_markdown_module()`, and `build_markdown_docs()`.
   - Add unit tests in `tests/test_doc_generator.py` validating AST extraction, Google docstring block parsing, and markdown rendering.

3. **Step 3: CLI Entry Point Polish (`solver/__main__.py`)**:
   - Implement complete `build_parser()` with subcommands (`init`, `explore`, `prove`, `analyze`, `export lean`, `export graph`, `docs`).
   - Implement handlers `cmd_init`, `cmd_explore`, `cmd_prove`, `cmd_analyze`, `cmd_export_lean`, `cmd_export_graph`, `cmd_docs`.
   - Add CLI integration tests in `tests/test_cli.py` executing all commands end-to-end using `sys.argv` mocking or `main(argv)`.

4. **Step 4: Packaging & Repository Setup**:
   - Create `pyproject.toml` with project metadata, dependencies, script entry points, and `pytest-cov` settings (enforcing `--cov-fail-under=85`).
   - Create comprehensive `README.md` with features, CLI reference, and Python API examples.

5. **Step 5: Docstring Completeness Verification (`tests/test_docstrings.py`)**:
   - Implement `tests/test_docstrings.py` using `importlib` and `inspect` to walk through all `solver.*` modules and assert that every public function, class, and method has a non-empty docstring.
   - Run `pytest` with coverage reporting to confirm overall code coverage $\ge 85\%$.

6. **Step 6: Static Documentation Build (`docs/`)**:
   - Execute `python -m solver docs --output-dir docs`.
   - Verify that `docs/index.md` and `docs/api/*.md` files are built properly and contain accurate class/function definitions.

---

## 6. Testing Requirements

### 6.1 Unit Tests (`tests/test_logging.py`)
- Test standard `setup_logging(log_level="DEBUG")` attaches handlers to the root `solver` logger.
- Test custom log formatter includes timestamps, module name, and line numbers when `debug_mode=True`.
- Test `get_logger("prover.engine")` properly scopes logger under `solver.prover.engine`.

### 6.2 Unit Tests (`tests/test_doc_generator.py`)
- Test docstring parsing on sample modules containing classes, methods, parameters, return types, and exceptions.
- Test `parse_google_docstring()` correctly separates summary, `Args:`, `Returns:`, and `Raises:` sections.
- Test `build_markdown_docs()` creates output files under `docs/api/` and updates `docs/index.md`.

### 6.3 Automated Docstring Verification (`tests/test_docstrings.py`)

```python
import importlib
import inspect
import pkgutil
import pytest
import solver

def get_all_solver_modules():
    modules = []
    for importer, modname, ispkg in pkgutil.walk_packages(solver.__path__, solver.__name__ + "."):
        if "_main__" in modname:
            continue
        try:
            mod = importlib.import_module(modname)
            modules.append(mod)
        except Exception:
            pass
    return modules

@pytest.mark.parametrize("module", get_all_solver_modules())
def test_module_docstrings_present(module):
    """Asserts that all public modules, functions, classes, and methods have docstrings."""
    assert module.__doc__ is not None and len(module.__doc__.strip()) > 0, f"Module {module.__name__} missing docstring"
    
    for name, obj in inspect.getmembers(module):
        if name.startswith("_"):
            continue
        if inspect.isclass(obj) and obj.__module__ == module.__name__:
            assert obj.__doc__ is not None and len(obj.__doc__.strip()) > 0, f"Class {module.__name__}.{name} missing docstring"
            for mname, mobj in inspect.getmembers(obj, predicate=inspect.isfunction):
                if mname.startswith("_") and mname != "__init__":
                    continue
                assert mobj.__doc__ is not None and len(mobj.__doc__.strip()) > 0, f"Method {module.__name__}.{name}.{mname} missing docstring"
        elif inspect.isfunction(obj) and obj.__module__ == module.__name__:
            assert obj.__doc__ is not None and len(obj.__doc__.strip()) > 0, f"Function {module.__name__}.{name} missing docstring"
```

### 6.4 CLI Integration Tests (`tests/test_cli.py`)
- Test `python -m solver init --reset` executes without throwing exceptions.
- Test `python -m solver explore --count 5 --top-k 2` prints candidate summary.
- Test `python -m solver prove "P -> P"` outputs successful proof status.
- Test `python -m solver analyze` runs hypothesis deduction.
- Test `python -m solver export lean --output test.lean --stubs-only` writes valid file.
- Test `python -m solver export graph --type dependency --output test_dep.html` creates HTML file.
- Test `python -m solver docs --output-dir test_docs` generates documentation.
- Test invalid command arguments exit with non-zero exit code (1 or 2).

---

## 7. Acceptance Criteria

1. **Automated Docstring Coverage**: 100% of public modules, classes, methods, and functions in `solver` pass `test_docstrings_present`.
2. **Documentation Generation**: Running `python -m solver docs` produces valid, formatted Markdown files in `docs/api/` and a valid landing page in `docs/index.md`.
3. **CLI End-to-End Functionality**: All 7 CLI commands (`init`, `explore`, `prove`, `analyze`, `export lean`, `export graph`, `docs`) execute cleanly, respect `SolverConfig`, and display informative `--help` screens.
4. **Test Suite Coverage**: `pytest --cov=solver` passes with total line coverage $\ge 85\%$.
5. **Package Packaging**: `pyproject.toml` is syntactically valid and allows installation via `pip install -e .`.
6. **Repository Documentation**: `README.md` provides clear installation steps, CLI usage examples, and Python code snippets.

---

## 8. Risks and Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Docstring parser failure on complex docstrings** | Doc generator crashes when encountering unusual docstring formatting | Wrap section parsing in robust fallback handlers that extract unformatted text if standard block matching fails |
| **CLI test interference with `sys.exit`** | Running CLI tests kills the `pytest` runner | Use `main(argv)` returning integer status codes instead of calling `sys.exit()` directly within `main()`, and test with direct `main([...])` calls |
| **Test coverage falling below 85% requirement** | Build fails coverage threshold check | Add explicit unit tests for remaining edge cases, error handlers, and string representation methods (`__repr__`, `to_string()`) |
| **LEAN / Graph export visualization dependencies missing** | Export CLI commands fail gracefully | Include optional dependency checks with clear installation hints when `jinja2` is missing |
