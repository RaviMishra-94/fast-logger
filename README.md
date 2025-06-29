# Fast Logger

A simple, no-fuss logging setup for Python applications with sensible defaults.

## Features

- **Zero configuration**: Works out of the box with sensible defaults
- **Rotating file logs**: Automatically manages log file sizes and backups
- **Console output**: Simultaneous logging to file and console
- **Flexible configuration**: Easy to customize when needed
- **Type hints**: Full type hint support for better IDE experience
- **No dependencies**: Uses only Python standard library

## Installation

```bash
pip install fast-logger
```

## Quick Start

### Super Simple Usage

```python
from fast_logger import quick_logger

logger = quick_logger("my_app")
logger.info("Hello, world!")
logger.error("Something went wrong!")
```

### Basic Usage

```python
from fast_logger import get_logger

logger = get_logger("my_app")
logger.info("Application started")
logger.warning("This is a warning")
logger.error("This is an error")
```

### Advanced Usage

```python
from fast_logger import FastLogger

# Custom configuration
logger = FastLogger(
    name="my_advanced_app",
    level="DEBUG",
    log_folder="custom_logs",
    max_file_size_mb=100,
    backup_count=5,
    console_output=True
)

logger.info("Advanced logging setup complete")
logger.debug("Debug information")
```

### Web Application Example

```python
from fast_logger import get_logger
from flask import Flask

app = Flask(__name__)
logger = get_logger("web_app", level="INFO")

@app.route("/")
def home():
    logger.info("Home page accessed")
    return "Hello, World!"

@app.route("/api/data")
def get_data():
    try:
        # Your API logic here
        data = {"status": "success"}
        logger.info("Data retrieved successfully")
        return data
    except Exception as e:
        logger.error(f"Error retrieving data: {e}")
        return {"status": "error"}, 500
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

## Default Log Format

```
2024-01-15 10:30:45,123 - my_app [main.py:15] - INFO - Hello, world!
```

## File Structure

By default, logs are created in a `logs` folder relative to your script:

```
your_project/
├── main.py
└── logs/
    ├── my_app.log
    ├── my_app.log.1
    └── my_app.log.2
```

## API Reference

### FastLogger Class

The main class for advanced usage with full configuration options.

```python
logger = FastLogger(
    name="my_app",
    level="INFO",
    log_folder="logs",
    max_file_size_mb=50,
    backup_count=3,
    console_output=True,
    log_format=None,
    base_path=None
)
```

### Convenience Functions

- `quick_logger(name, level="INFO")`: Minimal setup for immediate use
- `get_logger(name, **kwargs)`: Returns FastLogger instance with fluent interface
- `setup_logger(name, **kwargs)`: Returns standard logging.Logger instance

## Why Fast Logger?

Most Python applications need logging, but setting it up properly requires boilerplate code:

- Creating formatters
- Setting up file handlers
- Configuring rotation
- Adding console output
- Managing log directories

Fast Logger eliminates this boilerplate while providing sensible defaults that work for most applications.

## Comparison with Standard Logging

**Standard logging setup:**
```python
import logging
import os
from logging.handlers import RotatingFileHandler

# 15+ lines of boilerplate code...
logger = logging.getLogger("my_app")
logger.setLevel(logging.INFO)
# ... more setup code
```

**Fast Logger:**
```python
from fast_logger import quick_logger

logger = quick_logger("my_app")
# Done! 
```

## Requirements

- Python 3.7+
- No external dependencies

## License

MIT License. See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.