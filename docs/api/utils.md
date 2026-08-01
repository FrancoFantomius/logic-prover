# API Reference: `utils`

# Module `solver.utils.doc_generator`

Automated reflection and AST documentation generator for the solver library.

Extracts docstrings, type annotations, and signatures from Python source modules
and formats them into Markdown documentation files.

---

## Table of Contents
- [Classes](#classes)
- [Functions](#functions)

---

## Classes

### `class ParamDoc`

Represents a parameter documentation entry.

### `class ReturnDoc`

Represents a return value documentation entry.

### `class ExceptionDoc`

Represents an exception documentation entry.

### `class FunctionDoc`

Represents a documented standalone function or method.

### `class ClassDoc`

Represents a documented class.

### `class ModuleDoc`

Represents a documented Python module.

---

## Functions

### `def parse_google_docstring(docstring: Optional[str]) -> Tuple[str, str, List[ParamDoc], Optional[ReturnDoc], List[ExceptionDoc]]`

Parses a Google-style docstring into structured components.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `docstring` | `Optional[str]` | Raw docstring text. |

**Returns:** `Tuple[str, str, List[ParamDoc], Optional[ReturnDoc], List[ExceptionDoc]]` — Tuple containing (summary, detailed_description, params_list, return_info, raises_list).

### `def extract_docstrings_from_module(module_path: str) -> ModuleDoc`

Inspects docstrings and signatures from a Python module file using AST and reflection.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `module_path` | `str` | Absolute or relative file path to a .py file (e.g. 'solver/core/ast.py'). |

**Returns:** `ModuleDoc` — ModuleDoc containing parsed classes, functions, signatures, and docstring sections.

**Raises:**
- `FileNotFoundError`: If module_path does not exist.
- `SyntaxError`: If module_path contains invalid Python syntax.

### `def render_markdown_module(module_doc: ModuleDoc) -> str`

Renders a ModuleDoc object into GitHub-flavored Markdown text.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `module_doc` | `ModuleDoc` | ModuleDoc instance. |

**Returns:** `str` — Formatted Markdown string.

### `def build_markdown_docs(source_dir: str, output_docs_dir: str) -> Dict[str, str]`

Scans the source codebase, extracts docstrings from all modules, and writes Markdown documentation.

Generates:
- docs/api/<submodule_group>.md (e.g. docs/api/core.md, docs/api/prover.md)
- docs/index.md (Landing page with module links and summary tables)

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `source_dir` | `str` | Root package directory to scan (default 'solver'). |
| `output_docs_dir` | `str` | Target output directory for markdown files (default 'docs'). |

**Returns:** `Dict[str, str]` — Dictionary mapping created file paths to rendered content length.


---

# Module `solver.utils.logging`

Logging subsystem for the solver library.

Provides centralized logger setup, log level configuration, custom output formatting,
and hierarchical logger retrieval scoped under the 'solver' namespace.

---

## Table of Contents
- [Classes](#classes)
- [Functions](#functions)

---

## Classes

### `class SolverLogFormatter(logging.Formatter)`

Custom log formatter for the solver library providing structured output.

Formats:
- Standard: "[2026-08-01 15:30:00] [INFO] [solver.prover.engine]: Proof found in 4 steps."
- Debug: Include line numbers and thread identifiers when debug mode is enabled.

#### Methods

##### `def __init__(self, debug_mode: bool) -> None`

Initializes the custom log formatter.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `debug_mode` | `bool` | If True, includes line numbers in formatted log messages. |

**Returns:** `None`

---

## Functions

### `def setup_logging(config: Optional[SolverConfig], log_level: Optional[Union[str, int]], log_file: Optional[str], stream: Optional[TextIO]) -> None`

Configures the root logger for the solver library ('solver').

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `config` | `Optional[SolverConfig]` | Optional SolverConfig instance. If provided, log level is pulled from config.log_level. |
| `log_level` | `Optional[Union[str, int]]` | Explicit string ('DEBUG', 'INFO', 'WARNING', 'ERROR') or logging level int. |
| `log_file` | `Optional[str]` | Optional path to write log output to disk. |
| `stream` | `Optional[TextIO]` | Output stream for logging (defaults to sys.stderr if log_file is not specified). |

**Returns:** `None`

**Raises:**
- `ValueError`: If log_level is invalid.

### `def get_logger(name: str) -> logging.Logger`

Retrieves a logger instance scoped under the 'solver' namespace.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `name` | `str` | Sub-module name (e.g. 'prover.engine' or 'solver.core.ast'). |

**Returns:** `logging.Logger` — logging.Logger configured to bubble events up to root 'solver' logger.


---
