import json
from typing import Any

try:
    from rich.json import JSON
    from rich.syntax import Syntax
    from rich.console import Console

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def format_sql(query: str) -> Any:
    """
    Format SQL queries. If rich is available, returns a Syntax object for syntax highlighting.
    Otherwise, returns the query string.
    """
    if RICH_AVAILABLE:
        # A simple normalization before highlighting
        query = " ".join(query.split())
        return Syntax(query, "sql", theme="monokai", word_wrap=True)
    return query


def format_json(data: dict[str, Any]) -> Any:
    """
    Format JSON dictionaries. If rich is available, returns a rich JSON object.
    Otherwise, returns an indented JSON string.
    """
    if RICH_AVAILABLE:
        # rich.json.JSON requires a string
        return JSON(json.dumps(data))
    return json.dumps(data, indent=2)


def format_http(req_resp: Any) -> Any:
    """
    Takes an HTTP payload, dict, or standard object (like requests.Response or httpx.Response)
    and formats it into a readable structure.
    """
    # Check if it's a httpx or requests Response
    if hasattr(req_resp, "status_code") and hasattr(req_resp, "text"):
        method = (
            getattr(req_resp.request, "method", "GET")
            if hasattr(req_resp, "request")
            else "UNKNOWN"
        )
        url = getattr(req_resp, "url", "UNKNOWN")
        status = req_resp.status_code

        headers = dict(getattr(req_resp, "headers", {}))

        header_str = "\n".join(f"{k}: {v}" for k, v in headers.items())

        formatted = f"HTTP {status} | {method} {url}\n\nHeaders:\n{header_str}\n\nBody:\n{req_resp.text}"

        if RICH_AVAILABLE:
            from rich.panel import Panel

            return Panel(formatted, title="HTTP Response", expand=False)
        return formatted

    # If it's a dict holding request data
    if isinstance(req_resp, dict):
        if RICH_AVAILABLE:
            from rich.panel import Panel

            return Panel(format_json(req_resp), title="HTTP Payload", expand=False)
        return format_json(req_resp)

    return str(req_resp)
