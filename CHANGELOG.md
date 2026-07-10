# Changelog

All notable changes to this project will be documented in this file.

## [0.6.0] - 2026-07-10

### Added
- Log Viewer TUI (`python -m fast_logger.viewer`)
- Log Replay Tool (`python -m fast_logger.replay`)
- OpenTelemetry tracing support (`logger.span()`)
- Network request patching (`logger.patch_requests()`)
- Desktop screenshot logging (`logger.screenshot()`)
- Timeline / Gantt chart helper (`logger.timeline()`)
- Session recording and saving (`logger.record()`, `logger.save()`)
- Plugin architecture with auto-patching for FastAPI, SQLAlchemy, Requests
- Modular theme system (default, cyberpunk, dracula, minimal)
- Configuration file support (`fast_logger.json`, `pyproject.toml`)
- CLI tool (`fastlogger ui|tail|replay`)

### Fixed
- Timestamp parsing in `replay.py` and `timeline.py` (now uses ISO 8601)
- `save()` now clears the memory buffer to prevent duplicate entries
- `from_config()` gracefully ignores unknown config keys
- Plugin guards prevent double-patching for requests, FastAPI, and SQLAlchemy
- `record()` no longer pollutes session files with internal messages
- Replay stylize positions calculated dynamically instead of hardcoded
- Removed unused `Bar` import in `timeline.py`

## [0.5.0] - 2026-07-09

### Added
- Progress bars via `logger.progress()` (Rich-powered with fallback)
- Markdown rendering via `logger.markdown()`
- Tree view logging via `logger.tree()`
- Performance benchmarking via `logger.benchmark()`
- cURL command generator via `logger.curl()`
- Log rotation compression (`compress_backups=True`)
- Global rich exception handling (`pretty_exceptions=True`)

## [0.4.0] - 2026-07-08

### Added
- SQL query formatter (`logger.sql()`)
- JSON data formatter (`logger.json()`)
- HTTP request/response formatter (`logger.http()`)
- Object inspector (`logger.inspect()`)
- Exception catch context manager (`logger.catch()`)
- Diff viewer (`logger.diff()`)

## [0.3.0] - 2026-07-07

### Added
- Secret masking (`mask_secrets=True`)
- Variable watcher (`logger.watch()`)
- System telemetry (`logger.sysinfo()`)
- Panel formatting (`logger.panel()`)
- FastAPI correlation ID middleware (`FastAPILoggerMiddleware`)

## [0.2.0] - 2026-07-06

### Added
- Colored console output (`color_output=True`)
- Structured JSON log format (`json_format=True`)
- Async-safe logging (`async_safe=True`)
- Context binding (`logger.bind()`)
- Execution timing (`logger.timer()`)
- Function tracing decorator (`@logger.trace()`)
- Table formatting (`logger.table()`)
- Optional Rich support (`pip install "python-fast-logger[rich]"`)

## [0.1.0] - 2026-07-05

### Added
- Initial release
- `FastLogger` class with `RotatingFileHandler`
- Console output with configurable log levels
- `setup_logger()`, `get_logger()`, `quick_logger()` convenience functions
