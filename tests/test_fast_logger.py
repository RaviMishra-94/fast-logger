import json
import logging
import shutil
import tempfile
import time
import unittest
from pathlib import Path

from fast_logger import (
    ColorFormatter,
    FastLogger,
    JsonFormatter,
    __version__,
    get_logger,
    quick_logger,
    setup_logger,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _flush(logger_obj: FastLogger) -> None:
    """Flush all handlers (works for both sync and async modes)."""
    for handler in logger_obj.get_logger().handlers:
        if hasattr(handler, "flush"):
            handler.flush()


# ---------------------------------------------------------------------------
# Original tests (unchanged) — 16 cases
# ---------------------------------------------------------------------------

class TestFastLogger(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_name = "test_logger"

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_basic_logger_creation(self):
        logger = FastLogger(name=self.test_name, base_path=self.temp_dir)
        self.assertIsNotNone(logger.get_logger())
        self.assertEqual(logger.name, self.test_name)
        self.assertEqual(logger.level, logging.INFO)

    def test_log_file_creation(self):
        logger = FastLogger(name=self.test_name, base_path=self.temp_dir)
        logger.info("Test message")
        _flush(logger)
        log_file = Path(self.temp_dir) / "logs" / f"{self.test_name}.log"
        self.assertTrue(log_file.exists())

    def test_log_content(self):
        logger = FastLogger(name=self.test_name, base_path=self.temp_dir, console_output=False)
        logger.info("Test log message")
        _flush(logger)
        log_file = Path(self.temp_dir) / "logs" / f"{self.test_name}.log"
        content = log_file.read_text()
        self.assertIn("Test log message", content)
        self.assertIn("INFO", content)

    def test_different_log_levels(self):
        logger = FastLogger(
            name=self.test_name, base_path=self.temp_dir, level=logging.DEBUG, console_output=False
        )
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        _flush(logger)
        content = (Path(self.temp_dir) / "logs" / f"{self.test_name}.log").read_text()
        for lvl in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            self.assertIn(lvl, content)

    def test_string_level_parsing(self):
        logger = FastLogger(name=self.test_name, base_path=self.temp_dir, level="DEBUG")
        self.assertEqual(logger.level, logging.DEBUG)
        logger2 = FastLogger(name=self.test_name + "2", base_path=self.temp_dir, level="warning")
        self.assertEqual(logger2.level, logging.WARNING)

    def test_custom_log_folder(self):
        custom_folder = "custom_logs"
        logger = FastLogger(name=self.test_name, base_path=self.temp_dir, log_folder=custom_folder)
        logger.info("Test message")
        _flush(logger)
        log_file = Path(self.temp_dir) / custom_folder / f"{self.test_name}.log"
        self.assertTrue(log_file.exists())

    def test_quick_logger_function(self):
        logger = quick_logger(self.test_name)
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, self.test_name)

    def test_get_logger_function(self):
        logger = get_logger(self.test_name, base_path=self.temp_dir)
        self.assertIsInstance(logger, FastLogger)
        self.assertEqual(logger.name, self.test_name)

    def test_setup_logger_function(self):
        logger = setup_logger(self.test_name, base_path=self.temp_dir)
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, self.test_name)

    def test_no_duplicate_handlers(self):
        logger1 = FastLogger(name=self.test_name, base_path=self.temp_dir)
        count1 = len(logger1.get_logger().handlers)
        logger2 = FastLogger(name=self.test_name, base_path=self.temp_dir)
        count2 = len(logger2.get_logger().handlers)
        self.assertEqual(count1, count2)

    def test_console_output_disabled(self):
        logger = FastLogger(name=self.test_name, base_path=self.temp_dir, console_output=False)
        handlers = logger.get_logger().handlers
        self.assertEqual(len(handlers), 1)
        self.assertTrue(any(h.__class__.__name__ == "RotatingFileHandler" for h in handlers))

    def test_custom_format(self):
        logger = FastLogger(
            name=self.test_name,
            base_path=self.temp_dir,
            log_format="%(levelname)s: %(message)s",
            console_output=False,
        )
        logger.info("Test message")
        _flush(logger)
        content = (Path(self.temp_dir) / "logs" / f"{self.test_name}.log").read_text().strip()
        self.assertTrue(content.startswith("INFO: Test message"))

    def test_version_exported(self):
        self.assertIsNotNone(__version__)
        self.assertRegex(__version__, r"^\d+\.\d+\.\d+$")

    def test_propagate_false(self):
        logger = FastLogger(name=self.test_name, base_path=self.temp_dir)
        self.assertFalse(logger.get_logger().propagate)

    def test_integer_level(self):
        logger = FastLogger(name=self.test_name, base_path=self.temp_dir, level=logging.DEBUG)
        self.assertEqual(logger.level, logging.DEBUG)

    def test_exception_logging(self):
        logger = FastLogger(name=self.test_name, base_path=self.temp_dir, console_output=False)
        try:
            raise ValueError("boom")
        except ValueError:
            logger.exception("caught error")
        _flush(logger)
        content = (Path(self.temp_dir) / "logs" / f"{self.test_name}.log").read_text()
        self.assertIn("ValueError", content)
        self.assertIn("boom", content)


