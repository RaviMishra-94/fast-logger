import unittest
import tempfile
import shutil
import logging
from pathlib import Path
from fast_logger import FastLogger, quick_logger, get_logger, setup_logger


class TestFastLogger(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_name = "test_logger"

    def tearDown(self):
        """Clean up after tests."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_basic_logger_creation(self):
        """Test basic logger creation."""
        logger = FastLogger(
            name=self.test_name,
            base_path=self.temp_dir
        )

        self.assertIsNotNone(logger.get_logger())
        self.assertEqual(logger.name, self.test_name)
        self.assertEqual(logger.level, logging.INFO)

    def test_log_file_creation(self):
        """Test that log files are created."""
        logger = FastLogger(
            name=self.test_name,
            base_path=self.temp_dir
        )

        logger.info("Test message")

        # Force flush to ensure file is written
        for handler in logger.get_logger().handlers:
            if hasattr(handler, 'flush'):
                handler.flush()

        log_file = Path(self.temp_dir) / "logs" / f"{self.test_name}.log"
        self.assertTrue(log_file.exists())

    def test_log_content(self):
        """Test that log content is written correctly."""
        logger = FastLogger(
            name=self.test_name,
            base_path=self.temp_dir,
            console_output=False  # Only file output for testing
        )

        test_message = "Test log message"
        logger.info(test_message)

        # Force flush to ensure file is written
        for handler in logger.get_logger().handlers:
            if hasattr(handler, 'flush'):
                handler.flush()

        log_file = Path(self.temp_dir) / "logs" / f"{self.test_name}.log"
        with open(log_file, 'r') as f:
            content = f.read()

        self.assertIn(test_message, content)
        self.assertIn("INFO", content)

    def test_different_log_levels(self):
        """Test different logging levels."""
        logger = FastLogger(
            name=self.test_name,
            base_path=self.temp_dir,
            level=logging.DEBUG,
            console_output=False
        )

        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")

        # Force flush to ensure file is written
        for handler in logger.get_logger().handlers:
            if hasattr(handler, 'flush'):
                handler.flush()

        log_file = Path(self.temp_dir) / "logs" / f"{self.test_name}.log"
        with open(log_file, 'r') as f:
            content = f.read()

        self.assertIn("DEBUG", content)
        self.assertIn("INFO", content)
        self.assertIn("WARNING", content)
        self.assertIn("ERROR", content)
        self.assertIn("CRITICAL", content)

    def test_string_level_parsing(self):
        """Test string level parsing."""
        logger = FastLogger(
            name=self.test_name,
            base_path=self.temp_dir,
            level="DEBUG"
        )

        self.assertEqual(logger.level, logging.DEBUG)

        logger = FastLogger(
            name=self.test_name + "2",
            base_path=self.temp_dir,
            level="warning"
        )

        self.assertEqual(logger.level, logging.WARNING)

    def test_custom_log_folder(self):
        """Test custom log folder."""
        custom_folder = "custom_logs"
        logger = FastLogger(
            name=self.test_name,
            base_path=self.temp_dir,
            log_folder=custom_folder
        )

        logger.info("Test message")

        # Force flush to ensure file is written
        for handler in logger.get_logger().handlers:
            if hasattr(handler, 'flush'):
                handler.flush()

        log_file = Path(self.temp_dir) / custom_folder / f"{self.test_name}.log"
        self.assertTrue(log_file.exists())

    def test_quick_logger_function(self):
        """Test quick_logger convenience function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # This is tricky to test since quick_logger uses caller's directory
            # We'll just test that it returns a logger
            logger = quick_logger(self.test_name)
            self.assertIsInstance(logger, logging.Logger)
            self.assertEqual(logger.name, self.test_name)

    def test_get_logger_function(self):
        """Test get_logger convenience function."""
        logger = get_logger(self.test_name, base_path=self.temp_dir)
        self.assertIsInstance(logger, FastLogger)
        self.assertEqual(logger.name, self.test_name)

    def test_setup_logger_function(self):
        """Test setup_logger convenience function."""
        logger = setup_logger(self.test_name, base_path=self.temp_dir)
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, self.test_name)

    def test_no_duplicate_handlers(self):
        """Test that creating the same logger twice doesn't duplicate handlers."""
        logger1 = FastLogger(name=self.test_name, base_path=self.temp_dir)
        initial_handler_count = len(logger1.get_logger().handlers)

        logger2 = FastLogger(name=self.test_name, base_path=self.temp_dir)
        final_handler_count = len(logger2.get_logger().handlers)

        self.assertEqual(initial_handler_count, final_handler_count)

    def test_console_output_disabled(self):
        """Test logger with console output disabled."""
        logger = FastLogger(
            name=self.test_name,
            base_path=self.temp_dir,
            console_output=False
        )

        # Should have only file handler
        handlers = logger.get_logger().handlers
        self.assertEqual(len(handlers), 1)
        self.assertTrue(any(handler.__class__.__name__ == 'RotatingFileHandler'
                            for handler in handlers))

    def test_custom_format(self):
        """Test custom log format."""
        custom_format = "%(levelname)s: %(message)s"
        logger = FastLogger(
            name=self.test_name,
            base_path=self.temp_dir,
            log_format=custom_format,
            console_output=False
        )

        logger.info("Test message")

        # Force flush to ensure file is written
        for handler in logger.get_logger().handlers:
            if hasattr(handler, 'flush'):
                handler.flush()

        log_file = Path(self.temp_dir) / "logs" / f"{self.test_name}.log"
        with open(log_file, 'r') as f:
            content = f.read().strip()

        # Should match our custom format
        self.assertTrue(content.startswith("INFO: Test message"))


if __name__ == '__main__':
    unittest.main()