# Fast Logger

![Tests](https://github.com/RaviMishra-94/fast-logger/actions/workflows/python-app.yml/badge.svg)

A professional-grade, no-fuss logging setup for Python applications with sensible defaults and developer productivity tools.

## Features

- **Zero configuration**: Works out of the box with sensible defaults
- **Rich Terminal Output**: Beautiful colors, traceback formatting, and table printing (optional)
- **Developer Productivity**: Context binding (`bind`), execution timing (`timer`), and function tracing (`@trace`)
- **JSON Formatting**: Built-in support for structured JSON logging
- **Async-Safe**: Thread-safe and async-safe logging using `QueueHandler` and `QueueListener`
- **Rotating file logs**: Automatically manages log file sizes and backups
- **Console output**: Simultaneous logging to file and console
- **Type hints**: Full type hint support for better IDE experience
- **Zero dependencies** (by default): Uses only Python standard library unless extended

## Installation

**Standard Installation (No dependencies):**
```bash
pip install python-fast-logger
```

**Developer Installation (with Beautiful Console Output):**
```bash
pip install "python-fast-logger[rich]"
```

*Note: The API remains exactly the same regardless of how you install it. If `rich` is installed, your terminal output will automatically look beautiful.*

## Quick Start

### Basic Usage

```python
from fast_logger import quick_logger

logger = quick_logger("my_app")
logger.info("Hello, world!")
logger.error("Something went wrong!")
```

## Developer Productivity (Tier 2 Features)

### Context Logger (Binding Data)

Inject contextual information into your logs persistently:

```python
from fast_logger import get_logger

logger = get_logger("my_app", json_format=True)
ctx_logger = logger.bind(request_id="req-123", user_id=42)

ctx_logger.info("Processing payment")
# JSON Output: {"message": "Processing payment", "request_id": "req-123", "user_id": 42, ...}
```

### Benchmarking (Timer)

Easily time blocks of code using the `timer` context manager:

```python
with logger.timer("Database query"):
    # ... your database logic
    pass

# Output: [INFO] Database query took 142.30ms
```

### Function Tracing (Trace)

Automatically log function entry, exit, and execution time using the `@trace` decorator:

```python
@logger.trace(level="DEBUG")
def fetch_data(url: str):
    return requests.get(url)

# Output: 
# [DEBUG] ENTER fetch_data()
# [DEBUG] EXIT fetch_data() took 312.45ms
```

### Rich Tables

Render beautiful terminal tables directly from your logger (requires `rich`):

```python
users = [
    {"id": 1, "name": "Alice", "role": "Admin"},
    {"id": 2, "name": "Bob", "role": "User"}
]

logger.table(users, title="Active Users")
```

## Advanced Configuration

```python
from fast_logger import FastLogger

logger = FastLogger(
    name="my_advanced_app",
    level="DEBUG",
    log_folder="custom_logs",
    max_file_size_mb=100,
    backup_count=5,
    console_output=True,
    json_format=True,   # Output structured JSON instead of text
    async_safe=True     # Enable QueueHandler for non-blocking logging
)
```

## Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | Required | Logger name (used as filename) |
| `level` | str/int | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `log_folder` | str | `logs` | Directory name for log files |
| `max_file_size_mb` | int | `50` | Maximum size of each log file in MB |
| `backup_count` | int | `3` | Number of backup files to keep |
| `console_output` | bool | `True` | Whether to output to console |
| `log_format` | str | Default format | Custom log format string |
| `base_path` | str | Caller's directory | Base directory for logs |
| `json_format` | bool | `False` | Log files in structured JSON format |
| `color_output` | bool | `True` | ANSI colors / rich rendering in terminal |
| `async_safe` | bool | `False` | Wrap handlers in QueueHandler (thread-safe, non-blocking) |

## Requirements

- Python 3.9+
- Optional: `rich` >= 14.0.0

## License

MIT License. See LICENSE file for details.