"""
fast_logger.exceptions
~~~~~~~~~~~~~~~~~~~~~~
Heuristic exception suggestions — maps exception types and message patterns to
human-readable causes, fixes, and IDE-clickable file links.

No LLM required. Pure static pattern matching.
"""

from __future__ import annotations

import inspect
import os
import sys
import traceback
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Heuristic rule table
# Each entry: (ExceptionType, message_substring | None, causes, fixes)
# ---------------------------------------------------------------------------
_RULES: list[tuple[type, Optional[str], list[str], list[str]]] = [
    # Connection errors
    (
        ConnectionRefusedError,
        None,
        [
            "Service is not running (database, Redis, etc.)",
            "Wrong host or port in connection string",
            "Firewall or network rule blocking the connection",
        ],
        [
            "Check the service is running: `systemctl status <service>`",
            "Verify host/port in your config or .env",
            "Check firewall: `ufw status` or security group rules",
        ],
    ),
    (
        ConnectionError,
        "refused",
        [
            "Target service is down",
            "Wrong port number",
        ],
        ["Confirm service is running", "Check port number"],
    ),
    # Index / Key errors
    (
        IndexError,
        None,
        [
            "Loop or access exceeded the length of the list/array",
            "Off-by-one error in index calculation",
            "List was modified while iterating",
        ],
        [
            "Add bounds check: `if index < len(collection):`",
            "Use `enumerate()` instead of manual indexing",
            "Avoid mutating a list while iterating — use a copy",
        ],
    ),
    (
        KeyError,
        None,
        [
            "Dictionary key does not exist",
            "Typo in key name",
            "Key was deleted before access",
        ],
        [
            "Use `.get(key, default)` instead of direct `[]` access",
            "Check key existence: `if key in d:`",
            "Print `d.keys()` to see available keys",
        ],
    ),
    # File system
    (
        FileNotFoundError,
        None,
        [
            "File path is wrong or relative to a different working directory",
            "File was deleted or never created",
            "Environment difference between dev and prod",
        ],
        [
            "Use `Path(__file__).parent / 'filename'` for relative paths",
            "Add `print(os.getcwd())` to debug working directory",
            "Check file exists: `os.path.exists(path)`",
        ],
    ),
    (
        PermissionError,
        None,
        [
            "Running without sufficient OS privileges",
            "File is owned by another user",
            "Read-only filesystem or volume",
        ],
        [
            "Check file permissions: `ls -la <path>`",
            "Run with appropriate user or use `sudo` carefully",
            "Change ownership: `chown user:group <path>`",
        ],
    ),
    # Import
    (
        ImportError,
        None,
        [
            "Package not installed in the current environment",
            "Wrong virtual environment is active",
            "Circular import in your own code",
        ],
        [
            "Install the package: `pip install <package>`",
            "Verify venv: `which python` and `pip list`",
            "Check for circular imports by reviewing import order",
        ],
    ),
    (
        ModuleNotFoundError,
        None,
        ["Package not installed", "Typo in module name"],
        ["Run `pip install <package>`", "Double-check the import spelling"],
    ),
    # Attribute
    (
        AttributeError,
        "NoneType",
        [
            "A function returned None instead of the expected object",
            "Variable was never assigned before use",
        ],
        [
            "Add a None check before attribute access",
            "Trace where the variable was supposed to be set",
        ],
    ),
    (
        AttributeError,
        None,
        [
            "Wrong object type — method/attribute doesn't exist on this class",
            "Typo in attribute name",
            "API changed in a library update",
        ],
        [
            "Use `dir(obj)` to see available attributes",
            "Check the library's changelog for breaking changes",
        ],
    ),
    # Timeout
    (
        TimeoutError,
        None,
        [
            "Remote service is slow or unresponsive",
            "Network latency spike",
            "Timeout value is too short for the operation",
        ],
        [
            "Increase timeout in your HTTP/DB client config",
            "Add retry logic with exponential backoff",
            "Check remote service health",
        ],
    ),
    # Memory
    (
        MemoryError,
        None,
        [
            "Loading too much data into memory at once",
            "Memory leak — objects not released",
            "System is under heavy load",
        ],
        [
            "Use generators or chunked processing instead of loading all data",
            "Profile memory with `tracemalloc` or `memory_profiler`",
            "Increase system/container memory limit",
        ],
    ),
    # Recursion
    (
        RecursionError,
        None,
        [
            "Infinite recursive call — base case missing or unreachable",
            "Circular object graph",
        ],
        [
            "Add or fix the base case in your recursive function",
            "Increase limit temporarily: `sys.setrecursionlimit(N)` (not a fix)",
            "Consider converting to an iterative solution",
        ],
    ),
    # Zero division
    (
        ZeroDivisionError,
        None,
        [
            "Divisor is zero — missing validation",
            "Empty list passed to average calculation",
        ],
        [
            "Guard with: `if denominator != 0:`",
            "Use `len(lst) or 1` to avoid division by zero",
        ],
    ),
    # Type
    (
        TypeError,
        "takes",
        [
            "Wrong number of arguments passed to function",
            "Missing required positional argument",
        ],
        [
            "Check the function signature with `help(func)` or `inspect.signature(func)`",
        ],
    ),
    (
        TypeError,
        None,
        [
            "Operation applied to incompatible types (e.g. str + int)",
            "None passed where a value is expected",
        ],
        [
            "Add explicit type conversion: `str()`, `int()`, etc.",
            "Check upstream code that produces the value",
        ],
    ),
    # Value
    (
        ValueError,
        None,
        [
            "Input value is in the right type but invalid range/format",
            "Parsing failure (e.g. int('abc'))",
        ],
        [
            "Validate input before passing to the function",
            "Wrap in try/except to handle bad input gracefully",
        ],
    ),
]


