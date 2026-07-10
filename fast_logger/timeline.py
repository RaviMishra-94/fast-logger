"""
Timeline Gantt Chart Generator for fast-logger.
Run with: python -m fast_logger.timeline <path_to_json_log>
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

try:
    from rich.console import Console
    from rich.table import Table
    from rich.text import Text
    from rich.bar import Bar
except ImportError:
    Console = None  # type: ignore


def generate_gantt(log_path: str) -> None:
    path = Path(log_path)
    if not path.exists():
        print(f"Error: Log file {path} not found.")
        return
        
    if Console is None:
        print("Rich is required for the timeline visualization (pip install rich)")
        return

    console = Console()

    # Store events: {title: {"start": ts, "end": ts}}
    events: Dict[str, Dict[str, float]] = {}

    from datetime import datetime

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                msg = data.get("message", "")
                if msg.startswith("Timeline [") and (
                    "] START" in msg or "] END" in msg
                ):
                    ts_str = data.get("timestamp", "")
                    try:
                        dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S,%f")
                        current_ts = dt.timestamp()
                    except ValueError:
                        continue

                    # Parse title
                    start_idx = msg.find("[") + 1
                    end_idx = msg.find("]")
                    title = msg[start_idx:end_idx]

                    if title not in events:
                        events[title] = {}

                    if "] START" in msg:
                        events[title]["start"] = current_ts
                    elif "] END" in msg:
                        events[title]["end"] = current_ts

            except json.JSONDecodeError:
                continue

    valid_events = []
    min_ts = float("inf")
    max_ts = 0.0

    for title, times in events.items():
        start = times.get("start")
        end = times.get("end")
        if start is not None and end is not None:
            valid_events.append({"title": title, "start": start, "end": end})
            min_ts = min(min_ts, start)
            max_ts = max(max_ts, end)

    if not valid_events:
        console.print("[yellow]No timeline events found in log.[/yellow]")
        return

    total_duration = max_ts - min_ts
    if total_duration == 0:
        total_duration = 1.0  # prevent division by zero

    table = Table(title="Execution Timeline (Gantt)")
    table.add_column("Task", style="cyan", no_wrap=True)
    table.add_column("Duration (s)", justify="right", style="green")
    table.add_column("Timeline", width=50)

    valid_events.sort(key=lambda x: float(str(x["start"])))

    for ev in valid_events:
        ev_title = str(ev["title"])
        ev_start = float(str(ev["start"]))
        ev_end = float(str(ev["end"]))
        
        start_offset = ev_start - min_ts
        duration = ev_end - ev_start
        
        # Calculate percentage representation for the bar chart
        start_pct = start_offset / total_duration
        width_pct = duration / total_duration
        
        # Create a visual bar using spaces and blocks
        total_chars = 40
        empty_prefix = int(start_pct * total_chars)
        bar_chars = max(1, int(width_pct * total_chars))
        
        bar_text = Text()
        bar_text.append(" " * empty_prefix)
        bar_text.append("█" * bar_chars, style="blue")
        
        table.add_row(ev_title, f"{duration:.3f}", bar_text)

    console.print(table)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a Gantt chart timeline from fast-logger JSON logs."
    )
    parser.add_argument("log_file", help="Path to the .log (JSON) file")
    args = parser.parse_args()

    generate_gantt(args.log_file)


if __name__ == "__main__":
    main()
