"""
Fast Logger - A simple, no-fuss logging setup for Python applications.

This package provides a quick and easy way to set up logging in Python applications
with sensible defaults, rotating file handlers, and console output.

New in 0.3.0:
  • Secret masking              — mask_secrets=True
  • Variable watch & diff       — logger.watch(), logger.diff()
  • System telemetry            — logger.sysinfo()
  • AI Panels & FastAPI         — logger.panel(), FastAPILoggerMiddleware

New in 0.2.0:
  • Optional rich support         — pip install "python-fast-logger[rich]"
  • Context bounding            — logger.bind(request_id="123")
  • Execution timing            — with logger.timer("task")
  • Function tracing            — @logger.trace()
  • Table formatting            — logger.table(data)
  • Colored console output      — pass color_output=True to FastLogger
  • Structured JSON log format  — pass json_format=True to FastLogger
  • Async-safe logging          — pass async_safe=True to FastLogger

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
        backup_count=5,
        color_output=True,    # colourised console
        json_format=True,     # structured JSON logs
        async_safe=True,      # non-blocking via QueueHandler
        mask_secrets=True,    # Auto-redact API keys and passwords
    )
    logger.info("Hello, world!")
"""

from .core import (
    ColorFormatter,
    FastLogger,
    JsonFormatter,
    get_logger,
    quick_logger,
    setup_logger,
)

__version__ = "0.3.0"
__author__ = "Ravi Mishra"
__email__ = "ravi@iscodesearch.com"

__all__ = [
    "FastLogger",
    "ColorFormatter",
    "JsonFormatter",
    "setup_logger",
    "get_logger",
    "quick_logger",
    "__version__",
]
