"""
Unit tests for the logging subsystem (logic/utils/logging.py).
"""

from __future__ import annotations
import io
import logging
import os
import tempfile
import unittest

from logic.config import SolverConfig
from logic.utils.logging import SolverLogFormatter, setup_logging, get_logger


class TestSolverLogging(unittest.TestCase):
    """Test suite for logging configuration, formatting, and scoping."""

    def tearDown(self) -> None:
        """Reset root logic logger handlers after each test."""
        logger = logging.getLogger("logic")
        for h in list(logger.handlers):
            h.close()
            logger.removeHandler(h)
        logger.setLevel(logging.NOTSET)

    def test_setup_logging_levels(self) -> None:
        """Test setting valid log levels via setup_logging."""
        setup_logging(log_level="DEBUG")
        logger = logging.getLogger("logic")
        self.assertEqual(logger.level, logging.DEBUG)

        setup_logging(log_level="WARNING")
        self.assertEqual(logger.level, logging.WARNING)

        setup_logging(log_level=logging.ERROR)
        self.assertEqual(logger.level, logging.ERROR)

    def test_setup_logging_with_config(self) -> None:
        """Test setting log level via SolverConfig."""
        config = SolverConfig(log_level="DEBUG")
        setup_logging(config=config)
        logger = logging.getLogger("logic")
        self.assertEqual(logger.level, logging.DEBUG)

    def test_setup_logging_invalid_level(self) -> None:
        """Test that invalid log levels raise ValueError."""
        with self.assertRaises(ValueError):
            setup_logging(log_level="INVALID_LEVEL")

        with self.assertRaises(ValueError):
            setup_logging(log_level=12.34)  # type: ignore

    def test_logic_log_formatter_normal(self) -> None:
        """Test SolverLogFormatter standard formatting mode."""
        formatter = SolverLogFormatter(debug_mode=False)
        record = logging.LogRecord(
            name="logic.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Hello world",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        self.assertIn("[INFO]", formatted)
        self.assertIn("[logic.test]", formatted)
        self.assertIn("Hello world", formatted)
        self.assertNotIn("test.py", formatted)
        self.assertNotIn(":42]", formatted)

    def test_logic_log_formatter_debug(self) -> None:
        """Test SolverLogFormatter debug formatting mode."""
        formatter = SolverLogFormatter(debug_mode=True)
        record = logging.LogRecord(
            name="logic.test",
            level=logging.DEBUG,
            pathname="test.py",
            lineno=42,
            msg="Debug trace",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        self.assertIn("[DEBUG]", formatted)
        self.assertIn("[logic.test:42]", formatted)
        self.assertIn("Debug trace", formatted)

    def test_get_logger_scoping(self) -> None:
        """Test logger namespace prefixing in get_logger."""
        log1 = get_logger("prover.engine")
        self.assertEqual(log1.name, "logic.prover.engine")

        log2 = get_logger("logic.core.ast")
        self.assertEqual(log2.name, "logic.core.ast")

        log3 = get_logger("logic")
        self.assertEqual(log3.name, "logic")

    def test_logging_stream_output(self) -> None:
        """Test logging output captured in stream."""
        stream = io.StringIO()
        setup_logging(log_level="INFO", stream=stream)

        logger = get_logger("test_module")
        logger.info("Test message stream")

        output = stream.getvalue()
        self.assertIn("[INFO]", output)
        self.assertIn("[logic.test_module]", output)
        self.assertIn("Test message stream", output)

    def test_logging_file_output(self) -> None:
        """Test logging output saved to disk file."""
        with tempfile.NamedTemporaryFile("w+", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            setup_logging(log_level="INFO", log_file=tmp_path)
            logger = get_logger("file_test")
            logger.info("Message for file")

            # Flush and close handlers so file lock is released on Windows
            for h in list(logging.getLogger("logic").handlers):
                h.flush()
                h.close()
                logging.getLogger("logic").removeHandler(h)

            with open(tmp_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("Message for file", content)
            self.assertIn("[logic.file_test]", content)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
