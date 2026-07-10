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
import time
import gzip
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import wraps
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from pathlib import Path
from queue import Queue
from typing import Any, Callable, Optional, Union, Generator

try:
    from rich.console import Console
    from rich.traceback import install as install_rich_traceback
    from rich.panel import Panel
    import rich.pretty

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from .formatters import format_sql, format_json, format_http
from .masking import mask_secrets_in_string
from .sysinfo import get_system_info

try:
    from .fastapi import request_id_ctx_var

    HAS_CONTEXT_VAR = True
except ImportError:
    HAS_CONTEXT_VAR = False


# ---------------------------------------------------------------------------
# ANSI color codes (no third-party deps)
# ---------------------------------------------------------------------------

_RESET = "\033[0m"
_BOLD = "\033[1m"

_LEVEL_COLORS: dict[int, str] = {
    logging.DEBUG: "\033[36m",  # Cyan
    logging.INFO: "\033[32m",  # Green
    logging.WARNING: "\033[33m",  # Yellow
    logging.ERROR: "\033[31m",  # Red
    logging.CRITICAL: "\033[35m",  # Magenta
}

_LEVEL_ICONS: dict[int, str] = {
    logging.DEBUG: "🚀",
    logging.INFO: "✓",
    logging.WARNING: "⚠",
    logging.ERROR: "✗",
    logging.CRITICAL: "🔥",
}


