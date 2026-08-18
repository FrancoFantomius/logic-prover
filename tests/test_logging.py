"""
Unit tests for the logging subsystem (logic_prover.logging).
"""

from __future__ import annotations
import io
import logging
import unittest

from logic_prover.config import SolverConfig
from logic_prover.logging import SolverLogFormatter, get_logger, setup_logging


class TestLoggingSubsystem(unittest.TestCase):
    """Test suite for setup_logging, get_logger, and SolverLogFormatter."""

    def test_get_logger_naming(self) -> None:
        """Test that get_logger produces correctly scoped logger names."""
        log1 = get_logger("logic_prover")
        self.assertEqual(log1.name, "logic_prover")

        log2 = get_logger("logic_prover.cli")
        self.assertEqual(log2.name, "logic_prover.cli")

        log3 = get_logger("prover.engine")
        self.assertEqual(log3.name, "logic_prover.prover.engine")

    def test_formatter_normal_and_debug(self) -> None:
        """Test SolverLogFormatter output format in standard and debug modes."""
        record = logging.LogRecord(
            name="logic_prover.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Hello world",
            args=(),
            exc_info=None,
        )

        fmt_normal = SolverLogFormatter(debug_mode=False)
        formatted_normal = fmt_normal.format(record)
        self.assertIn("[INFO]", formatted_normal)
        self.assertIn("[logic_prover.test]: Hello world", formatted_normal)

        fmt_debug = SolverLogFormatter(debug_mode=True)
        formatted_debug = fmt_debug.format(record)
        self.assertIn("[logic_prover.test:42]: Hello world", formatted_debug)

    def test_setup_logging_stream(self) -> None:
        """Test setup_logging with an in-memory stream."""
        stream = io.StringIO()
        setup_logging(log_level="DEBUG", stream=stream)

        logger = get_logger("test_stream")
        logger.debug("Debug test message")

        out = stream.getvalue()
        self.assertIn("Debug test message", out)
        self.assertIn("[DEBUG]", out)

    def test_setup_logging_with_config(self) -> None:
        """Test setup_logging using SolverConfig instance."""
        config = SolverConfig()
        stream = io.StringIO()
        setup_logging(config=config, stream=stream)

        logger = get_logger("test_config")
        logger.info("Config test message")

        out = stream.getvalue()
        self.assertIn("Config test message", out)

    def test_setup_logging_invalid_level(self) -> None:
        """Test setup_logging with an invalid level raises ValueError."""
        with self.assertRaises(ValueError):
            setup_logging(log_level="INVALID_LEVEL")


if __name__ == "__main__":
    unittest.main()