# ---------------------------------------------------------------------------
# New tests — Colored console output
# ---------------------------------------------------------------------------

class TestColorOutput(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_color_formatter_exported(self):
        """ColorFormatter must be importable from fast_logger."""
        self.assertTrue(issubclass(ColorFormatter, logging.Formatter))

    def test_color_formatter_contains_ansi(self):
        """ColorFormatter output should contain ANSI escape codes."""
        import io
        formatter = ColorFormatter("%(levelname)s %(message)s")
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="hello", args=(), exc_info=None,
        )
        output = formatter.format(record)
        self.assertIn("\033[", output, "Expected ANSI codes in ColorFormatter output")

    def test_color_output_flag_stored(self):
        """color_output=True should be stored (may be downgraded to False if not a TTY)."""
        logger = FastLogger(
            name="color_test", base_path=self.temp_dir, color_output=True, console_output=False
        )
        # The attribute exists; in non-TTY environments it degrades to False — that's correct.
        self.assertIsInstance(logger.color_output, bool)

    def test_no_color_in_file_logs(self):
        """Even with color_output=True, the FILE handler must write plain text."""
        logger = FastLogger(
            name="color_file_test",
            base_path=self.temp_dir,
            color_output=True,
            console_output=False,
            level="DEBUG",
        )
        logger.info("plain text in file")
        _flush(logger)
        content = (Path(self.temp_dir) / "logs" / "color_file_test.log").read_text()
        self.assertNotIn("\033[", content, "ANSI codes must not appear in log files")


# ---------------------------------------------------------------------------
# New tests — JSON log format
# ---------------------------------------------------------------------------

