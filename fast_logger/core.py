"""
Fast Logger - A simple, no-fuss logging setup for Python applications.

New in 0.2.0:
  • Colored console output      (color_output=True)
  • Structured JSON log format  (json_format=True)
  • Async-safe logging          (async_safe=True)  — non-blocking via QueueHandler
"""

import json
import logging
import logging.handlers
import sys
import threading
from datetime import datetime, timezone
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from pathlib import Path
from queue import Queue
from typing import Any, Optional, Union

# ---------------------------------------------------------------------------
# ANSI color codes (no third-party deps)
# ---------------------------------------------------------------------------

_RESET = "\033[0m"
_BOLD = "\033[1m"

_LEVEL_COLORS: dict[int, str] = {
    logging.DEBUG: "\033[36m",       # Cyan
    logging.INFO: "\033[32m",        # Green
    logging.WARNING: "\033[33m",     # Yellow
    logging.ERROR: "\033[31m",       # Red
    logging.CRITICAL: "\033[35m",    # Magenta
}


class ColorFormatter(logging.Formatter):
    """Formatter that wraps the level name (and optionally the whole line) in ANSI color."""

    def format(self, record: logging.LogRecord) -> str:
        color = _LEVEL_COLORS.get(record.levelno, "")
        record = logging.makeLogRecord(record.__dict__)  # shallow copy
        record.levelname = f"{color}{_BOLD}{record.levelname}{_RESET}"
        formatted = super().format(record)
        # Colorize the whole output line for visual impact
        return f"{color}{formatted}{_RESET}"


# ---------------------------------------------------------------------------
# JSON formatter
# ---------------------------------------------------------------------------

