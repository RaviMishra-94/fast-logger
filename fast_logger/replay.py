"""
Log Replay Tool for fast-logger.
Run with: python -m fast_logger.replay <path_to_json_log> [--speed 1.0]
"""

import sys
import json
import time
import argparse
from pathlib import Path


def replay_logs(log_path: str, speed_multiplier: float = 1.0) -> None:
    """Reads a fast-logger JSON file and replays it to stdout mimicking original delays."""
    path = Path(log_path)
    if not path.exists():
        print(f"Error: Log file {path} not found.")
        return

    try:
        from rich.console import Console
        from rich.text import Text

        console = Console()
    except ImportError:
        console = None

    last_timestamp = None

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            try:
                data = json.loads(line)
                # Timestamp format: "2026-07-11 00:08:28,152"
                # For simplicity in replay, we'll parse it back to seconds
                from datetime import datetime

                ts_str = data.get("timestamp", "")

                try:
                    dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S,%f")
                    current_ts = dt.timestamp()
                except ValueError:
                    current_ts = time.time()  # fallback if parsing fails

                if last_timestamp is not None:
                    delay = current_ts - last_timestamp
                    if delay > 0:
                        time.sleep(delay / speed_multiplier)

                last_timestamp = current_ts

                # Render to screen
                lvl = data.get("level", "INFO")
                msg = data.get("message", "")

                if console:
                    color = "white"
                    if lvl == "ERROR" or lvl == "CRITICAL":
                        color = "red"
                    elif lvl == "WARNING":
                        color = "yellow"
                    elif lvl == "INFO":
                        color = "green"
                    elif lvl == "DEBUG":
                        color = "cyan"

                    text = Text(f"[{ts_str}] {lvl}: {msg}")
                    text.stylize(color, 26, 26 + len(lvl))
                    console.print(text)
                else:
                    print(f"[{ts_str}] {lvl}: {msg}")

            except json.JSONDecodeError:
                print(line, end="")


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay fast-logger JSON logs.")
    parser.add_argument("log_file", help="Path to the .log (JSON) file")
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Speed multiplier (e.g. 2.0 is 2x faster)",
    )
    args = parser.parse_args()

    print(f"Replaying logs from {args.log_file} at {args.speed}x speed...")
    replay_logs(args.log_file, args.speed)


if __name__ == "__main__":
    main()
