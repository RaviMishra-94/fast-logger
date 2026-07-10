"""FastLogger CLI — developer-experience command suite."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def _print_rich(msg: str) -> None:
    """Print with Rich if available, else plain print."""
    try:
        from rich.console import Console

        Console().print(msg)
    except ImportError:
        # Strip basic markup for plain fallback
        import re

        print(re.sub(r"\[.*?\]", "", msg))


def cmd_doctor(_args: argparse.Namespace) -> None:
    """Check environment health for fast-logger."""
    _print_rich("\n[bold cyan]FastLogger Doctor[/bold cyan]\n")

    checks = []

    # Python version
    major, minor = sys.version_info[:2]
    ok = major == 3 and minor >= 9
    checks.append((ok, f"Python {major}.{minor}", "Requires Python 3.9+"))

    # Rich
    try:
        import rich  # noqa: F401

        checks.append((True, "rich installed", "Syntax highlighting & panels enabled"))
    except ImportError:
        checks.append((False, "rich not installed", "pip install rich"))

    # Textual
    try:
        import textual  # noqa: F401

        checks.append((True, "textual installed", "TUI viewer enabled"))
    except ImportError:
        checks.append(
            (False, "textual not installed", "pip install textual  (optional)")
        )

    # Log directory writable
    log_dir = Path("logs")
    try:
        log_dir.mkdir(exist_ok=True)
        test_file = log_dir / ".fl_doctor_test"
        test_file.touch()
        test_file.unlink()
        checks.append((True, f"{log_dir}/ writable", "Log files will be created here"))
    except Exception as e:
        checks.append((False, f"{log_dir}/ not writable", str(e)))

    # Config file
    config_found = any(
        Path(p).exists()
        for p in ["fast_logger.json", "pyproject.toml", ".fast_logger.json"]
    )
    checks.append(
        (
            config_found,
            "Config file found" if config_found else "No config file",
            "Run `fastlogger init` to create one",
        )
    )

    # Terminal color support
    color_ok = sys.stdout.isatty()
    checks.append(
        (
            color_ok,
            "Terminal supports color" if color_ok else "No color (not a TTY)",
            "Use color_output=True only in TTY",
        )
    )

    for ok, label, hint in checks:
        icon = "[bold green]✓[/bold green]" if ok else "[bold red]✗[/bold red]"
        status = f"[green]{label}[/green]" if ok else f"[red]{label}[/red]"
        _print_rich(f"  {icon}  {status}")
        if not ok:
            _print_rich(f"       [dim]→ {hint}[/dim]")

    passed = sum(1 for ok, _, _ in checks if ok)
    _print_rich(f"\n[dim]{passed}/{len(checks)} checks passed[/dim]\n")


def cmd_init(_args: argparse.Namespace) -> None:
    """Scaffold a fast_logger.json config in the current directory."""
    config_path = Path("fast_logger.json")
    if config_path.exists():
        _print_rich(
            f"[yellow]⚠ {config_path} already exists — not overwriting.[/yellow]"
        )
        sys.exit(0)

    config = {
        "level": "INFO",
        "theme": "default",
        "log_folder": "logs",
        "max_file_size_mb": 50,
        "backup_count": 3,
        "color_output": True,
        "json_format": False,
        "async_safe": False,
        "mask_secrets": False,
        "compress_backups": False,
        "pretty_exceptions": True,
    }
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    _print_rich(f"[green]✓ Created {config_path}[/green]")
    _print_rich(
        "[dim]Edit to customise your logger. Load with FastLogger.from_config()[/dim]\n"
    )


def cmd_stats(args: argparse.Namespace) -> None:
    """Show log level counts and top messages from a .fl or .log file."""
    filepath = args.file
    if not os.path.exists(filepath):
        _print_rich(f"[red]Error: File '{filepath}' not found.[/red]")
        sys.exit(1)

    counts: dict[str, int] = {}
    messages: list[str] = []

    with open(filepath, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                lvl = record.get("level", "INFO").upper()
                msg = record.get("message", "")
            except json.JSONDecodeError:
                lvl = "INFO"
                msg = line
            counts[lvl] = counts.get(lvl, 0) + 1
            messages.append(msg)

    _print_rich(f"\n[bold cyan]Stats: {filepath}[/bold cyan]\n")

    level_colors = {
        "DEBUG": "dim",
        "INFO": "blue",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold red",
    }
    for lvl in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        if lvl in counts:
            c = level_colors.get(lvl, "white")
            _print_rich(f"  [{c}]{lvl:<10}[/{c}] {counts[lvl]}")

    total = sum(counts.values())
    _print_rich(f"\n  [dim]Total: {total} entries[/dim]")

    # Top 5 most common messages
    from collections import Counter

    top = Counter(messages).most_common(5)
    if top:
        _print_rich("\n[bold]Top Messages:[/bold]")
        for msg, cnt in top:
            short = msg[:72] + "..." if len(msg) > 72 else msg
            _print_rich(f"  [dim]{cnt:>4}×[/dim]  {short}")
    _print_rich("")


def cmd_tail(args: argparse.Namespace) -> None:
    """Tail a log file in real-time (like tail -f but prettier)."""
    import time

    if not os.path.exists(args.file):
        _print_rich(f"[red]Error: File '{args.file}' not found.[/red]")
        sys.exit(1)

    _print_rich(f"[dim]Tailing {args.file} — Ctrl+C to stop[/dim]\n")

    level_colors = {
        "DEBUG": "\033[90m",
        "INFO": "\033[34m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    reset = "\033[0m"

    try:
        with open(args.file, "r", encoding="utf-8") as f:
            f.seek(0, 2)  # seek to end
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                line = line.rstrip()
                try:
                    record = json.loads(line)
                    lvl = record.get("level", "INFO").upper()
                    ts = record.get("timestamp", "")[:19]
                    msg = record.get("message", "")
                    color = level_colors.get(lvl, "")
                    print(f"{color}[{ts}] {lvl:<8}{reset} {msg}")
                except json.JSONDecodeError:
                    print(line)
    except KeyboardInterrupt:
        sys.exit(0)


def cmd_replay(args: argparse.Namespace) -> None:
    """Replay a saved .fl session file with original timing."""
    try:
        from .replay import replay_logs

        replay_logs(args.file)
    except ImportError as e:
        _print_rich(f"[red]Replay feature requires additional dependencies: {e}[/red]")
    except FileNotFoundError:
        _print_rich(f"[red]Error: '{args.file}' not found.[/red]")
        sys.exit(1)


def cmd_ui(args: argparse.Namespace) -> None:
    """Launch the interactive TUI log viewer."""
    try:
        from .viewer import LogViewer

        app = LogViewer(args.file)
        app.run()
    except ImportError:
        _print_rich(
            "[red]Error:[/red] [yellow]textual[/yellow] is required for the UI. "
            "Install it with: [bold]pip install textual[/bold]"
        )
        sys.exit(1)


def cmd_timeline(args: argparse.Namespace) -> None:
    """Render a Gantt timeline chart from a .fl session file."""
    try:
        from .timeline import generate_gantt

        generate_gantt(args.file)
    except ImportError as e:
        _print_rich(f"[red]Timeline requires additional dependencies: {e}[/red]")
    except FileNotFoundError:
        _print_rich(f"[red]Error: '{args.file}' not found.[/red]")
        sys.exit(1)


def cmd_benchmark(_args: argparse.Namespace) -> None:
    """Run a microbenchmark comparing fast-logger vs logging vs loguru."""
    import timeit

    _print_rich("\n[bold cyan]FastLogger Benchmark[/bold cyan]\n")

    results = []

    # fast-logger
    setup_fl = """
