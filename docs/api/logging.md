# API Reference: `logging`

# Module `logic_prover.logging`

Logging subsystem for the logic library.

Provides centralized logger setup, log level configuration, custom output formatting,
and hierarchical logger retrieval scoped under the 'logic' namespace.

---

## Table of Contents
- [Classes](#classes)
- [Functions](#functions)

---

## Classes

### `class SolverLogFormatter(logging.Formatter)`

Custom log formatter for the logic library providing structured output.

Formats:
- Standard: "[2026-08-01 15:30:00] [INFO] [logic.prover.engine]: Proof found in 4 steps."
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

Configures the root logger for the logic library ('logic').

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

Retrieves a logger instance scoped under the 'logic_prover' namespace.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `name` | `str` | Sub-module name (e.g. 'prover.engine' or 'logic_prover.core.ast'). |

**Returns:** `logging.Logger` — logging.Logger configured to bubble events up to root 'logic_prover' logger.


---