class ColorFormatter(logging.Formatter):
    """Formatter that wraps the level name (and optionally the whole line) in ANSI color."""

    def format(self, record: logging.LogRecord) -> str:
        color = _LEVEL_COLORS.get(record.levelno, "")
        icon = _LEVEL_ICONS.get(record.levelno, "")
        record = logging.makeLogRecord(record.__dict__)  # shallow copy
        record.levelname = f"{color}{_BOLD}{icon} {record.levelname}{_RESET}"
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
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "funcName": record.funcName,
            "threadName": record.threadName,
            "process": record.process,
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
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "exc_info",
                "exc_text",
                "stack_info",
                "message",
                "taskName",
            }:
                try:
                    json.dumps(value)  # only include JSON-serialisable extras
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
        # --- new in 0.3.0 ---
        mask_secrets: bool = False,
        # --- new in 0.4.0 / 0.5.0 ---
        compress_backups: bool = False,
        pretty_exceptions: bool = True,
        # Internal params for context binding
        _existing_logger: Optional[logging.Logger] = None,
        _bound_kwargs: Optional[dict[str, Any]] = None,
        _listener: Optional[QueueListener] = None,
    ):
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
        self.mask_secrets = mask_secrets
        self.compress_backups = compress_backups
        self.pretty_exceptions = pretty_exceptions

        if self.pretty_exceptions and RICH_AVAILABLE:
            install_rich_traceback(show_locals=True)

        self._bound_kwargs = _bound_kwargs or {}

        # The base logging string, including some extra diagnostic info
        # (funcName, threadName, process) for debugging.
        self.log_format = log_format or (
            "%(asctime)s - %(name)s [%(filename)s:%(lineno)d] "
            "[P:%(process)d T:%(threadName)s] - %(levelname)s - %(message)s"
        )

        self._logger: Optional[logging.Logger] = None
        self._queue: Optional[Queue[Any]] = None
        self._listener: Optional[QueueListener] = _listener

        if _existing_logger:
            self._logger = _existing_logger
        else:
            self._setup_logger()

        # If Rich is available and we're writing to a TTY console in color mode,
        # enable pretty printing and traceback handling globally.
        if RICH_AVAILABLE and self.color_output and not _existing_logger:
            install_rich_traceback(show_locals=False)
            rich.pretty.install()

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

        real_handlers: list[logging.Handler] = []

        log_dir = self._get_log_directory()
        log_file = log_dir / f"{self.name}.log"
        file_handler = RotatingFileHandler(
            str(log_file),
            maxBytes=self.max_file_size_mb * 1024 * 1024,
            backupCount=self.backup_count,
            encoding="utf-8",
        )
        
        if self.compress_backups:
            def _gzip_rotator(source: str, dest: str) -> None:
                with open(source, 'rb') as f_in:
                    with gzip.open(dest, 'wb') as f_out:
                        f_out.writelines(f_in)
                os.remove(source)

            def _gzip_namer(default_name: str) -> str:
                return default_name + ".gz"
                
            file_handler.rotator = _gzip_rotator
            file_handler.namer = _gzip_namer

        file_handler.setLevel(self.level)
        file_handler.setFormatter(self._make_formatter(color=False))
        real_handlers.append(file_handler)

        if self.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.level)
            console_handler.setFormatter(self._make_formatter(color=True))
            real_handlers.append(console_handler)

        if self.async_safe:
            self._queue = Queue(maxsize=-1)  # unbounded
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

    def _log(self, level_method: str, message: str, *args: Any, **kwargs: Any) -> None:
        if not self._logger:
            return

        extra = kwargs.pop("extra", {})
        if self._bound_kwargs:
            extra.update(self._bound_kwargs)

        if HAS_CONTEXT_VAR:
            req_id = request_id_ctx_var.get("")
            if req_id:
                extra["correlation_id"] = req_id

        if extra:
            kwargs["extra"] = extra

            # If not using JSON format, we might want to append bound context
            # to the string output so the user sees it in the console.
            if not self.json_format and extra:
                context_str = " | ".join(f"{k}={v}" for k, v in extra.items())
                message = f"{message} [{context_str}]"

        if self.mask_secrets:
            message = mask_secrets_in_string(message)

        getattr(self._logger, level_method)(message, *args, **kwargs)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_logger(self) -> logging.Logger:
        """Return the underlying :class:`logging.Logger`."""
        assert self._logger is not None
        return self._logger

    def stop(self) -> None:
        """
        Gracefully shut down the async listener.
        """
        if (
            self._listener is not None
            and getattr(self._listener, "_thread", None) is not None
        ):
            self._listener.stop()
            self._listener = None

    def bind(self, **kwargs: Any) -> "FastLogger":
        """
        Returns a new FastLogger instance that automatically injects the provided
        kwargs into every log record (useful for request_id, user_id, etc).
        """
        new_kwargs = {**self._bound_kwargs, **kwargs}
        return FastLogger(
            name=self.name,
            level=self.level,
            log_folder=self.log_folder,
            max_file_size_mb=self.max_file_size_mb,
            backup_count=self.backup_count,
            log_format=self.log_format,
            console_output=self.console_output,
            base_path=self.base_path,
            color_output=self.color_output,
            json_format=self.json_format,
            async_safe=self.async_safe,
            mask_secrets=self.mask_secrets,
            _existing_logger=self._logger,
            _bound_kwargs=new_kwargs,
            _listener=self._listener,
        )

    @contextmanager
    def timer(self, name: str, level: str = "INFO") -> Any:
        """Context manager to easily time blocks of code."""
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = (time.perf_counter() - start) * 1000
            self._log(level.lower(), f"{name} took {elapsed:.2f}ms")

    def trace(self, level: str = "DEBUG") -> Callable:
        """Decorator to automatically log entry, exit, and execution time of a function."""

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                self._log(level.lower(), f"ENTER {func.__name__}()")
                start = time.perf_counter()
                try:
                    return func(*args, **kwargs)
                finally:
                    elapsed = (time.perf_counter() - start) * 1000
                    self._log(
                        level.lower(), f"EXIT {func.__name__}() took {elapsed:.2f}ms"
                    )

            return wrapper

        return decorator

    # Render features that use Rich if available -----------------------

    def table(self, data: Any, title: str = "", level: str = "INFO") -> None:
        """Logs a table. Uses Rich formatting if installed, otherwise stringifies."""
        if RICH_AVAILABLE:
            from rich.table import Table

            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                table_obj = Table(title=title if title else None)
                for key in data[0].keys():
                    table_obj.add_column(str(key))
                for row in data:
                    table_obj.add_row(*[str(row.get(k, "")) for k in data[0].keys()])
            else:
                table_obj = data

            console = Console(force_terminal=self.color_output)
            with console.capture() as capture:
                console.print(table_obj)
            self._log(level.lower(), "\n" + capture.get())
        else:
            self._log(level.lower(), str(data))

    def watch(self, var_name: str, var_value: Any, level: str = "DEBUG") -> None:
        """Logs a variable name, type, and value cleanly."""
        if RICH_AVAILABLE:
            from rich.pretty import Pretty

            console = Console(force_terminal=self.color_output)
            with console.capture() as capture:
                console.print(
                    f"[bold cyan]{var_name}[/bold cyan] ({type(var_value).__name__}) =",
                    Pretty(var_value),
                )
            self._log(level.lower(), "\n" + capture.get())
        else:
            self._log(
                level.lower(),
                f"WATCH: {var_name} ({type(var_value).__name__}) = {var_value!r}",
            )

    def diff(self, old: Any, new: Any, level: str = "INFO") -> None:
        """Logs a diff of two dictionaries or strings."""
        if RICH_AVAILABLE:
            from rich.text import Text
            import difflib
            import pprint

            old_str = pprint.pformat(old) if not isinstance(old, str) else old
            new_str = pprint.pformat(new) if not isinstance(new, str) else new

            differ = difflib.ndiff(old_str.splitlines(), new_str.splitlines())
            text = Text()
            for line in differ:
                if line.startswith("- "):
                    text.append(line + "\n", style="red")
                elif line.startswith("+ "):
                    text.append(line + "\n", style="green")
                elif line.startswith("? "):
                    text.append(line + "\n", style="yellow")
                else:
                    text.append(line + "\n")

            console = Console(force_terminal=self.color_output)
            with console.capture() as capture:
                console.print(text)
            self._log(level.lower(), "\n" + capture.get())
        else:
            import pprint

            self._log(
                level.lower(),
                f"DIFF:\nOld: {pprint.pformat(old)}\nNew: {pprint.pformat(new)}",
            )

    def panel(self, text: str, title: str = "", level: str = "INFO") -> None:
        """Wraps text in a stylish panel (uses Rich if available)."""
        if RICH_AVAILABLE:
            console = Console(force_terminal=self.color_output)
            with console.capture() as capture:
                console.print(Panel(text, title=title, border_style="cyan"))
            self._log(level.lower(), "\n" + capture.get())
        else:
            border = "-" * 50
            header = f"--- {title} ---" if title else border
            self._log(level.lower(), f"\n{header}\n{text}\n{border}")

    def sysinfo(self, level: str = "INFO") -> None:
        """Logs system and environment information."""
        info = get_system_info()
        self._log(level.lower(), f"System Info: {json.dumps(info, indent=2)}")

    def sql(self, query: str, level: str = "INFO") -> None:
        """Formats and logs a SQL query."""
        formatted = format_sql(query)
        if RICH_AVAILABLE and not isinstance(formatted, str):
            console = Console(force_terminal=self.color_output)
            with console.capture() as capture:
                console.print(formatted)
            self._log(level.lower(), "\n" + capture.get())
        else:
            self._log(level.lower(), f"\n{formatted}")

    def json(self, data: dict[str, Any], level: str = "INFO") -> None:
        """Formats and logs a JSON dictionary."""
        formatted = format_json(data)
        if RICH_AVAILABLE and not isinstance(formatted, str):
            console = Console(force_terminal=self.color_output)
            with console.capture() as capture:
                console.print(formatted)
            self._log(level.lower(), "\n" + capture.get())
        else:
            self._log(level.lower(), f"\n{formatted}")

    def http(self, req_resp: Any, level: str = "INFO") -> None:
        """Formats and logs an HTTP request/response or dictionary payload."""
        formatted = format_http(req_resp)
        if RICH_AVAILABLE and not isinstance(formatted, str):
            console = Console(force_terminal=self.color_output)
            with console.capture() as capture:
                console.print(formatted)
            self._log(level.lower(), "\n" + capture.get())
        else:
            self._log(level.lower(), f"\n{formatted}")

    def inspect(self, obj: Any, level: str = "INFO") -> None:
        """Inspects an object structure."""
        if RICH_AVAILABLE:
            from rich import inspect as rich_inspect
            console = Console(force_terminal=self.color_output)
            with console.capture() as capture:
                rich_inspect(obj, console=console, methods=True)
            self._log(level.lower(), "\n" + capture.get())
        else:
            self._log(level.lower(), f"INSPECT:\n{dir(obj)}\n{vars(obj) if hasattr(obj, '__dict__') else ''}")

    @contextmanager
    def catch(self, message: str = "An error occurred", reraise: bool = True) -> Generator[None, None, None]:
        """
        Context manager to catch exceptions and log them beautifully.
        If rich is available, prints a rich traceback.
        """
        try:
            yield
        except Exception as e:
            if RICH_AVAILABLE:
                from rich.traceback import Traceback
                console = Console(force_terminal=self.color_output)
                with console.capture() as capture:
                    console.print(Traceback.from_exception(type(e), e, e.__traceback__, show_locals=True))
                self._log("error", f"{message}\n{capture.get()}")
            else:
                self.exception(message)
            if reraise:
                raise

    # Convenience log-level methods -----------------------------------

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log("debug", message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log("info", message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log("warning", message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log("error", message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log("critical", message, *args, **kwargs)

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log("exception", message, *args, **kwargs)

    # Context manager support (useful for async_safe=True) ------------
    @contextmanager
    def progress(self, *args: Any, **kwargs: Any) -> Generator[Any, None, None]:
        """Provides a progress bar context manager using rich.progress."""
        if RICH_AVAILABLE:
            from rich.progress import Progress
            with Progress(*args, **kwargs) as p:
                yield p
        else:
            class DummyProgress:
                def add_task(self, *a: Any, **k: Any) -> int: return 1
                def update(self, *a: Any, **k: Any) -> None: pass
                def advance(self, *a: Any, **k: Any) -> None: pass
            yield DummyProgress()

    def tree(self, title: str, data: Union[dict[str, Any], list[Any], Any]) -> None:
        """Logs a hierarchical tree."""
        if RICH_AVAILABLE:
            from rich.tree import Tree
            def build_tree(t: Tree, obj: Any) -> None:
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        branch = t.add(f"[bold blue]{k}[/bold blue]")
                        build_tree(branch, v)
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        branch = t.add(f"[green][{i}][/green]")
                        build_tree(branch, item)
                else:
                    t.add(str(obj))
                    
            t = Tree(f"[bold red]{title}[/bold red]")
            build_tree(t, data)
            console = Console(force_terminal=self.color_output)
            with console.capture() as capture:
                console.print(t)
            self._log("info", f"\n{capture.get()}")
        else:
            self._log("info", f"{title}:\n{json.dumps(data, indent=2, default=str)}")

    def markdown(self, markup: str) -> None:
        """Renders and logs a markdown string."""
        if RICH_AVAILABLE:
            from rich.markdown import Markdown
            console = Console(force_terminal=self.color_output)
            with console.capture() as capture:
                console.print(Markdown(markup))
            self._log("info", f"\n{capture.get()}")
        else:
            self._log("info", f"\n{markup}")

    def benchmark(self, title: str, func: Callable[..., Any], iterations: int = 100, *args: Any, **kwargs: Any) -> Any:
        """Executes a function multiple times and logs the performance metrics."""
        if iterations < 1:
            iterations = 1
        times = []
        result = None
        for _ in range(iterations):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            times.append(time.perf_counter() - start)
            
        avg_time = sum(times) / iterations
        fastest = min(times)
        slowest = max(times)
        
        msg = f"Benchmark '{title}' ({iterations} runs): Avg: {avg_time:.4f}s | Fastest: {fastest:.4f}s | Slowest: {slowest:.4f}s"
        self._log("info", msg)
        return result

    def curl(self, request: dict[str, Any]) -> None:
        """Logs an equivalent cURL command for an HTTP request dictionary."""
        method = request.get("method", "GET").upper()
        url = request.get("url", "")
        headers = request.get("headers", {})
        body = request.get("body", "")
        
        curl_parts = [f"curl -X {method}"]
        for k, v in headers.items():
            curl_parts.append(f"-H '{k}: {v}'")
        if body:
            if isinstance(body, dict):
                body_str = json.dumps(body)
            else:
                body_str = str(body)
            # escape single quotes for bash
            body_str = body_str.replace("'", "'\\''")
            curl_parts.append(f"-d '{body_str}'")
        curl_parts.append(f"'{url}'")
        
        curl_cmd = " \\\n  ".join(curl_parts)
        
        if RICH_AVAILABLE:
            from rich.syntax import Syntax
            console = Console(force_terminal=self.color_output)
            with console.capture() as capture:
                console.print(Syntax(curl_cmd, "bash", theme="monokai", word_wrap=True))
            self._log("info", f"cURL Command:\n{capture.get()}")
        else:
            self._log("info", f"cURL Command:\n{curl_cmd}")

    def screenshot(self, filename: str = "screenshot.png") -> None:
        """Takes a screenshot of the desktop and logs the save path."""
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            log_dir = self._get_log_directory()
            path = log_dir / filename
            img.save(path)
            self._log("info", f"Screenshot successfully captured and saved to {path}")
        except ImportError:
            self._log("error", "Pillow is required for screenshot logging (pip install Pillow)")
        except Exception as e:
            self._log("error", f"Failed to capture screenshot: {e}")

    def patch_requests(self) -> None:
        """Monkey-patches the requests library to automatically log all outgoing HTTP calls."""
        try:
            import requests
            if hasattr(requests.Session, "_fast_logger_patched"):
                return
                
            original_request = requests.Session.request
            
            def new_request(sess: Any, method: str, url: str, **kwargs: Any) -> Any:
                start = time.perf_counter()
                self._log("info", f"Network Request START: {method} {url}")
                try:
                    resp = original_request(sess, method, url, **kwargs)
                    elapsed = time.perf_counter() - start
                    self._log("info", f"Network Request SUCCESS: {method} {url} [{resp.status_code}] ({elapsed:.3f}s)")
                    return resp
                except Exception as e:
                    elapsed = time.perf_counter() - start
                    self._log("error", f"Network Request FAILED: {method} {url} - {str(e)} ({elapsed:.3f}s)")
                    raise
                    
            requests.Session.request = new_request # type: ignore
            setattr(requests.Session, "_fast_logger_patched", True)
            self._log("info", "Requests library successfully patched for network logging.")
        except ImportError:
            self._log("error", "The 'requests' library is not installed.")

    @contextmanager
    def span(self, span_name: str) -> Generator[Any, None, None]:
        """Context manager for distributed OpenTelemetry tracing."""
        try:
            from opentelemetry import trace as otel_trace  # type: ignore
            tracer = otel_trace.get_tracer(self.name)
            with tracer.start_as_current_span(span_name) as span_obj:
                yield span_obj
        except ImportError:
            # Fallback if opentelemetry is not installed
            yield None

    @contextmanager
    def timeline(self, title: str) -> Generator[None, None, None]:
        """Context manager to measure and log execution blocks as a timeline."""
        start = time.perf_counter()
        self._log("info", f"Timeline [{title}] START")
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            self._log("info", f"Timeline [{title}] END ({elapsed:.3f}s)")

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
