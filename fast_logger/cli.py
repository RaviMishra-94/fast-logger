import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="FastLogger CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # UI command
    ui_parser = subparsers.add_parser("ui", help="Launch interactive TUI dashboard")
    ui_parser.add_argument(
        "file", type=str, nargs="?", default="bug.fl", help="Log file to view"
    )

    # Tail command
    tail_parser = subparsers.add_parser("tail", help="Tail a log file")
    tail_parser.add_argument("file", type=str, help="Log file to tail")

    # Replay command
    replay_parser = subparsers.add_parser(
        "replay", help="Replay a saved session (.fl file)"
    )
    replay_parser.add_argument("file", type=str, help="Session file to replay")

    args = parser.parse_args()

    if args.command == "ui":
        try:
            from .viewer import LogViewer

            app = LogViewer(args.file)
            app.run()
        except ImportError:
            print(
                "Error: textual is required for the UI. Install it with `pip install textual`."
            )
            sys.exit(1)
        except AttributeError:
            print("UI feature coming soon...")
    elif args.command == "tail":
        # simple python implementation of tail -f
        import time
        import os

        if not os.path.exists(args.file):
            print(f"Error: File {args.file} not found.")
            sys.exit(1)

        try:
            with open(args.file, "r") as f:
                f.seek(0, 2)
                print(f"Tailing {args.file}...")
                while True:
                    line = f.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                    print(line, end="")
        except KeyboardInterrupt:
            sys.exit(0)
    elif args.command == "replay":
        try:
            from .replay import replay_logs

            replay_logs(args.file)
        except ImportError:
            print("Replay feature not fully implemented or missing dependencies.")
        except AttributeError:
            print("Replay feature coming soon...")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
