"""
Logging subsystem for the logic library.

Provides centralized logger setup, log level configuration, custom output formatting,
and hierarchical logger retrieval scoped under the 'logic' namespace.
"""

from __future__ import annotations
import logging
import sys
from typing import Optional, TextIO, Union
from logic_prover.config import SolverConfig


class SolverLogFormatter(logging.Formatter):
    """
    Custom log formatter for the logic library providing structured output.

    Formats:
    - Standard: "[2026-08-01 15:30:00] [INFO] [logic.prover.engine]: Proof found in 4 steps."
    - Debug: Include line numbers and thread identifiers when debug mode is enabled.
    """

    FMT_NORMAL = "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"
    FMT_DEBUG = "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d]: %(message)s"
    DATE_FMT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, debug_mode: bool = False) -> None:
        """
        Initializes the custom log formatter.

        Args:
            debug_mode: If True, includes line numbers in formatted log messages.
        """
        fmt = self.FMT_DEBUG if debug_mode else self.FMT_NORMAL
        super().__init__(fmt=fmt, datefmt=self.DATE_FMT)


def setup_logging(
    config: Optional[SolverConfig] = None,
    log_level: Optional[Union[str, int]] = None,
    log_file: Optional[str] = None,
    stream: Optional[TextIO] = None,
) -> None:
    """
    Configures the root logger for the logic library ('logic').

    Args:
        config: Optional SolverConfig instance. If provided, log level is pulled from config.log_level.
        log_level: Explicit string ('DEBUG', 'INFO', 'WARNING', 'ERROR') or logging level int.
        log_file: Optional path to write log output to disk.
        stream: Output stream for logging (defaults to sys.stderr if log_file is not specified).

    Raises:
        ValueError: If log_level is invalid.
    """
    effective_level: Union[str, int] = "INFO"
    if log_level is not None:
        effective_level = log_level
    elif config is not None:
        effective_level = getattr(config, "log_level", "INFO")

    if isinstance(effective_level, str):
        level_str = effective_level.upper()
        if not hasattr(logging, level_str):
            raise ValueError(f"Invalid log level string: '{effective_level}'")
        numeric_level = getattr(logging, level_str)
    elif isinstance(effective_level, int):
        numeric_level = effective_level
    else:
        raise ValueError(f"Invalid log level type: {type(effective_level)}")

    logger = logging.getLogger("logic_prover")
    logger.setLevel(numeric_level)

    # Clear existing handlers to allow reconfiguration without duplication
    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    debug_mode = (numeric_level == logging.DEBUG)
    formatter = SolverLogFormatter(debug_mode=debug_mode)

    if stream is not None or log_file is None:
        stream_handler = logging.StreamHandler(stream or sys.stderr)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    if log_file is not None:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """
    Retrieves a logger instance scoped under the 'logic_prover' namespace.

    Args:
        name: Sub-module name (e.g. 'prover.engine' or 'logic_prover.core.ast').

    Returns:
        logging.Logger configured to bubble events up to root 'logic_prover' logger.
    """
    if name == "logic_prover":
        return logging.getLogger("logic_prover")
    elif name.startswith("logic_prover."):
        return logging.getLogger(name)
    else:
        return logging.getLogger(f"logic_prover.{name}")