import tempfile, os, sys
from fast_logger import FastLogger
_tmpdir = tempfile.mkdtemp()
_logger = FastLogger('bench', base_path=_tmpdir, console_output=False, level='DEBUG')
"""
    t_fl = timeit.timeit(
        "_logger.debug('benchmark message')", setup=setup_fl, number=10_000
    )
    results.append(("fast-logger", t_fl))

    # stdlib logging
    setup_log = """
import logging, tempfile, os
_tmpdir = tempfile.mkdtemp()
_log = logging.getLogger('bench_stdlib')
_log.setLevel(logging.DEBUG)
_h = logging.FileHandler(os.path.join(_tmpdir, 'bench.log'))
_h.setLevel(logging.DEBUG)
_log.addHandler(_h)
"""
    t_log = timeit.timeit(
        "_log.debug('benchmark message')", setup=setup_log, number=10_000
    )
    results.append(("logging (stdlib)", t_log))

    # loguru (optional)
    try:
        setup_lu = """
import tempfile, os
from loguru import logger as _lu
_tmpdir = tempfile.mkdtemp()
_lu.remove()
_lu.add(os.path.join(_tmpdir, 'bench.log'), level='DEBUG', enqueue=False)
"""
        t_lu = timeit.timeit(
            "_lu.debug('benchmark message')", setup=setup_lu, number=10_000
        )
        results.append(("loguru", t_lu))
    except ImportError:
        pass

    _print_rich("  10,000 debug() calls:\n")
    for name, elapsed in sorted(results, key=lambda x: x[1]):
        per_call_us = (elapsed / 10_000) * 1_000_000
        bar = "█" * max(1, int(per_call_us * 3))
        _print_rich(
            f"  [cyan]{name:<20}[/cyan]  [green]{per_call_us:>6.2f}µs[/green]  [dim]{bar}[/dim]"
        )
    _print_rich("")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="fastlogger",
        description="FastLogger CLI — developer experience toolkit",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")

    # doctor
    subparsers.add_parser("doctor", help="Check environment health and dependencies")

    # init
    subparsers.add_parser(
        "init", help="Scaffold fast_logger.json config in current directory"
    )

    # stats
    stats_p = subparsers.add_parser(
        "stats", help="Show log level counts from a .fl or .log file"
    )
    stats_p.add_argument("file", help="Log or session file to analyse")

    # tail
    tail_p = subparsers.add_parser("tail", help="Tail a log file in real-time")
    tail_p.add_argument("file", help="Log file to tail")

    # replay
    replay_p = subparsers.add_parser("replay", help="Replay a saved .fl session file")
    replay_p.add_argument("file", help="Session file (.fl) to replay")

    # ui
    ui_p = subparsers.add_parser("ui", help="Launch the interactive TUI log viewer")
    ui_p.add_argument(
        "file",
        nargs="?",
        default="bug.fl",
        help="Session file to view (default: bug.fl)",
    )

    # timeline
    timeline_p = subparsers.add_parser(
        "timeline", help="Render a Gantt chart from a .fl file"
    )
    timeline_p.add_argument("file", help="Session file (.fl) to render")

    # benchmark
    subparsers.add_parser(
        "benchmark", help="Microbenchmark fast-logger vs logging vs loguru"
    )

    args = parser.parse_args()

    dispatch = {
        "doctor": cmd_doctor,
        "init": cmd_init,
        "stats": cmd_stats,
        "tail": cmd_tail,
        "replay": cmd_replay,
        "ui": cmd_ui,
        "timeline": cmd_timeline,
        "benchmark": cmd_benchmark,
    }

    if args.command in dispatch:
        dispatch[args.command](args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