class TestJsonFormat(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_json_formatter_exported(self):
        self.assertTrue(issubclass(JsonFormatter, logging.Formatter))

    def test_json_formatter_valid_json(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test", level=logging.WARNING, pathname="f.py", lineno=42,
            msg="something went wrong", args=(), exc_info=None,
        )
        output = formatter.format(record)
        payload = json.loads(output)   # must not raise
        self.assertIn("message", payload)
        self.assertIn("level", payload)
        self.assertIn("timestamp", payload)

    def test_json_format_flag_writes_json_to_file(self):
        logger = FastLogger(
            name="json_test",
            base_path=self.temp_dir,
            json_format=True,
            console_output=False,
        )
        logger.warning("json warning")
        _flush(logger)
        lines = (Path(self.temp_dir) / "logs" / "json_test.log").read_text().strip().splitlines()
        self.assertTrue(len(lines) >= 1)
        payload = json.loads(lines[-1])
        self.assertEqual(payload["message"], "json warning")
        self.assertEqual(payload["level"], "WARNING")

    def test_json_format_contains_expected_keys(self):
        logger = FastLogger(
            name="json_keys_test",
            base_path=self.temp_dir,
            json_format=True,
            console_output=False,
        )
        logger.info("key check")
        _flush(logger)
        line = (Path(self.temp_dir) / "logs" / "json_keys_test.log").read_text().strip()
        payload = json.loads(line)
        for key in ("timestamp", "level", "logger", "filename", "line", "message"):
            self.assertIn(key, payload, f"Missing key: {key}")

    def test_json_format_exception_key(self):
        logger = FastLogger(
            name="json_exc_test",
            base_path=self.temp_dir,
            json_format=True,
            console_output=False,
        )
        try:
            raise RuntimeError("oops")
        except RuntimeError:
            logger.exception("caught it")
        _flush(logger)
        line = (Path(self.temp_dir) / "logs" / "json_exc_test.log").read_text().strip()
        payload = json.loads(line)
        self.assertIn("exc_info", payload)
        self.assertIn("RuntimeError", payload["exc_info"])


# ---------------------------------------------------------------------------
# New tests — Async-safe logging
# ---------------------------------------------------------------------------

class TestAsyncSafe(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _make_async_logger(self, name: str, **kwargs) -> FastLogger:
        return FastLogger(
            name=name,
            base_path=self.temp_dir,
            async_safe=True,
            console_output=False,
            **kwargs,
        )

    def test_async_safe_creates_queue_handler(self):
        """In async_safe mode the logger should have a QueueHandler attached."""
        from logging.handlers import QueueHandler
        logger = self._make_async_logger("async_queue")
        handlers = logger.get_logger().handlers
        self.assertTrue(
            any(isinstance(h, QueueHandler) for h in handlers),
            "Expected a QueueHandler in async_safe mode",
        )
        logger.stop()

    def test_async_safe_writes_to_file(self):
        """Messages must eventually appear in the log file."""
        logger = self._make_async_logger("async_write")
        logger.info("async hello")
        logger.stop()   # stop() flushes the queue
        content = (Path(self.temp_dir) / "logs" / "async_write.log").read_text()
        self.assertIn("async hello", content)

    def test_async_safe_all_levels(self):
        logger = self._make_async_logger("async_levels", level="DEBUG")
        logger.debug("d")
        logger.info("i")
        logger.warning("w")
        logger.error("e")
        logger.critical("c")
        logger.stop()
        content = (Path(self.temp_dir) / "logs" / "async_levels.log").read_text()
        for msg in ("d", "i", "w", "e", "c"):
            self.assertIn(msg, content)

    def test_async_safe_context_manager(self):
        """FastLogger should work as a context manager for clean shutdown."""
        with FastLogger(
            name="async_ctx",
            base_path=self.temp_dir,
            async_safe=True,
            console_output=False,
        ) as logger:
            logger.info("context manager works")
        # After __exit__, listener is stopped; file must contain the message.
        content = (Path(self.temp_dir) / "logs" / "async_ctx.log").read_text()
        self.assertIn("context manager works", content)

    def test_async_safe_json_combo(self):
        """async_safe + json_format should produce valid JSON in the log file."""
        with FastLogger(
            name="async_json",
            base_path=self.temp_dir,
            async_safe=True,
            json_format=True,
            console_output=False,
        ) as logger:
            logger.error("async json error")
        line = (Path(self.temp_dir) / "logs" / "async_json.log").read_text().strip()
        payload = json.loads(line)
        self.assertEqual(payload["message"], "async json error")
        self.assertEqual(payload["level"], "ERROR")

    def test_stop_is_idempotent(self):
        """Calling stop() multiple times should not raise."""
        logger = self._make_async_logger("async_stop")
        logger.stop()
        logger.stop()   # second call must be safe


if __name__ == "__main__":
    unittest.main()
