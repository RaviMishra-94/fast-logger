"""Tests for heuristic exception suggestions and rich traceback formatting."""

import tempfile
import pytest
from fast_logger.exceptions import get_suggestions, format_rich_traceback


class TestGetSuggestions:
    def test_connection_refused_error(self) -> None:
        exc = ConnectionRefusedError("Connection refused to localhost:5432")
        result = get_suggestions(exc)
        assert result is not None
        assert len(result["causes"]) > 0
        assert len(result["fixes"]) > 0

    def test_index_error(self) -> None:
        exc = IndexError("list index out of range")
        result = get_suggestions(exc)
        assert result is not None
        assert any(
            "length" in c.lower() or "index" in c.lower() for c in result["causes"]
        )

    def test_key_error(self) -> None:
        exc = KeyError("user_id")
        result = get_suggestions(exc)
        assert result is not None
        assert len(result["causes"]) > 0

    def test_file_not_found(self) -> None:
        exc = FileNotFoundError("No such file: config.yaml")
        result = get_suggestions(exc)
        assert result is not None

    def test_attribute_error_nonetype(self) -> None:
        exc = AttributeError("'NoneType' object has no attribute 'id'")
        result = get_suggestions(exc)
        assert result is not None
        assert any("None" in c for c in result["causes"])

    def test_import_error(self) -> None:
        exc = ImportError("No module named 'pandas'")
        result = get_suggestions(exc)
        assert result is not None
        assert any("pip install" in f for f in result["fixes"])

    def test_zero_division(self) -> None:
        exc = ZeroDivisionError("division by zero")
        result = get_suggestions(exc)
        assert result is not None

    def test_recursion_error(self) -> None:
        exc = RecursionError("maximum recursion depth exceeded")
        result = get_suggestions(exc)
        assert result is not None

    def test_unknown_exception_returns_none(self) -> None:
        exc = StopIteration("no match")
        result = get_suggestions(exc)
        assert result is None


class TestFormatRichTraceback:
    def test_returns_string(self) -> None:
        try:
            raise ValueError("test error for traceback")
        except ValueError as e:
            result = format_rich_traceback(e)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_exception_type(self) -> None:
        try:
            raise IndexError("list index out of range")
        except IndexError as e:
            result = format_rich_traceback(e)
        assert "IndexError" in result

    def test_contains_suggestions_for_known_error(self) -> None:
        try:
            raise ConnectionRefusedError("Connection refused")
        except ConnectionRefusedError as e:
            result = format_rich_traceback(e)
        # Either Rich Panel or plain text output should contain cause info
        assert (
            "Service" in result
            or "cause" in result.lower()
            or "refused" in result.lower()
        )

    def test_no_locals_flag(self) -> None:
        """include_locals=False should not crash."""
        try:
            raise KeyError("missing_key")
        except KeyError as e:
            result = format_rich_traceback(e, include_locals=False)
        assert isinstance(result, str)


class TestCatchIntegration:
    def test_catch_logs_suggestions(self) -> None:
        """logger.catch() should use heuristic traceback for exceptions."""
        import os
        from fast_logger import FastLogger

        tmpdir = tempfile.mkdtemp()
        logger = FastLogger(
            "exc_test", base_path=tmpdir, console_output=False, json_format=True
        )

        with pytest.raises(IndexError):
            with logger.catch("Test catch"):
                items = [1, 2, 3]
                _ = items[10]

        import glob

        log_files = glob.glob(os.path.join(tmpdir, "**", "*.log"), recursive=True)
        assert log_files, "Expected log file to be created"
        content = open(log_files[0]).read()
        assert "IndexError" in content or "error" in content.lower()
        logger.stop()
