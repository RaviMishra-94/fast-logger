"""
Fast Logger - A simple, no-fuss logging setup for Python applications
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Union


class FastLogger:
    """A simple logger setup with sensible defaults."""

    def __init__(self,
                 name: str,
                 level: Union[int, str] = logging.INFO,
                 log_folder: str = 'logs',
                 max_file_size_mb: int = 50,
                 backup_count: int = 3,
                 log_format: Optional[str] = None,
                 console_output: bool = True,
                 base_path: Optional[str] = None):
        """
        Initialize FastLogger with configuration.

        Args:
            name: Logger name (will be used as filename)
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_folder: Directory name for log files
            max_file_size_mb: Maximum size of each log file in MB
            backup_count: Number of backup files to keep
            log_format: Custom log format string
            console_output: Whether to output to console
            base_path: Base directory for logs (defaults to caller's directory)
        """
        self.name = name
        self.level = self._parse_level(level)
        self.log_folder = log_folder
        self.max_file_size_mb = max_file_size_mb
        self.backup_count = backup_count
        self.console_output = console_output
        self.base_path = base_path

        self.log_format = log_format or (
            '%(asctime)s - %(name)s [%(filename)s:%(lineno)d] - '
            '%(levelname)s - %(message)s'
        )

        self._logger = None
        self._setup_logger()

    @staticmethod
    def _parse_level(level: Union[int, str]) -> int:
        """Parse logging level from string or int."""
        if isinstance(level, str):
            return getattr(logging, level.upper(), logging.INFO)
        return level

    def _get_log_directory(self) -> Path:
        """Get the log directory path."""
        if self.base_path:
            base = Path(self.base_path)
        else:
            import inspect
            frame = inspect.currentframe()
            try:
                caller_frame = frame.f_back.f_back
                caller_file = caller_frame.f_code.co_filename
                base = Path(caller_file).parent
            finally:
                del frame

        log_dir = base / self.log_folder
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    def _setup_logger(self):
        """Set up the logger with file and console handlers."""
        if self.name in logging.Logger.manager.loggerDict:
            existing_logger = logging.getLogger(self.name)
            if existing_logger.handlers:
                self._logger = existing_logger
                return

        self._logger = logging.getLogger(self.name)
        self._logger.setLevel(self.level)

        self._logger.handlers.clear()

        formatter = logging.Formatter(self.log_format)

        log_dir = self._get_log_directory()
        log_file = log_dir / f"{self.name}.log"

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=self.max_file_size_mb * 1024 * 1024,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(self.level)
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)

        if self.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.level)
            console_handler.setFormatter(formatter)
            self._logger.addHandler(console_handler)

        self._logger.propagate = False

    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance."""
        return self._logger

    def debug(self, message: str, *args, **kwargs):
        """Log a debug message."""
        self._logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        """Log an info message."""
        self._logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """Log a warning message."""
        self._logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """Log an error message."""
        self._logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        """Log a critical message."""
        self._logger.critical(message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs):
        """Log an exception with traceback."""
        self._logger.exception(message, *args, **kwargs)

def setup_logger(name: str, **kwargs) -> logging.Logger:
    """
    Quick setup function for backward compatibility and convenience.

    Args:
        name: Logger name
        **kwargs: Additional arguments passed to FastLogger

    Returns:
        Configured logger instance
    """
    fast_logger = FastLogger(name, **kwargs)
    return fast_logger.get_logger()

def get_logger(name: str, **kwargs) -> FastLogger:
    """
    Get a FastLogger instance with fluent interface.

    Args:
        name: Logger name
        **kwargs: Additional arguments passed to FastLogger

    Returns:
        FastLogger instance
    """
    return FastLogger(name, **kwargs)

def quick_logger(name: str, level: str = 'INFO') -> logging.Logger:
    """
    Super quick logger setup with minimal configuration.

    Args:
        name: Logger name
        level: Logging level

    Returns:
        Configured logger instance
    """
    return setup_logger(name, level=level)