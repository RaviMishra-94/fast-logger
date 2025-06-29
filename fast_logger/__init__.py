"""
Fast Logger - A simple, no-fuss logging setup for Python applications.

This package provides a quick and easy way to set up logging in Python applications
with sensible defaults, rotating file handlers, and console output.

Basic usage:
    from fast_logger import get_logger

    logger = get_logger("my_app")
    logger.info("Hello, world!")

Quick setup:
    from fast_logger import quick_logger

    logger = quick_logger("my_app")
    logger.info("Hello, world!")

Advanced usage:
    from fast_logger import FastLogger

    logger = FastLogger(
        name="my_app",
        level="DEBUG",
        max_file_size_mb=100,
        backup_count=5
    )
    logger.info("Hello, world!")
"""

from .core import FastLogger, setup_logger, get_logger, quick_logger

__version__ = "0.1.0"
__author__ = "Ravi Mishra"
__email__ = "ravi@paisafintech.com"

__all__ = [
    "FastLogger",
    "setup_logger",
    "get_logger",
    "quick_logger",
    "__version__",
]