def get_suggestions(exc: BaseException) -> Optional[dict[str, Any]]:
    """
    Return a dict with 'causes' and 'fixes' for a given exception,
    or None if no heuristic rule matches.
    """
    msg = str(exc).lower()
    for exc_type, substring, causes, fixes in _RULES:
        if isinstance(exc, exc_type):
            if substring is None or substring.lower() in msg:
                return {"causes": causes, "fixes": fixes}
    return None


def _ide_link(filename: str, lineno: int) -> str:
    """Return a VS Code / PyCharm clickable terminal hyperlink."""
    abs_path = os.path.abspath(filename)
    # OSC 8 hyperlink escape sequence (supported by VS Code terminal, iTerm2, etc.)
    return f"\033]8;;file://{abs_path}:{lineno}\033\\{os.path.basename(filename)}:{lineno}\033]8;;\033\\"


def format_rich_traceback(
    exc: BaseException,
    include_locals: bool = True,
) -> str:
    """
    Format a Rust-style rich traceback with:
    - File + line IDE hyperlinks
    - Local variables at the point of failure
    - Heuristic cause suggestions
    """
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text
        from rich.table import Table
        import io

        tb = traceback.extract_tb(exc.__traceback__)
        exc_type = type(exc).__name__
        exc_msg = str(exc)

        console = Console(file=io.StringIO(), highlight=False, width=88)

        # Header
        console.print(
            Panel(
                f"[bold red]{exc_type}[/bold red]\n[white]{exc_msg}[/white]",
                title="[bold red]Exception[/bold red]",
                border_style="red",
            )
        )

        # Traceback frames
        if tb:
            frame_table = Table(
                show_header=False, box=None, padding=(0, 1), expand=True
            )
            frame_table.add_column("info", style="dim")
            frame_table.add_column("code")

            for frame in tb:
                link = _ide_link(frame.filename, frame.lineno or 0)
                frame_table.add_row(
                    f"  {link}",
                    f"[cyan]{frame.name}()[/cyan]",
                )
                if frame.line:
                    frame_table.add_row("", f"  [white]{frame.line.strip()}[/white]")

            console.print(
                Panel(
                    frame_table,
                    title="[bold yellow]Traceback[/bold yellow]",
                    border_style="yellow",
                )
            )

        # Local variables at failure point
        if include_locals and exc.__traceback__:
            # Walk to the innermost frame
            tb_frame = exc.__traceback__
            while tb_frame.tb_next:
                tb_frame = tb_frame.tb_next
            local_vars = tb_frame.tb_frame.f_locals

            if local_vars:
                var_table = Table(show_header=True, box=None, padding=(0, 1))
                var_table.add_column("Variable", style="bold cyan")
                var_table.add_column("Value", style="white")
                var_table.add_column("Type", style="dim")
                for name, val in list(local_vars.items())[:15]:  # cap at 15
                    if name.startswith("_"):
                        continue
                    try:
                        val_repr = repr(val)
                        if len(val_repr) > 80:
                            val_repr = val_repr[:77] + "..."
                    except Exception:
                        val_repr = "<error getting repr>"
                    var_table.add_row(name, val_repr, type(val).__name__)
                console.print(
                    Panel(
                        var_table,
                        title="[bold blue]Variables[/bold blue]",
                        border_style="blue",
                    )
                )

        # Heuristic suggestions
        suggestions = get_suggestions(exc)
        if suggestions:
            causes_text = Text()
            for c in suggestions["causes"]:
                causes_text.append(f"  • {c}\n", style="yellow")
            fixes_text = Text()
            for f in suggestions["fixes"]:
                fixes_text.append(f"  ✓ {f}\n", style="green")

            from rich.columns import Columns

            console.print(
                Panel(
                    Columns(
                        [
                            Panel(
                                causes_text,
                                title="Likely Causes",
                                border_style="yellow",
                                expand=True,
                            ),
                            Panel(
                                fixes_text,
                                title="Suggested Fixes",
                                border_style="green",
                                expand=True,
                            ),
                        ]
                    ),
                    title="[bold magenta]Diagnostics[/bold magenta]",
                    border_style="magenta",
                )
            )

        return str(console.file.getvalue())  # type: ignore[attr-defined, no-any-return]

    except ImportError:
        # Fallback: plain text
        lines = [f"\n{'='*60}", f"  {type(exc).__name__}: {exc}", "=" * 60]
        for frame in traceback.extract_tb(exc.__traceback__):
            lines.append(f"  File {frame.filename}:{frame.lineno} in {frame.name}()")
            if frame.line:
                lines.append(f"    {frame.line.strip()}")
        suggestions = get_suggestions(exc)
        if suggestions:
            lines.append("\nLikely Causes:")
            for c in suggestions["causes"]:
                lines.append(f"  • {c}")
            lines.append("\nSuggested Fixes:")
            for f in suggestions["fixes"]:
                lines.append(f"  ✓ {f}")
        return "\n".join(lines)
