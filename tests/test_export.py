"""Tests for export_html and export_markdown."""

import json
import os
import tempfile
import pytest
from fast_logger import FastLogger
from fast_logger.export import export_html, export_markdown


def make_session_file() -> tuple[str, str]:
    """Create a temp dir and a .fl session file with sample records."""
    tmpdir = tempfile.mkdtemp()
    fl_path = os.path.join(tmpdir, "test.fl")
    records = [
        {
            "timestamp": "2026-07-10T19:00:00+00:00",
            "level": "INFO",
            "logger": "app",
            "message": "Server started",
        },
        {
            "timestamp": "2026-07-10T19:00:01+00:00",
            "level": "WARNING",
            "logger": "app",
            "message": "High memory usage",
        },
        {
            "timestamp": "2026-07-10T19:00:02+00:00",
            "level": "ERROR",
            "logger": "app",
            "message": "Connection refused",
        },
        {
            "timestamp": "2026-07-10T19:00:03+00:00",
            "level": "DEBUG",
            "logger": "app",
            "message": "Cache miss for key=user:42",
        },
    ]
    with open(fl_path, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    return tmpdir, fl_path


class TestExportHTML:
    def test_creates_html_file(self) -> None:
        tmpdir, fl_path = make_session_file()
        out = os.path.join(tmpdir, "report.html")
        export_html(fl_path, out)
        assert os.path.exists(out)

    def test_html_contains_log_messages(self) -> None:
        tmpdir, fl_path = make_session_file()
        out = os.path.join(tmpdir, "report.html")
        export_html(fl_path, out)
        content = open(out).read()
        assert "Server started" in content
        assert "Connection refused" in content

    def test_html_contains_level_badges(self) -> None:
        tmpdir, fl_path = make_session_file()
        out = os.path.join(tmpdir, "report.html")
        export_html(fl_path, out)
        content = open(out).read()
        assert "ERROR" in content
        assert "WARNING" in content

    def test_html_is_valid_start(self) -> None:
        tmpdir, fl_path = make_session_file()
        out = os.path.join(tmpdir, "report.html")
        export_html(fl_path, out)
        content = open(out).read()
        assert content.startswith("<!DOCTYPE html>")

    def test_html_has_search_input(self) -> None:
        tmpdir, fl_path = make_session_file()
        out = os.path.join(tmpdir, "report.html")
        export_html(fl_path, out)
        content = open(out).read()
        assert 'id="search"' in content

    def test_logger_export_html_method(self) -> None:
        tmpdir, fl_path = make_session_file()
        logger = FastLogger("exp", base_path=tmpdir, console_output=False)
        out_path = logger.export_html(fl_path)
        assert os.path.exists(out_path)
        assert out_path.endswith(".html")
        logger.stop()


class TestExportMarkdown:
    def test_creates_md_file(self) -> None:
        tmpdir, fl_path = make_session_file()
        out = os.path.join(tmpdir, "report.md")
        export_markdown(fl_path, out)
        assert os.path.exists(out)

    def test_md_has_table_header(self) -> None:
        tmpdir, fl_path = make_session_file()
        out = os.path.join(tmpdir, "report.md")
        export_markdown(fl_path, out)
        content = open(out).read()
        assert "| Timestamp |" in content
        assert "| Level |" in content
        assert "| Message |" in content

    def test_md_contains_log_messages(self) -> None:
        tmpdir, fl_path = make_session_file()
        out = os.path.join(tmpdir, "report.md")
        export_markdown(fl_path, out)
        content = open(out).read()
        assert "Server started" in content
        assert "High memory usage" in content

    def test_logger_export_markdown_method(self) -> None:
        tmpdir, fl_path = make_session_file()
        logger = FastLogger("exp_md", base_path=tmpdir, console_output=False)
        out_path = logger.export_markdown(fl_path)
        assert os.path.exists(out_path)
        assert out_path.endswith(".md")
        logger.stop()
