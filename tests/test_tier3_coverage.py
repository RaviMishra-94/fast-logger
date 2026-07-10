import unittest
import json
import tempfile
import os
from unittest.mock import patch
from typing import Any

from fast_logger.viewer import LogViewer
from fast_logger.replay import replay_logs
from fast_logger.timeline import generate_gantt


class TestTier3Coverage(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.temp_dir.name, "test.log")

        # Write some fake logs
        with open(self.log_file, "w") as f:
            f.write(
                json.dumps(
                    {
                        "timestamp": "2026-07-11 00:00:00,000",
                        "level": "INFO",
                        "message": "Timeline [Task A] START",
                    }
                )
                + "\n"
            )
            f.write(
                json.dumps(
                    {
                        "timestamp": "2026-07-11 00:00:01,000",
                        "level": "INFO",
                        "message": "Timeline [Task A] END",
                    }
                )
                + "\n"
            )
            f.write(
                json.dumps(
                    {
                        "timestamp": "2026-07-11 00:00:00,500",
                        "level": "INFO",
                        "message": "Regular log",
                    }
                )
                + "\n"
            )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    @patch("fast_logger.viewer.LogViewer.run", create=True)
    def test_viewer(self, mock_run: Any) -> None:
        app = LogViewer(self.log_file)
        self.assertEqual(str(app.log_path), self.log_file)

    @patch("rich.console.Console.print")
    @patch("time.sleep")
    @patch("builtins.print")
    def test_replay(self, mock_print: Any, mock_sleep: Any, mock_rich_print: Any) -> None:
        # Replay the logs, mocking print and sleep to speed it up and not spam console
        replay_logs(self.log_file, speed_multiplier=100.0)
        self.assertTrue(mock_print.called or mock_rich_print.called)

    @patch("rich.console.Console.print")
    def test_timeline_gantt(self, mock_print: Any) -> None:
        generate_gantt(self.log_file)
        self.assertTrue(mock_print.called)


if __name__ == "__main__":
    unittest.main()
