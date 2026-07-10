import uuid
from typing import Any, Callable

try:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import Response
    from contextvars import ContextVar

    # Context variable to store the request ID for the current async task
    request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="")

    class FastAPILoggerMiddleware(BaseHTTPMiddleware):
        """
        FastAPI / Starlette middleware that injects a correlation ID
        into a ContextVar for each incoming request.
        """

        async def dispatch(self, request: Request, call_next: Callable) -> Response:
            # Check if correlation ID was passed in headers
            req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

            # Set context variable for this request
            token = request_id_ctx_var.set(req_id)

            try:
                response = await call_next(request)
                if not isinstance(response, Response):
                    from typing import cast
                    response = cast(Response, response)
                
                # Inject correlation ID back into response headers
                response.headers["X-Request-ID"] = req_id
                return response
            finally:
                request_id_ctx_var.reset(token)

except ImportError:
    # If Starlette / FastAPI is not installed, provide a dummy class
    class FastAPILoggerMiddleware:  # type: ignore
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ImportError(
                "FastAPI/Starlette is required to use FastAPILoggerMiddleware. "
                "Install it with `pip install fastapi`."
            )
