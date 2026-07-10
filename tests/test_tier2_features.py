import json
import logging
from pathlib import Path
from typing import Any

from fast_logger import FastLogger


class TestTier2Features:
    def test_bind_context_logger_json(self, tmp_path: Path) -> None:
        """Test that logger.bind() injects kwargs into JSON output."""
        logger = FastLogger("test_bind", base_path=str(tmp_path), json_format=True)

        # Bind context
        ctx_logger = logger.bind(request_id="abc-123", user_id=42)
        ctx_logger.info("Payment processed")

        # Read log file
        log_file = tmp_path / "logs" / "test_bind.log"
        content = log_file.read_text().strip()
        data = json.loads(content)

        assert data["message"] == "Payment processed"
        assert data["request_id"] == "abc-123"
        assert data["user_id"] == 42
        assert data["level"] == "INFO"

    def test_bind_context_logger_text(self, tmp_path: Path) -> None:
        """Test that logger.bind() appends kwargs into text output."""
        logger = FastLogger("test_bind_text", base_path=str(tmp_path))

        # Bind context
        ctx_logger = logger.bind(request_id="xyz-987")
        ctx_logger.warning("Storage low")

        # Read log file
        log_file = tmp_path / "logs" / "test_bind_text.log"
        content = log_file.read_text().strip()

        assert "Storage low [request_id=xyz-987]" in content

    def test_timer_context_manager(self, tmp_path: Path) -> None:
        """Test that logger.timer() logs execution time."""
        logger = FastLogger("test_timer", base_path=str(tmp_path))

        with logger.timer("Database Query"):
            pass  # instant

        log_file = tmp_path / "logs" / "test_timer.log"
        content = log_file.read_text().strip()

        assert "Database Query took" in content
        assert "ms" in content

    def test_trace_decorator(self, tmp_path: Path) -> None:
        """Test that @logger.trace() logs entry, exit and duration."""
        logger = FastLogger("test_trace", level="DEBUG", base_path=str(tmp_path))

        @logger.trace()
        def dummy_function(x: int) -> int:
            return x * 2

        result = dummy_function(21)
        assert result == 42

        log_file = tmp_path / "logs" / "test_trace.log"
        content = log_file.read_text().strip()

        # Expecting ENTER and EXIT
        assert "ENTER dummy_function()" in content
        assert "EXIT dummy_function() took" in content
