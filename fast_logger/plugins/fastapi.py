from typing import Any
import time


def patch(logger: Any) -> None:
    try:
        from fastapi import Request, Response, FastAPI  # type: ignore
        from starlette.middleware.base import BaseHTTPMiddleware  # type: ignore

        class FastLoggerMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: Request, call_next: Any) -> Response:
                start_time = time.perf_counter()
                logger.info(f"Incoming Request: {request.method} {request.url.path}")
                try:
                    response = await call_next(request)
                    elapsed = (time.perf_counter() - start_time) * 1000
                    logger.info(
                        f"Response: {response.status_code} {request.method} {request.url.path} (took {elapsed:.2f}ms)"
                    )
                    return response  # type: ignore
                except Exception as e:
                    elapsed = (time.perf_counter() - start_time) * 1000
                    logger.error(
                        f"Request Failed: {request.method} {request.url.path} - {e} (took {elapsed:.2f}ms)"
                    )
                    raise

        if hasattr(FastAPI, "_fast_logger_plugin_patched"):
            return

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
