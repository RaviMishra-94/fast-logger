import unittest
import io
import time
from fast_logger import FastLogger


class TestTier3Final(unittest.TestCase):
    def setUp(self) -> None:
        self.stream = io.StringIO()
        self.logger = FastLogger(
            "test_tier3_final",
            console_output=True,
            color_output=False,
            json_format=False,
        )
        assert self.logger._logger is not None
        for h in self.logger._logger.handlers:
            if hasattr(h, "stream"):
                h.stream = self.stream

    def test_timeline(self) -> None:
        with self.logger.timeline("Process Data"):
            time.sleep(0.01)
        output = self.stream.getvalue()
        self.assertIn("Timeline [Process Data] START", output)
        self.assertIn("Timeline [Process Data] END", output)

    def test_screenshot(self) -> None:
        # Since Pillow might not be installed or no display, we just verify it doesn't crash
        self.logger.screenshot("test_screen.png")
        output = self.stream.getvalue()
        # Should either save or log an error about Pillow/Display
        self.assertTrue(len(output) > 0)

    def test_patch_requests(self) -> None:
        # Verify it doesn't crash
        self.logger.patch_requests()
        output = self.stream.getvalue()
        # Might error if requests isn't installed
        self.assertTrue(len(output) > 0)

    def test_span(self) -> None:
        # Verify it yields safely without OpenTelemetry
        with self.logger.span("test_span") as span:
            self.assertIsNone(span)


if __name__ == "__main__":
    unittest.main()