class JsonFormatter(logging.Formatter):
    """Emits each log record as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "filename": record.filename,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        if record.stack_info:
            payload["stack_info"] = self.formatStack(record.stack_info)

        # Merge any extra fields the caller passed in
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "lineno", "funcName", "created",
                "msecs", "relativeCreated", "thread", "threadName",
                "processName", "process", "exc_info", "exc_text",
                "stack_info", "message", "taskName",
            }:
                try:
                    json.dumps(value)   # only include JSON-serialisable extras
                    payload[key] = value
                except (TypeError, ValueError):
                    payload[key] = str(value)

        return json.dumps(payload, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Main FastLogger class
# ---------------------------------------------------------------------------

class FastLogger:
    """
    A zero-fuss, production-ready logger with:
      • RotatingFileHandler (file rotation out of the box)
      • Optional colored console output   (color_output=True)
      • Optional JSON structured logging  (json_format=True)
      • Optional async-safe mode          (async_safe=True)
    """

    def __init__(
        self,
        name: str,
        level: Union[int, str] = logging.INFO,
        log_folder: str = "logs",
        max_file_size_mb: int = 50,
        backup_count: int = 3,
        log_format: Optional[str] = None,
        console_output: bool = True,
        base_path: Optional[str] = None,
        # --- new in 0.2.0 ---
        color_output: bool = False,
        json_format: bool = False,
        async_safe: bool = False,
    ):
        """
        Initialise FastLogger.

        Args:
            name:             Logger name (also used as the log filename).
            level:            Logging level — string ("DEBUG") or int (logging.DEBUG).
            log_folder:       Sub-directory for log files.
            max_file_size_mb: Max size per log file before rotation.
            backup_count:     Number of rotated backup files to keep.
            log_format:       Custom ``logging.Formatter`` format string.
                              Ignored when ``json_format=True``.
            console_output:   Attach a StreamHandler to stdout.
            base_path:        Root directory for log files.
                              Defaults to the calling script's directory.
            color_output:     Colorise console output using ANSI codes.
                              Automatically disabled when stdout is not a TTY.
            json_format:      Emit structured JSON records instead of plain text.
                              Applies to both file and console handlers.
            async_safe:       Route all log calls through a ``QueueHandler`` /
                              ``QueueListener`` so that I/O never blocks the
                              calling thread / async event loop.
        """
        self.name = name
        self.level = self._parse_level(level)
        self.log_folder = log_folder
        self.max_file_size_mb = max_file_size_mb
        self.backup_count = backup_count
        self.console_output = console_output
        self.base_path = base_path
        self.color_output = color_output and sys.stdout.isatty()
        self.json_format = json_format
        self.async_safe = async_safe

        self.log_format = log_format or (
            "%(asctime)s - %(name)s [%(filename)s:%(lineno)d] - "
            "%(levelname)s - %(message)s"
        )

        self._logger: Optional[logging.Logger] = None
        self._queue: Optional[Queue[Any]] = None
        self._listener: Optional[QueueListener] = None
        self._setup_logger()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_level(level: Union[int, str]) -> int:
        if isinstance(level, str):
            return getattr(logging, level.upper(), logging.INFO)
        return level

    def _get_log_directory(self) -> Path:
        if self.base_path:
            base = Path(self.base_path)
        else:
            import inspect

            current_dir = Path(__file__).parent
            for frame_info in inspect.stack():
                caller_file = Path(frame_info.filename)
                if caller_file.parent != current_dir:
                    base = caller_file.parent if caller_file.exists() else Path.cwd()
                    break
            else:
                base = Path.cwd()

        log_dir = base / self.log_folder
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    def _make_formatter(self, *, color: bool = False) -> logging.Formatter:
        """Return the appropriate formatter instance."""
        if self.json_format:
            return JsonFormatter()
        if color and self.color_output:
            return ColorFormatter(self.log_format)
        return logging.Formatter(self.log_format)

    def _setup_logger(self) -> None:
        self._logger = logging.getLogger(self.name)
        self._logger.handlers.clear()
        self._logger.setLevel(self.level)
        self._logger.propagate = False

        # Build the real I/O handlers
        real_handlers: list[logging.Handler] = []

        # File handler
        log_dir = self._get_log_directory()
        log_file = log_dir / f"{self.name}.log"
        file_handler = RotatingFileHandler(
            str(log_file),
            maxBytes=self.max_file_size_mb * 1024 * 1024,
            backupCount=self.backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(self.level)
        file_handler.setFormatter(self._make_formatter(color=False))
        real_handlers.append(file_handler)

        # Console handler
        if self.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.level)
            console_handler.setFormatter(self._make_formatter(color=True))
            real_handlers.append(console_handler)

        if self.async_safe:
            # Route all records through an in-process queue so the calling
            # thread is never blocked by file/network I/O.
            self._queue: Queue[Any] = Queue(maxsize=-1)  # unbounded
            queue_handler = QueueHandler(self._queue)
            queue_handler.setLevel(self.level)
            self._logger.addHandler(queue_handler)

            self._listener = QueueListener(
                self._queue,
                *real_handlers,
                respect_handler_level=True,
            )
            self._listener.start()
        else:
            for handler in real_handlers:
                self._logger.addHandler(handler)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_logger(self) -> logging.Logger:
        """Return the underlying :class:`logging.Logger`."""
        assert self._logger is not None
        return self._logger

    def stop(self) -> None:
        """
        Gracefully shut down the async listener (only needed when
        ``async_safe=True``).  Call this at application exit.
        """
        if self._listener is not None:
            self._listener.stop()

    # Convenience log-level methods -----------------------------------

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        if self._logger:
            self._logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        if self._logger:
            self._logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        if self._logger:
            self._logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        if self._logger:
            self._logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        if self._logger:
            self._logger.critical(message, *args, **kwargs)

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        if self._logger:
            self._logger.exception(message, *args, **kwargs)

    # Context manager support (useful for async_safe=True) ------------

    def __enter__(self) -> "FastLogger":
        return self

    def __exit__(self, *_: Any) -> None:
        self.stop()


# ---------------------------------------------------------------------------
# Module-level convenience functions (unchanged public surface)
# ---------------------------------------------------------------------------

def setup_logger(name: str, **kwargs: Any) -> logging.Logger:
    """
    One-liner: return a configured :class:`logging.Logger`.

    Args:
        name:     Logger name.
        **kwargs: Forwarded to :class:`FastLogger`.
    """
    return FastLogger(name, **kwargs).get_logger()


def get_logger(name: str, **kwargs: Any) -> FastLogger:
    """
    Return a :class:`FastLogger` instance (fluent interface).

    Args:
        name:     Logger name.
        **kwargs: Forwarded to :class:`FastLogger`.
    """
    return FastLogger(name, **kwargs)


def quick_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Minimal one-liner — sensible defaults, no config needed.

    Args:
        name:  Logger name.
        level: Logging level string.
    """
    return setup_logger(name, level=level)
