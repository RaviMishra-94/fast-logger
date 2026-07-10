"""Flask plugin for FastLogger — automatic request/response logging via hooks."""

from __future__ import annotations

from typing import Any


def patch_flask(app: Any, logger: Any) -> None:
    """Attach FastLogger to a Flask app via before/after request hooks."""
    try:
        import flask  # noqa: F401

        if getattr(app, "_fast_logger_plugin_patched", False):
            return

        import time

        @app.before_request
        def _fl_before() -> None:
            import flask as _flask

            _flask.g._fl_start = time.perf_counter()
            req = _flask.request
            req_id = req.headers.get("X-Request-ID", "-")
            logger.info(
                f"[{req_id}] ← {req.method} {req.path}"
                + (f"?{req.query_string.decode()}" if req.query_string else "")
            )

        @app.after_request
        def _fl_after(response: Any) -> Any:
            import flask as _flask

            elapsed = (
                time.perf_counter()
                - getattr(_flask.g, "_fl_start", time.perf_counter())
            ) * 1000
            req = _flask.request
            req_id = req.headers.get("X-Request-ID", "-")
            level = (
                "info"
                if response.status_code < 400
                else ("warning" if response.status_code < 500 else "error")
            )
            logger._log(
                level,
                f"[{req_id}] → {req.method} {req.path} {response.status_code} ({elapsed:.1f}ms)",
            )
            return response

        setattr(app, "_fast_logger_plugin_patched", True)
        logger.info(
            "Plugin 'flask' active: Registered before/after request hooks on Flask app"
        )
    except ImportError:
        logger.warning("Plugin 'flask' failed: 'flask' library not found.")
