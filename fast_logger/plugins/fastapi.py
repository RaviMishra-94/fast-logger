"""FastAPI plugin for FastLogger — full request/response/exception logging middleware."""

from __future__ import annotations

import time
import uuid
from typing import Any


def patch(logger: Any) -> None:
    """
    Monkey-patch FastAPI.__init__ so every new FastAPI app automatically gets
    FastLoggerMiddleware attached. Idempotent — safe to call multiple times.
    """
    try:
        from fastapi import FastAPI  # type: ignore

        if hasattr(FastAPI, "_fast_logger_plugin_patched"):
            return

        FastLoggerMiddleware = _make_middleware(logger)
        original_init = FastAPI.__init__

        def patched_init(self: Any, *args: Any, **kwargs: Any) -> None:
            original_init(self, *args, **kwargs)
            self.add_middleware(FastLoggerMiddleware)

        FastAPI.__init__ = patched_init  # type: ignore
        setattr(FastAPI, "_fast_logger_plugin_patched", True)
        logger.info(
            "Plugin 'fastapi' active: Monkey-patched FastAPI.__init__ to add FastLoggerMiddleware"
        )
    except ImportError:
        logger.warning("Plugin 'fastapi' failed: 'fastapi' library not found.")


def patch_app(app: Any, logger: Any) -> None:
    """
    Directly attach FastLoggerMiddleware to an *existing* FastAPI app instance.
    Use this when you already have an app and want logging without init-patching.

    Example::

        logger.patch_fastapi(app)
    """
    try:
        from fastapi import FastAPI  # type: ignore  # noqa: F401

        if getattr(app, "_fast_logger_app_patched", False):
            return

        FastLoggerMiddleware = _make_middleware(logger)
        app.add_middleware(FastLoggerMiddleware)
        setattr(app, "_fast_logger_app_patched", True)
        logger.info(
            "patch_fastapi: FastLoggerMiddleware attached to FastAPI app instance"
        )
    except ImportError:
        logger.warning("patch_fastapi failed: 'fastapi' library not found.")


def _make_middleware(logger: Any) -> Any:
    """Build the FastLoggerMiddleware class capturing the logger in closure."""
    from starlette.middleware.base import BaseHTTPMiddleware  # type: ignore
    from starlette.requests import Request  # type: ignore
    from starlette.responses import Response  # type: ignore

    class FastLoggerMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next: Any) -> Response:
            req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
            start = time.perf_counter()
            logger.info(
                f"[{req_id}] ← {request.method} {request.url.path}"
                + (f"?{request.url.query}" if request.url.query else "")
            )
            try:
                response = await call_next(request)
                elapsed = (time.perf_counter() - start) * 1000
                level = (
                    "info"
                    if response.status_code < 400
                    else ("warning" if response.status_code < 500 else "error")
                )
                logger._log(
                    level,
                    f"[{req_id}] → {request.method} {request.url.path} "
                    f"{response.status_code} ({elapsed:.1f}ms)",
                )
                response.headers["X-Request-ID"] = req_id
                return response  # type: ignore
            except Exception as exc:
                elapsed = (time.perf_counter() - start) * 1000
                logger.error(
                    f"[{req_id}] ✗ {request.method} {request.url.path} "
                    f"EXCEPTION {type(exc).__name__}: {exc} ({elapsed:.1f}ms)"
                )
                raise

    return FastLoggerMiddleware
